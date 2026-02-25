"""
Guitar Practice App (guitprac)
A Flask app for guitar practice with chord display, audio playback, and auto-scroll
Now with library management and automatic song fetching from YouTube!
Multi-source chord fetching: Songsterr → Ultimate Guitar → Ollama AI → Manual
"""
import os
import json
import threading
from flask import Flask, render_template, jsonify, request, redirect, url_for
from utils.chordpro_parser import parse_chordpro
from utils import database as db
from utils.youtube_downloader import search_youtube, download_audio, check_ytdlp_installed
from utils.chords_fetcher import search_ultimate_guitar, fetch_chords_from_url, convert_to_chordpro, search_chords_simple
from utils.artist_lookup import get_song_metadata, parse_search_query


app = Flask(__name__)
app.config['SECRET_KEY'] = 'guitar-practice-app-secret-key'

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
def index():
    """Home page with song list"""
    songs = get_all_songs()
    return render_template('song_list.html', songs=songs)


@app.route('/library')
def library():
    """Library management page"""
    songs = get_all_songs()
    ytdlp_installed = check_ytdlp_installed()
    return render_template('library.html', songs=songs, ytdlp_installed=ytdlp_installed)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
