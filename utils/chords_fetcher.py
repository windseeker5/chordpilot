"""
Guitar chords fetcher for Guitar Practice App
Fetches chords from various sources and converts to ChordPro format
Multi-source support: Songsterr API → Ultimate Guitar → Ollama AI → Manual Entry
"""
import re
import requests
import json
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


# ═══════════════════════════════════════════════════════════════════════════
# SONGSTERR API INTEGRATION (Primary Source)
# ═══════════════════════════════════════════════════════════════════════════

def search_songsterr(song_title: str, artist: str) -> Optional[str]:
    """
    Search Songsterr API for guitar chords/tabs
    Returns ChordPro formatted content if found
    """
    print(f"[CHORDS] Trying Songsterr API for: {song_title} - {artist}")

    try:
        # Songsterr search endpoint
        search_url = "https://www.songsterr.com/api/songs"
        params = {
            'pattern': f"{song_title} {artist}",
            'size': 5
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[CHORDS] ✗ Songsterr HTTP {response.status_code}")
            return None

        results = response.json()
        if not results:
            print(f"[CHORDS] ✗ No Songsterr results")
            return None

        # Get first matching song
        song = results[0]
        song_artist = song.get('artist', artist)  # artist is a string in Songsterr API
        print(f"[CHORDS] Found: '{song.get('title')}' by '{song_artist}'")

        # Songsterr only provides metadata; tab content is Guitar Pro binary format.
        print(f"[CHORDS] Songsterr: metadata only (no tab content available), skipping")
        return None

    except requests.exceptions.Timeout:
        print(f"[CHORDS] ✗ Songsterr timeout")
        return None
    except Exception as e:
        print(f"[CHORDS] ✗ Songsterr error: {e}")
        return None


def generate_songsterr_template(song_data: dict, title: str, artist: str) -> Optional[str]:
    """
    Songsterr uses Guitar Pro binary format — no real tab text available via API.
    Return None so the pipeline falls through to Ultimate Guitar or AI.
    """
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ULTIMATE GUITAR INTEGRATION (Secondary Source)
# ═══════════════════════════════════════════════════════════════════════════

def search_ultimate_guitar(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search Ultimate Guitar for chords/tabs
    Returns list of results with URL, title, artist, rating, type
    """
    print(f"[CHORDS] Searching Ultimate Guitar for: {query}")

    try:
        # Ultimate Guitar search API endpoint
        search_url = "https://www.ultimate-guitar.com/search.php"
        params = {
            'search_type': 'title',
            'value': query
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        print(f"[CHORDS] Requesting: {search_url}?search_type=title&value={query}")
        response = requests.get(search_url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[CHORDS] ✗ HTTP error: {response.status_code}")
            return []

        print(f"[CHORDS] ✓ Got response, parsing...")

        # Parse the page to find the data
        # Ultimate Guitar embeds search results in a JavaScript variable
        match = re.search(r'window\.UGAPP\.store\.page\s*=\s*({.*?});', response.text, re.DOTALL)

        if not match:
            print("[CHORDS] ✗ Could not find search results in page")
            print(f"[CHORDS] Response preview: {response.text[:500]}...")
            return []

        import json
        data = json.loads(match.group(1))

        results = []

        # Extract results from the data structure
        if 'data' in data and 'results' in data['data']:
            for item in data['data']['results'][:max_results]:
                if item.get('type') in ['Chords', 'Tab']:
                    results.append({
                        'id': item.get('id', ''),
                        'title': item.get('song_name', ''),
                        'artist': item.get('artist_name', ''),
                        'url': item.get('tab_url', ''),
                        'rating': item.get('rating', 0),
                        'votes': item.get('votes', 0),
                        'type': item.get('type', ''),
                        'version': item.get('version', 1)
                    })

            print(f"[CHORDS] ✓ Found {len(results)} results")
            if results:
                print(f"[CHORDS] Top result: {results[0]['title']} by {results[0]['artist']} ({results[0]['type']})")
        else:
            print("[CHORDS] ✗ No results in data structure")

        return results

    except Exception as e:
        print(f"[CHORDS] ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_chords_from_url(url: str) -> Optional[str]:
    """
    Fetch chords content from Ultimate Guitar URL.
    Returns raw chord content (not yet ChordPro format).

    Strategy A: Parse div.js-store[data-content] (URL-encoded JSON).
    Strategy B: Find window.UGAPP JSON blob using JSONDecoder boundary finder.
    """
    print(f"[CHORDS] Fetching from URL: {url}")

    try:
        from urllib.parse import unquote

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[CHORDS] ✗ HTTP error: {response.status_code}")
            return None

        print(f"[CHORDS] ✓ Got response ({len(response.text)} chars), extracting content...")

        # ── Strategy A: js-store div (preferred) ─────────────────────────────
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            store_div = soup.find('div', class_='js-store')
            if store_div and store_div.get('data-content'):
                data = json.loads(unquote(store_div['data-content']))
                content = data['store']['page']['data']['tab_view']['wiki_tab']['content']
                print(f"[CHORDS] ✓ Strategy A: extracted {len(content)} chars from js-store div")
                return content
        except Exception as e:
            print(f"[CHORDS] Strategy A failed: {e}")

        # ── Strategy B: window.UGAPP JSON blob with proper boundary finder ───
        try:
            marker = 'window.UGAPP.store.page = '
            idx = response.text.find(marker)
            if idx != -1:
                start = response.text.index('{', idx)
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(response.text[start:])
                content = data['data']['tab_view']['wiki_tab']['content']
                print(f"[CHORDS] ✓ Strategy B: extracted {len(content)} chars from UGAPP blob")
                return content
        except Exception as e:
            print(f"[CHORDS] Strategy B failed: {e}")

        print("[CHORDS] ✗ Could not extract chord content from page")
        return None

    except Exception as e:
        print(f"[CHORDS] ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_to_chordpro(raw_content: str, title: str, artist: str) -> str:
    """
    Convert raw chord content to ChordPro format
    Uses the chord_converter module for improved conversion
    """
    print(f"[CHORDS] Converting to ChordPro format...")

    # Try to detect key (look for common patterns)
    key = detect_key(raw_content)

    # Use the improved chord converter
    from utils.chord_converter import convert_raw_to_chordpro

    result = convert_raw_to_chordpro(
        raw_text=raw_content,
        title=title,
        artist=artist,
        key=key or ''
    )

    print(f"[CHORDS] ✓ Converted to ChordPro ({len(result)} characters)")
    return result


def is_chord_line(line: str) -> bool:
    """Check if a line contains chords"""
    # Remove spaces
    line = line.strip()
    if not line:
        return False

    # Split into tokens
    tokens = line.split()

    # Check if most tokens look like chords
    chord_pattern = re.compile(r'^[A-G](#|b)?(m|maj|min|dim|aug|sus)?(2|4|5|6|7|9|11|13)?(/[A-G](#|b)?)?$')

    chord_count = sum(1 for token in tokens if chord_pattern.match(token))

    # If more than 50% are chords, it's probably a chord line
    return len(tokens) > 0 and (chord_count / len(tokens)) > 0.5


def extract_chords_positions(chord_line: str) -> List[tuple]:
    """Extract chords and their positions from a chord line"""
    chords = []
    chord_pattern = re.compile(r'[A-G](#|b)?(m|maj|min|dim|aug|sus)?(2|4|5|6|7|9|11|13)?(/[A-G](#|b)?)?')

    for match in chord_pattern.finditer(chord_line):
        chords.append((match.start(), match.group()))

    return chords


def insert_chords_inline(lyric_line: str, chords: List[tuple]) -> str:
    """Insert chords inline with lyrics at the correct positions"""
    if not chords:
        return lyric_line

    result = []
    last_pos = 0

    for pos, chord in chords:
        # Add lyrics up to this chord position
        if pos < len(lyric_line):
            result.append(lyric_line[last_pos:pos])
            result.append(f'[{chord}]')
            last_pos = pos
        else:
            # Chord is beyond the lyric line
            result.append(lyric_line[last_pos:])
            result.append(f'[{chord}]')
            last_pos = len(lyric_line)

    # Add remaining lyrics
    if last_pos < len(lyric_line):
        result.append(lyric_line[last_pos:])

    return ''.join(result)


def detect_key(content: str) -> Optional[str]:
    """Try to detect the musical key from the content"""
    # Look for key indicators in the content
    key_pattern = re.compile(r'(?:key|capo|tune)[:\s]+([A-G](#|b)?(m|maj|min)?)', re.IGNORECASE)
    match = key_pattern.search(content)

    if match:
        return match.group(1)

    # Otherwise, try to detect from most common chord
    chords = re.findall(r'\b([A-G](#|b)?m?)\b', content)
    if chords:
        # Return most common chord as likely key
        from collections import Counter
        most_common = Counter(chords).most_common(1)
        if most_common:
            return most_common[0][0]

    return None


def fetch_chords_from_chordify(song_title: str, artist: str = None) -> Optional[str]:
    """
    Alternative: Try to fetch chords using a simpler method
    This searches for chords on multiple sites and returns the best match
    """
    try:
        # Build search query
        if artist:
            search_query = f"{song_title} {artist} chords"
        else:
            search_query = f"{song_title} chords"

        # For now, return None - this will trigger the manual template
        # In the future, we could add more chord sources here
        return None

    except Exception as e:
        print(f"Alternative chord fetch error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# OLLAMA AI INTEGRATION (Tertiary Source - AI Fallback)
# ═══════════════════════════════════════════════════════════════════════════

def get_ollama_url() -> str:
    """Get Ollama URL from settings (supports remote AI server)"""
    try:
        import os
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('ollama_url', 'http://localhost:11434')
    except Exception as e:
        print(f"[CHORDS] Warning: Could not load settings: {e}")

    return 'http://localhost:11434'


def get_ollama_model() -> str:
    """Get Ollama model from settings"""
    try:
        import os
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('ollama_model', 'mistral:7b')
    except Exception as e:
        print(f"[CHORDS] Warning: Could not load settings: {e}")

    return 'mistral:7b'


def is_ollama_enabled() -> bool:
    """Check if Ollama is enabled in settings"""
    try:
        import os
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('ollama_enabled', False)
    except Exception as e:
        print(f"[CHORDS] Warning: Could not load settings: {e}")

    return False


def check_ollama_available() -> bool:
    """Check if Ollama is running (local or remote)"""
    if not is_ollama_enabled():
        return False

    try:
        ollama_url = get_ollama_url()
        response = requests.get(f"{ollama_url}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


def generate_chords_ollama(song_title: str, artist: str, key: str = '') -> Optional[str]:
    """
    Generate ChordPro format chords using Ollama AI (local or remote)
    Requires: Ollama running and enabled in settings
    """
    if not is_ollama_enabled():
        print(f"[CHORDS] Ollama is disabled in settings")
        return None

    ollama_url = get_ollama_url()
    ollama_model = get_ollama_model()

    print(f"[CHORDS] Generating with Ollama AI: {song_title} - {artist}")
    print(f"[CHORDS]   Server: {ollama_url}")
    print(f"[CHORDS]   Model: {ollama_model}")

    try:
        # Ollama HTTP API endpoint
        endpoint = f"{ollama_url}/api/generate"

        prompt = f"""Generate a complete ChordPro format guitar chord chart for this song:

Title: {song_title}
Artist: {artist}
{f'Key: {key}' if key else ''}

Requirements:
- Start with metadata tags: {{{{title: }}}}, {{{{artist: }}}}, {{{{key: }}}}
- Use section markers: {{{{start_of_verse}}}}, {{{{start_of_chorus}}}}, {{{{start_of_bridge}}}}, etc.
- Place chords in square brackets before syllables: [Am], [C], [G7], [Dsus4]
- Include complete and accurate lyrics
- Choose an appropriate guitar-friendly key (C, G, D, A, E major or their relative minors)
- Make it playable and singable
- Output ONLY valid ChordPro format, no explanations

Example format:
{{{{title: Let It Be}}}}
{{{{artist: The Beatles}}}}
{{{{key: C}}}}

{{{{start_of_verse}}}}
[C]When I [G]find myself in [Am]times of [F]trouble
[C]Mother [G]Mary [F]comes to [C]me
{{{{end_of_verse}}}}

Now generate for "{song_title}" by {artist}:"""

        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower = more consistent
                "num_predict": 2000  # Max tokens
            }
        }

        print("[CHORDS] Calling Ollama API (this may take 30-60 seconds)...")
        response = requests.post(endpoint, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"[CHORDS] ✗ Ollama HTTP {response.status_code}")
            return None

        result = response.json()
        chordpro_content = result.get('response', '').strip()

        # Basic validation
        if chordpro_content and '{title:' in chordpro_content:
            print(f"[CHORDS] ✓ Ollama generated {len(chordpro_content)} chars")
            return chordpro_content
        else:
            print(f"[CHORDS] ✗ Ollama output invalid format")
            return None

    except requests.exceptions.Timeout:
        print("[CHORDS] ✗ Ollama timeout (>120s)")
        return None
    except requests.exceptions.ConnectionError:
        print(f"[CHORDS] ✗ Cannot connect to Ollama at {ollama_url}")
        return None
    except Exception as e:
        print(f"[CHORDS] ✗ Ollama error: {e}")
        return None


def search_chords_simple(query: str) -> List[Dict]:
    """
    Legacy function - redirects to multi-source search
    Kept for backward compatibility
    """
    return search_chords_multi_source(query)


def search_chords_multi_source(query: str) -> List[Dict]:
    """
    Multi-source chord search with intelligent fallback

    Strategy:
    1. Try Songsterr API (fast, reliable)
    2. Try Ultimate Guitar (existing implementation)
    3. Generate with Ollama if both fail (and if enabled)
    4. Return manual entry template as last resort
    """
    print(f"[CHORDS] ═══════════════════════════════════════════════════════")
    print(f"[CHORDS] Multi-source search: '{query}'")
    print(f"[CHORDS] ═══════════════════════════════════════════════════════")

    from utils.artist_lookup import parse_search_query
    parsed = parse_search_query(query)
    title = parsed['title']
    artist = parsed['artist'] or 'Unknown'

    # SOURCE 1: Songsterr API (primary)
    print(f"[CHORDS] [1/3] Trying Songsterr API...")
    songsterr_chords = search_songsterr(title, artist)
    if songsterr_chords:
        print(f"[CHORDS] ✓ Songsterr success!")
        return [{
            'id': 'songsterr',
            'title': title,
            'artist': artist,
            'url': 'songsterr',  # Special marker
            'rating': 5,
            'votes': 100,
            'type': 'Chords',
            'version': 1,
            'chords_content': songsterr_chords  # Pre-fetched content
        }]

    # SOURCE 2: Ultimate Guitar (existing)
    print(f"[CHORDS] [2/3] Trying Ultimate Guitar...")
    ug_results = search_ultimate_guitar(query)
    if ug_results:
        print(f"[CHORDS] ✓ Ultimate Guitar found {len(ug_results)} results")
        return ug_results

    # SOURCE 3: Ollama AI Generation (if available and enabled)
    if check_ollama_available():
        print(f"[CHORDS] [3/3] Trying Ollama AI generation...")
        ai_chords = generate_chords_ollama(title, artist)
        if ai_chords:
            print(f"[CHORDS] ✓ Ollama AI generated chords successfully!")
            return [{
                'id': 'ollama-generated',
                'title': title,
                'artist': artist,
                'url': 'ai-generated',  # Special marker
                'rating': 4,
                'votes': 1,
                'type': 'AI Generated',
                'version': 1,
                'chords_content': ai_chords  # Pre-generated content
            }]
    else:
        if is_ollama_enabled():
            print(f"[CHORDS] ⚠ Ollama enabled but not responding")
            print(f"[CHORDS]   Check if Ollama is running at: {get_ollama_url()}")
        else:
            print(f"[CHORDS] ⚠ Ollama is disabled in settings")
            print(f"[CHORDS]   To enable: Visit Settings page and configure Ollama")

    # FALLBACK: Manual entry template
    print(f"[CHORDS] ✗ All sources failed - using manual entry")
    print(f"[CHORDS] ═══════════════════════════════════════════════════════")
    return [{
        'id': 'manual-entry',
        'title': title,
        'artist': artist,
        'url': 'manual',
        'rating': 0,
        'votes': 0,
        'type': 'Manual Entry',
        'version': 1
    }]


if __name__ == '__main__':
    # Test the module
    print("Testing chords fetcher...")

    query = "Let It Be - Beatles"
    results = search_chords_simple(query)

    print(f"\nFound {len(results)} results for '{query}':")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['title']} by {result['artist']}")
        print(f"   Type: {result['type']}, Rating: {result['rating']}, URL: {result['url']}")
