"""
Guitar Practice App (guitprac)
A Flask app for guitar practice with chord display, audio playback, and auto-scroll
Now with library management and automatic song fetching from YouTube!
Multi-source chord fetching: Songsterr → Ultimate Guitar → Ollama AI → Manual
"""
import os
import re
import json
import time
import subprocess
import threading
import hashlib
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from utils.chordpro_parser import parse_chordpro
from utils import database as db
from utils.youtube_downloader import search_youtube, download_audio, check_ytdlp_installed
from utils.chords_fetcher import search_ultimate_guitar, fetch_chords_from_url, convert_to_chordpro, search_chords_simple
from utils.artist_lookup import get_song_metadata, parse_search_query


app = Flask(__name__)
app.config['SECRET_KEY'] = 'guitar-practice-app-secret-key'

from urllib.parse import quote as _url_quote
app.jinja_env.filters['urlencode'] = lambda s: _url_quote(str(s or ''), safe='')

# Git version: short commit hash (7 chars)
def _get_git_version():
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return 'dev'

GIT_VERSION = _get_git_version()

# ─────────────────────────────────────────────
# CHARTS CACHE  (TTL 1 hour each)
# ─────────────────────────────────────────────
_global_chart_cache  = {'data': None, 'ts': 0}
_guitar_chart_cache  = {'data': None, 'ts': 0}

import urllib.request as _urllib_req


def _http_get(url, timeout=6, extra_headers=None):
    """Simple GET helper with JSON decode."""
    headers = {'User-Agent': 'ChordPilot/1.0 (guitar practice app)'}
    if extra_headers:
        headers.update(extra_headers)
    req = _urllib_req.Request(url, headers=headers)
    with _urllib_req.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def fetch_global_chart(limit: int = 10):
    """
    Top tracks from Deezer Chart API — free, no auth, real streaming data.
    Endpoint: https://api.deezer.com/chart/0/tracks
    Returns rank, title, artist, genre, Deezer rank-score (popularity metric), link.
    Cached 1 hour.
    """
    global _global_chart_cache
    now = time.time()
    if _global_chart_cache['data'] and (now - _global_chart_cache['ts']) < 3600:
        return _global_chart_cache['data'][:limit]
    try:
        payload = _http_get(f'https://api.deezer.com/chart/0/tracks?limit={limit}')
        items = payload.get('data', [])
        result = []
        for i, item in enumerate(items):
            # Deezer 'rank' is a popularity score (higher = more popular)
            score = item.get('rank', 0)
            score_fmt = f"{score:,}" if score >= 1000 else str(score)
            result.append({
                'rank':    i + 1,
                'title':   item.get('title_short') or item.get('title', ''),
                'artist':  item.get('artist', {}).get('name', ''),
                'image':   item.get('album', {}).get('cover_medium', ''),
                'link':    item.get('link', ''),
                'score':   score_fmt,
                'source':  'Deezer Charts',
            })
        if result:
            _global_chart_cache = {'data': result, 'ts': now}
            print(f"[CHART] Loaded {len(result)} global tracks from Deezer")
            return result[:limit]
    except Exception as e:
        print(f"[CHART] Deezer fetch failed: {e}")
    return []   # empty → template shows "unavailable" state


