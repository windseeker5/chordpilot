"""
Artist lookup using MusicBrainz API
Helps identify artist from song title
"""
import musicbrainzngs
import requests
from typing import Optional, Dict


# Set user agent for MusicBrainz
musicbrainzngs.set_useragent(
    "GuitarPracticeApp",
    "1.0",
    "https://github.com/yourusername/guitprac"
)


def lookup_artist_musicbrainz(song_title: str) -> Optional[Dict]:
    """
    Look up artist information using MusicBrainz API

    Args:
        song_title: Song title to search for

    Returns:
        Dict with 'artist', 'title', 'year' or None if not found
    """
    try:
        # Search for recording
        result = musicbrainzngs.search_recordings(
            query=song_title,
            limit=5
        )

        if not result or 'recording-list' not in result:
            return None

        recordings = result['recording-list']

        if not recordings:
            return None

        # Get the first (best) match
        best_match = recordings[0]

        # Extract artist
        artist = "Unknown"
        if 'artist-credit' in best_match and best_match['artist-credit']:
            artist_credit = best_match['artist-credit'][0]
            if 'artist' in artist_credit:
                artist = artist_credit['artist'].get('name', 'Unknown')

        # Extract title
        title = best_match.get('title', song_title)

        # Extract year if available
        year = None
        if 'release-list' in best_match and best_match['release-list']:
            release = best_match['release-list'][0]
            if 'date' in release:
                year = release['date'][:4]  # Get year only

        return {
            'artist': artist,
            'title': title,
            'year': year,
            'score': best_match.get('ext:score', '100')
        }

    except Exception as e:
        print(f"MusicBrainz lookup error: {e}")
        return None


def format_title_case(text: str) -> str:
    """
    Convert text to proper title case

    Examples:
        "yellow" → "Yellow"
        "wish you were here" → "Wish You Were Here"
        "COLDPLAY" → "Coldplay"
    """
    if not text:
        return text

    # Simple title case - capitalizes first letter of each word
    # For more complex rules, could use titlecase library
    return text.strip().title()


def parse_search_query(query: str) -> Dict:
    """
    Parse search query to extract artist and title

    Handles formats like:
    - "Song Title - Artist Name"  (most common - song FIRST)
    - "Song Title, Artist Name"
    - "Song Title by Artist Name"
    - "Song Title Artist Name"

    Returns:
        Dict with 'title' and 'artist' (may be None)
    """
    query = query.strip()

    # Try "Title - Artist" format (most common)
    # Format is ALWAYS: Song - Artist (not based on length!)
    if ' - ' in query:
        parts = query.split(' - ', 1)
        return {
            'title': format_title_case(parts[0].strip()),
            'artist': format_title_case(parts[1].strip())
        }

    # Try "Title, Artist" format (comma separator)
    if ', ' in query:
        parts = query.split(', ', 1)
        return {
            'title': format_title_case(parts[0].strip()),
            'artist': format_title_case(parts[1].strip())
        }

    # Try "Title by Artist" format
    if ' by ' in query.lower():
        parts = query.lower().split(' by ', 1)
        return {
            'title': format_title_case(query[:len(parts[0])].strip()),
            'artist': format_title_case(query[len(parts[0])+4:].strip())
        }

    # No clear artist separator, just use the whole query as title
    return {'title': format_title_case(query), 'artist': None}


def get_song_metadata(query: str) -> Dict:
    """
    Get comprehensive song metadata from query

    Tries to extract from query first, then uses MusicBrainz lookup

    Returns:
        Dict with 'title', 'artist', 'year'
    """
    # Parse query first
    parsed = parse_search_query(query)
    title = parsed['title']
    artist = parsed['artist']

    # If we don't have an artist, try MusicBrainz
    if not artist or artist.lower() == 'unknown':
        mb_result = lookup_artist_musicbrainz(title)
        if mb_result:
            artist = format_title_case(mb_result['artist'])
            # Use MusicBrainz title if it's more complete
            if len(mb_result['title']) > len(title):
                title = format_title_case(mb_result['title'])

    return {
        'title': title,
        'artist': artist or 'Unknown',
        'year': None
    }


if __name__ == '__main__':
    # Test the module
    test_queries = [
        "Wish You Were Here",
        "I wish you were here - Pink Floyd",
        "Let It Be - Beatles",
        "Wonderwall by Oasis",
        "Stairway to Heaven"
    ]

    print("Testing artist lookup...\n")

    for query in test_queries:
        print(f"Query: '{query}'")
        result = get_song_metadata(query)
        print(f"  → Title: {result['title']}")
        print(f"  → Artist: {result['artist']}")
        print()