def fetch_guitar_chart(limit: int = 6):
    """
    Scrape Ultimate Guitar daily top tabs from the public /top/tabs page.
    UG embeds all page data as JSON inside <div class="js-store" data-content="...">.
    No API key needed. Returns top tabs sorted by daily hits.
    Cached 1 hour.
    """
    global _guitar_chart_cache
    now = time.time()
    if _guitar_chart_cache['data'] and (now - _guitar_chart_cache['ts']) < 3600:
        return _guitar_chart_cache['data'][:limit]
    try:
        import html as _html
        import re as _re
        url = 'https://www.ultimate-guitar.com/top/tabs?period=daily'
        req = _urllib_req.Request(url, headers={
            'User-Agent': (
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ),
            'Accept':          'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',
        })
        with _urllib_req.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')

        # UG injects all data into: <div class="js-store" data-content="...JSON...">
        m = _re.search(r'class="js-store"[^>]*data-content="([^"]*)"', page_html)
        if not m:
            raise ValueError("js-store element not found in page")

        data      = json.loads(_html.unescape(m.group(1)))
        page_data = data.get('store', {}).get('page', {}).get('data', {})
        tabs      = page_data.get('tabs', [])

        # Hits are stored separately: [{id, hits}, ...] — join by tab id
        hits_lookup = {h['id']: h['hits'] for h in page_data.get('hits', [])}

        result = []
        for i, tab in enumerate(tabs[:limit]):
            hits = hits_lookup.get(tab.get('id', 0), 0)
            image = (
                tab.get('album_cover', {})
                   .get('web_album_cover', {})
                   .get('small', '')
            )
            result.append({
                'rank':     i + 1,
                'title':    tab.get('song_name', ''),
                'artist':   tab.get('artist_name', ''),
                'hits':     f"{hits:,}" if hits >= 1000 else str(hits),
                'tab_type': tab.get('type_name') or tab.get('type', 'Chords'),
                'tab_url':  tab.get('tab_url', ''),
                'image':    image,
                'source':   'Ultimate Guitar',
            })

        if result:
            _guitar_chart_cache = {'data': result, 'ts': now}
            print(f"[CHART] Loaded {len(result)} guitar tabs from UG /top/tabs daily")
            return result[:limit]
    except Exception as e:
        print(f"[CHART] UG scrape failed: {e}")
    return []


# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """Return current user dict from session, or None."""
    user_id = session.get('user_id')
    if user_id:
        return db.get_user_by_id(user_id)
    return None

# Path to songs directory
SONGS_DIR = os.path.join(app.static_folder, 'songs')

# Path to settings file
SETTINGS_FILE = 'settings.json'

# Initialize database on startup
db.init_db()
db.migrate_from_json()


# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def load_settings():
    """Load app settings from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[SETTINGS] Error loading settings: {e}")

    # Default settings
    return {
        'ollama_url': 'http://localhost:11434',
        'ollama_model': 'mistral:7b',
        'ollama_enabled': False
    }


def save_settings(settings):
    """Save app settings to JSON file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"[SETTINGS] Settings saved successfully")
        return True
    except Exception as e:
        print(f"[SETTINGS] Error saving settings: {e}")
        return False


def get_all_songs():
    """Get all songs from database"""
    return db.get_all_songs()


def get_song_by_id(song_id):
    """Get a single song by its ID"""
    return db.get_song_by_id(song_id)


@app.route('/')
@login_required
def home_page():
    """Home / practice dashboard — song cards + quick stats"""
    songs = get_all_songs()
    total_plays = sum((s.get('play_count') or 0) for s in songs)
    practiced_count = sum(1 for s in songs if (s.get('play_count') or 0) > 0)
    # Top 8 songs by play_count
    top_songs = sorted(songs, key=lambda s: (s.get('play_count') or 0), reverse=True)[:8]
    tutorials = db.get_tutorials(limit=6)
    global_chart = fetch_global_chart(limit=6)
    guitar_chart = fetch_guitar_chart(limit=6)
    from datetime import datetime
    fetched_at = datetime.now().strftime('%H:%M')
    return render_template('home.html', songs=songs, top_songs=top_songs,
                           tutorials=tutorials,
                           global_chart=global_chart, guitar_chart=guitar_chart,
                           fetched_at=fetched_at,
                           total_plays=total_plays, practiced_count=practiced_count)


@app.route('/library')
@login_required
def library_page():
    """Library — full song database with table view"""
    songs = get_all_songs()
    enriched = []
    for s in songs:
        s = dict(s)
        folder = s.get('folder', '')
        s['has_audio'] = os.path.exists(os.path.join(SONGS_DIR, folder, 'audio.mp3'))
        s['has_chords'] = os.path.exists(os.path.join(SONGS_DIR, folder, 'chords.cho'))
        enriched.append(s)
    return render_template('library.html', songs=enriched,
                           total_rows=len(enriched), ytdlp_installed=check_ytdlp_installed())


@app.route('/library/search')
def library_search():
    """Search for songs to add"""
    query = request.args.get('q', '')

    if not query:
        return render_template('search_results.html', query='', youtube_results=[], chord_results=[])

    # Search YouTube
    youtube_results = search_youtube(query, max_results=5)

    # Search for chords
    chord_results = search_chords_simple(query)

    return render_template('search_results.html',
                          query=query,
                          youtube_results=youtube_results,
                          chord_results=chord_results)


@app.route('/library/add', methods=['POST'])
def library_add_song():
    """
    Add a new song to library
    Expects JSON with: title, artist, youtube_url, chords_url (or manual chords)
    """
    data = request.get_json()

    title = data.get('title', '').strip()
    artist = data.get('artist', '').strip()
    youtube_url = data.get('youtube_url', '').strip()
    chords_url = data.get('chords_url', '').strip()
    chords_content = data.get('chords_content', '').strip()  # Pre-fetched from Songsterr/AI
    manual_chords = data.get('manual_chords', '').strip()
    key = data.get('key', '').strip()
    search_query = data.get('search_query', '').strip()

    print(f"[APP] ═══════════════════════════════════════════════════════")
    print(f"[APP] Add song request:")
    print(f"[APP]   Title: '{title}'")
    print(f"[APP]   Artist: '{artist}'")
    print(f"[APP]   Chords URL: '{chords_url}'")
    print(f"[APP]   YouTube URL: '{youtube_url}'")
    print(f"[APP] ═══════════════════════════════════════════════════════")

    # If artist is Unknown or empty, try to get it from MusicBrainz
    if not artist or artist.lower() == 'unknown':
        print(f"[APP] Artist unknown, trying MusicBrainz lookup for '{title}'")
        metadata = get_song_metadata(search_query or title)
        if metadata['artist'] and metadata['artist'] != 'Unknown':
            artist = metadata['artist']
            # Also update title if MusicBrainz has a better version
            if len(metadata['title']) > len(title):
                title = metadata['title']
        print(f"[APP] After MusicBrainz: title='{title}', artist='{artist}'")

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    # Generate song_id and folder name
    song_id = title.lower().replace(' ', '-').replace("'", '').replace('"', '')
    song_id = ''.join(c for c in song_id if c.isalnum() or c == '-')
    folder = song_id

    # Create folder
    song_path = os.path.join(SONGS_DIR, folder)
    os.makedirs(song_path, exist_ok=True)

    # Add song to database
    song_data = {
        'song_id': song_id,
        'title': title,
        'artist': artist,
        'key': key,
        'folder': folder,
        'youtube_url': youtube_url,
        'chords_source': chords_url
    }

    try:
        db.add_song(song_data)
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    # Start background download process
    def download_process():
        download_id = db.create_download_record(song_id)

        try:
            # Download audio from YouTube
            if youtube_url:
                db.update_download_status(download_id, 'downloading_audio', 10)
                audio_path = os.path.join(song_path, 'audio.mp3')

                def progress_callback(percent, message):
                    db.update_download_status(download_id, 'downloading_audio', int(percent))

                success = download_audio(youtube_url, audio_path, progress_callback)

                if not success:
                    db.update_download_status(download_id, 'error', error='Failed to download audio')
                    return

            # Fetch and save chords
            print(f"[APP] ───────────────────────────────────────────────────────")
            print(f"[APP] Chord Fetching Phase")
            print(f"[APP] ───────────────────────────────────────────────────────")
            db.update_download_status(download_id, 'fetching_chords', 60)
            chordpro_path = os.path.join(song_path, 'chords.cho')

            chords_fetched = False

            # Check if chords were pre-fetched (Songsterr or AI)
            if chords_url in ['songsterr', 'ai-generated'] and chords_content:
                print(f"[APP] Using pre-fetched chords from {chords_url}")
                with open(chordpro_path, 'w') as f:
                    f.write(chords_content)
                chords_fetched = True
                print(f"[APP] ✓ Chords saved from {chords_url} ({len(chords_content)} chars)")

            elif manual_chords:
                # User provided manual chords
                print(f"[APP] ✓ Using manual chords ({len(manual_chords)} chars)")
                with open(chordpro_path, 'w') as f:
                    f.write(manual_chords)
                chords_fetched = True

            elif chords_url and chords_url not in ['#', 'manual', '', 'songsterr', 'ai-generated']:
                # Fetch from Ultimate Guitar URL
                print(f"[APP] Attempting to fetch chords from URL: {chords_url}")
                raw_chords = fetch_chords_from_url(chords_url)
                if raw_chords:
                    print(f"[APP] ✓ Got raw chords ({len(raw_chords)} chars), converting to ChordPro")
                    chordpro_content = convert_to_chordpro(raw_chords, title, artist)
                    with open(chordpro_path, 'w') as f:
                        f.write(chordpro_content)
                    chords_fetched = True
                    print(f"[APP] ✓ Chords saved successfully")
                else:
                    print(f"[APP] ✗ Failed to fetch chords from URL")
            else:
                print(f"[APP] Skipping chord fetch (chords_url='{chords_url}')")

            if not chords_fetched:
                # Create manual entry template with instructions
                print(f"[APP] Creating manual entry template for user to fill in")
                create_manual_entry_template(chordpro_path, title, artist, key)
                print(f"[APP] ⚠ Manual entry required - user must add chords")

            # Mark as complete
            db.update_download_status(download_id, 'completed', 100)
            print(f"[APP] ═══════════════════════════════════════════════════════")
            print(f"[APP] ✓ Song '{title}' added successfully!")
            print(f"[APP]   Chords: {'✓ Fetched' if chords_fetched else '⚠ Manual entry required'}")
            print(f"[APP]   Audio: {'✓ Downloaded' if youtube_url else '✗ No audio'}")
            print(f"[APP] ═══════════════════════════════════════════════════════")

        except Exception as e:
            print(f"[APP] ✗ Error in download process: {e}")
            import traceback
            traceback.print_exc()
            db.update_download_status(download_id, 'error', error=str(e))

    # Start background thread
    thread = threading.Thread(target=download_process)
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'song_id': song_id,
        'message': 'Song added! Download in progress...'
    })


def create_basic_chordpro(filepath, title, artist, key=''):
    """Create a basic ChordPro template"""
    content = f"""{{title: {title}}}
{{artist: {artist}}}
"""
    if key:
        content += f"{{key: {key}}}\n"

    content += """
{start_of_verse}
Add your [C]chords and [G]lyrics [Am]here
Edit this file to add the [F]actual chords
{end_of_verse}

{start_of_chorus}
[C]This is where the [G]chorus goes
{end_of_chorus}
"""

    with open(filepath, 'w') as f:
        f.write(content)


def create_manual_entry_template(filepath, title, artist, key=''):
    """Create a template for manual chord entry with helpful instructions"""
    content = f"""{{title: {title}}}
{{artist: {artist}}}
"""
    if key:
        content += f"{{key: {key}}}\n"

    content += f"""
{{comment: Chords could not be automatically fetched}}
{{comment: Please add chords manually by editing this file}}
{{comment: Visit Ultimate Guitar or similar site to get the chords}}
{{comment: Format: Put chords in [brackets] before the syllable}}

{{start_of_verse}}
[C]Example: Put chords in [G]brackets like [Am]this
Replace this with actual [F]lyrics and chords
{{end_of_verse}}

{{start_of_chorus}}
[C]Chorus [G]goes [Am]here [F]
{{end_of_chorus}}

{{comment: Quick reference:}}
{{comment: - Major chords: C, D, E, F, G, A, B}}
{{comment: - Minor chords: Cm, Dm, Em, Fm, Gm, Am, Bm}}
{{comment: - 7th chords: C7, D7, E7, etc.}}
{{comment: - Example line: "When I [C]find my[G]self in [Am]times of [F]trouble"}}
"""

    with open(filepath, 'w') as f:
        f.write(content)


@app.route('/library/delete/<song_id>', methods=['POST'])
def library_delete_song(song_id):
    """Delete a song from library"""
    song = get_song_by_id(song_id)

    if not song:
        return jsonify({'error': 'Song not found'}), 404

    # Delete files
    song_path = os.path.join(SONGS_DIR, song['folder'])
    if os.path.exists(song_path):
        import shutil
        shutil.rmtree(song_path)

    # Delete from database
    db.delete_song(song_id)

    return jsonify({'success': True, 'message': 'Song deleted'})


@app.route('/library/update-song-info/<song_id>', methods=['POST'])
@login_required
def library_update_song_info(song_id):
    """Update a song's title, artist, and key"""
    song = get_song_by_id(song_id)
    if not song:
        return jsonify({'error': 'Song not found'}), 404

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    artist = data.get('artist', '').strip()
    key = data.get('key', '').strip()

    updates = {}
    if title:
        updates['title'] = title
    if 'artist' in data:
        updates['artist'] = artist
    if 'key' in data:
        updates['key'] = key

    if updates:
        db.update_song(song_id, updates)

    # Update .cho file headers if it exists
    cho_path = os.path.join(SONGS_DIR, song['folder'], 'chords.cho')
    if os.path.exists(cho_path):
        with open(cho_path, 'r') as f:
            content = f.read()
        if title:
            if re.search(r'^\{title:[^}]*\}', content, re.MULTILINE):
                content = re.sub(r'^\{title:[^}]*\}', f'{{title: {title}}}', content, flags=re.MULTILINE)
            else:
                content = f'{{title: {title}}}\n' + content
        if 'artist' in data:
            if re.search(r'^\{artist:[^}]*\}', content, re.MULTILINE):
                content = re.sub(r'^\{artist:[^}]*\}', f'{{artist: {artist}}}', content, flags=re.MULTILINE)
            else:
                content = f'{{artist: {artist}}}\n' + content
        if 'key' in data:
            if key:
                if re.search(r'^\{key:[^}]*\}', content, re.MULTILINE):
                    content = re.sub(r'^\{key:[^}]*\}', f'{{key: {key}}}', content, flags=re.MULTILINE)
                else:
                    content = f'{{key: {key}}}\n' + content
        with open(cho_path, 'w') as f:
            f.write(content)

    return jsonify({'success': True})


@app.route('/library/download-status/<song_id>')
def library_download_status(song_id):
    """Get download status for a song"""
    status = db.get_download_status(song_id)
    if status:
        return jsonify(status)
    return jsonify({'status': 'not_found'}), 404


@app.route('/library/manual-chords/<song_id>', methods=['POST'])
def save_manual_chords(song_id):
    """
    Save manually entered chords for a song
    Accepts raw chord text and converts to ChordPro format
    """
    print(f"[APP] Manual chords save request for song: {song_id}")

    data = request.get_json()
    raw_chords = data.get('raw_chords', '').strip()

    if not raw_chords:
        print(f"[APP] ✗ No chords provided")
        return jsonify({'error': 'No chords provided'}), 400

    song = db.get_song_by_id(song_id)
    if not song:
        print(f"[APP] ✗ Song not found: {song_id}")
        return jsonify({'error': 'Song not found'}), 404

    print(f"[APP] Converting {len(raw_chords)} characters of raw chords to ChordPro")

    # Convert raw text to ChordPro
    from utils.chord_converter import convert_raw_to_chordpro

    try:
        chordpro_content = convert_raw_to_chordpro(
            raw_chords,
            song['title'],
            song['artist'],
            song.get('key', '')
        )

        # Save to file
        chordpro_path = os.path.join(SONGS_DIR, song['folder'], 'chords.cho')
        with open(chordpro_path, 'w') as f:
            f.write(chordpro_content)

        print(f"[APP] ✓ Successfully saved chords to {chordpro_path}")

        return jsonify({
            'success': True,
            'message': 'Chords saved successfully!',
            'song_id': song_id
        })

    except Exception as e:
        print(f"[APP] ✗ Error saving chords: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save chords: {str(e)}'}), 500


@app.route('/song/<song_id>')
def song_player(song_id):
    """Song player page with chords and audio"""
    song = get_song_by_id(song_id)

    if not song:
        return "Song not found", 404

    # Record play
    db.record_play(song_id)

    # Parse ChordPro file
    chordpro_path = os.path.join(SONGS_DIR, song['folder'], 'chords.cho')

    if not os.path.exists(chordpro_path):
        return f"ChordPro file not found: {chordpro_path}", 404

    parsed = parse_chordpro(chordpro_path)

    # Audio file path (relative to static)
    audio_url = f"/static/songs/{song['folder']}/audio.mp3"

    # Check if audio file exists
    audio_path = os.path.join(SONGS_DIR, song['folder'], 'audio.mp3')
    has_audio = os.path.exists(audio_path)

    return render_template(
        'player.html',
        song=song,
        parsed=parsed,
        audio_url=audio_url if has_audio else None
    )


@app.route('/song/<song_id>/edit', methods=['GET', 'POST'])
@login_required
def song_editor(song_id):
    """Chord editor — split-pane editor with live preview"""
    song = get_song_by_id(song_id)
    if not song:
        if request.method == 'POST':
            return jsonify({'error': 'Song not found'}), 404
        return "Song not found", 404

    if request.method == 'POST':
        data = request.get_json()
        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({'error': 'No content to save'}), 400

        # Auto-convert raw UG tab format → ChordPro if no directives
        if not re.search(r'\{(title|artist|start_of|end_of|key)\s*:', content, re.IGNORECASE):
            from utils.chord_converter import convert_raw_to_chordpro
            content = convert_raw_to_chordpro(
                content,
                song['title'],
                song.get('artist', ''),
                song.get('key', '')
            )

        chordpro_path = os.path.join(SONGS_DIR, song['folder'], 'chords.cho')
        os.makedirs(os.path.dirname(chordpro_path), exist_ok=True)
        with open(chordpro_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({'success': True, 'message': 'Chords saved!'})

    # GET — read existing content
    chordpro_path = os.path.join(SONGS_DIR, song['folder'], 'chords.cho')
    content = ''
    if os.path.exists(chordpro_path):
        with open(chordpro_path, 'r', encoding='utf-8') as f:
            content = f.read()

    return render_template('song_editor.html', song=song, content=content)


@app.route('/api/preview-chords', methods=['POST'])
def api_preview_chords():
    """Convert raw/ChordPro text to rendered HTML for the editor preview pane"""
    import tempfile
    data = request.get_json()
    content = (data.get('content') or '').strip()

    if not content:
        return jsonify({'html': ''})

    # Auto-convert raw UG tab format → ChordPro if no directives present
    if not re.search(r'\{(title|artist|start_of|end_of|key)\s*:', content, re.IGNORECASE):
        from utils.chord_converter import convert_raw_to_chordpro
        content = convert_raw_to_chordpro(content)

    # Write to a temp file and parse (reuses existing parse_chordpro)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cho', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        parsed = parse_chordpro(tmp_path)
        return jsonify({'html': parsed['html']})
    except Exception as e:
        return jsonify({'html': f'<p style="color:red">Parse error: {e}</p>'})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route('/api/songs')
def api_songs():
    """API endpoint to get all songs as JSON"""
    songs = get_all_songs()
    return jsonify(songs)


@app.route('/api/song/<song_id>')
def api_song(song_id):
    """API endpoint to get a single song"""
    song = get_song_by_id(song_id)
    if not song:
        return jsonify({'error': 'Song not found'}), 404
    return jsonify(song)


@app.route('/api/search/youtube')
def api_search_youtube():
    """API endpoint to search YouTube"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = search_youtube(query, max_results=5)
    return jsonify(results)


@app.route('/api/search/chords')
def api_search_chords():
    """API endpoint to search for chords"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = search_chords_simple(query)
    return jsonify(results)


@app.route('/settings')
@login_required
def settings_page():
    """Settings page for configuring AI server"""
    settings = load_settings()
    return render_template('settings.html', settings=settings)


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    return jsonify(load_settings())


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    new_settings = request.get_json()

    if save_settings(new_settings):
        return jsonify({'success': True, 'message': 'Settings saved'})
    else:
        return jsonify({'success': False, 'error': 'Failed to save settings'}), 500


@app.route('/api/settings/test-ollama', methods=['POST'])
def test_ollama_connection():
    """Test connection to remote Ollama server"""
    import requests as req

    data = request.get_json()
    ollama_url = data.get('ollama_url', 'http://localhost:11434')

    try:
        # Test connection by fetching available models
        response = req.get(f"{ollama_url}/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]

            return jsonify({
                'success': True,
                'message': f'Connected successfully! Found {len(models)} models.',
                'models': model_names
            })
        else:
            return jsonify({
                'success': False,
                'error': f'HTTP {response.status_code}'
            }), 400

    except req.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Connection timeout. Check URL and firewall settings.'
        }), 400
    except req.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Cannot connect to server. Is Ollama running?'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/ollama-status')
def check_ollama_status():
    """Check if Ollama AI is available for chord generation"""
    from utils.chords_fetcher import check_ollama_available, is_ollama_enabled, get_ollama_url

    enabled = is_ollama_enabled()
    available = check_ollama_available()

    if not enabled:
        message = 'Ollama is disabled. Enable in Settings to use AI chord generation.'
    elif available:
        message = f'Ollama is ready at {get_ollama_url()}'
    else:
        message = f'Ollama is enabled but not responding. Check if running at {get_ollama_url()}'

    return jsonify({
        'enabled': enabled,
        'available': available,
        'message': message
    })


# ═══════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page"""
    if session.get('user_id'):
        return redirect(url_for('home_page'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = db.verify_password(email, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['avatar_url'] = user.get('avatar_url') or ''
            return redirect(url_for('home_page'))
        else:
            error = 'Invalid email or password.'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    """Registration page"""
    if session.get('user_id'):
        return redirect(url_for('home_page'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            error = 'All fields are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            user_id = db.create_user(username, email, password)
            if user_id is None:
                error = 'Email or username already in use.'
            else:
                session['user_id'] = user_id
                session['username'] = username
                session['avatar_url'] = ''
                db.add_notification(user_id, f'Welcome to ChordPilot, {username}!')
                return redirect(url_for('home_page'))

    return render_template('login.html', error=error, register=True)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# ═══════════════════════════════════════════════════════════════════════════
# TUNER ROUTE
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/tuner')
@login_required
def tuner_page():
    """Guitar tuner page"""
    return render_template('tuner.html')


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS API
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/notifications')
def api_notifications():
    """Return unread count and notification list for current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'unread': 0, 'notifications': []})

    notifications = db.get_notifications(user_id)
    unread = db.get_unread_count(user_id)
    return jsonify({'unread': unread, 'notifications': notifications})


@app.route('/api/fetch-tab-url', methods=['POST'])
@login_required
def api_fetch_tab_url():
    """Fetch and convert chords from an Ultimate Guitar URL into ChordPro."""
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url or 'ultimate-guitar.com' not in url:
        return jsonify({'error': 'Please provide a valid Ultimate Guitar URL'}), 400

    song_id = data.get('song_id')
    song = db.get_song_by_id(song_id) if song_id else None

    raw = fetch_chords_from_url(url)
    if not raw:
        return jsonify({'error': 'Could not fetch chords from that URL. Try copying the tab text manually.'}), 422

    title = song['title'] if song else 'Unknown'
    artist = song['artist'] if song else 'Unknown'
    chordpro = convert_to_chordpro(raw, title, artist)
    return jsonify({'chordpro': chordpro})


@app.route('/api/notifications/read', methods=['POST'])
def api_mark_notifications_read():
    user_id = session.get('user_id')
    if user_id:
        db.mark_notifications_read(user_id)
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════════════════════════
# TUTORIALS API
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/tutorials')
@login_required
def api_get_tutorials():
    """Return all tutorials as JSON."""
    tutorials = db.get_tutorials()
    return jsonify(tutorials)


@app.route('/api/tutorials/add', methods=['POST'])
@login_required
def api_add_tutorial():
    """Add a tutorial — auto-fetches YT metadata via get_video_info."""
    from utils.youtube_downloader import get_video_info
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    song_hint = (data.get('song_hint') or '').strip()
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    info = get_video_info(url)
    if info:
        title = info.get('title') or url
        thumbnail = info.get('thumbnail') or ''
        channel = info.get('channel') or ''
        description = info.get('description') or ''
    else:
        # Fallback: use url as title if yt-dlp can't resolve it
        title = url
        thumbnail = channel = description = ''

    tutorial_id = db.add_tutorial(
        title=title, url=url, thumbnail=thumbnail,
        channel=channel, description=description, song_hint=song_hint
    )
    return jsonify({'success': True, 'id': tutorial_id, 'title': title,
                    'thumbnail': thumbnail, 'channel': channel})


@app.route('/api/tutorials/<int:tutorial_id>', methods=['DELETE'])
@login_required
def api_delete_tutorial(tutorial_id):
    """Delete a tutorial."""
    db.delete_tutorial(tutorial_id)
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT PROCESSOR — inject current_user into all templates
# ═══════════════════════════════════════════════════════════════════════════

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    current_user = None
    unread_count = 0
    gravatar_url = ''
    if user_id:
        current_user = db.get_user_by_id(user_id)
        unread_count = db.get_unread_count(user_id)
        if current_user:
            email = (current_user.get('email') or '').lower().strip()
            email_hash = hashlib.md5(email.encode()).hexdigest()
            gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s=80&d=identicon"
    return dict(current_user=current_user, unread_count=unread_count,
                git_version=GIT_VERSION, gravatar_url=gravatar_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
