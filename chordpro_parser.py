"""
ChordPro Parser for Guitar Practice App
Parses .cho files and converts to HTML with Tailwind CSS classes
"""
import re
from typing import Dict, List, Tuple


def parse_chordpro(file_path: str) -> Dict:
    """
    Parse a ChordPro format file and return structured data.

    Args:
        file_path: Path to the .cho file

    Returns:
        Dictionary with title, artist, key, and HTML content
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    title = re.search(r'\{title:\s*(.+?)\}', content, re.IGNORECASE)
    artist = re.search(r'\{artist:\s*(.+?)\}', content, re.IGNORECASE)
    key = re.search(r'\{key:\s*(.+?)\}', content, re.IGNORECASE)

    # Parse lines and convert to HTML
    html_lines = []
    lines = content.split('\n')
    in_verse = False
    in_chorus = False

    for line in lines:
        line = line.strip()

        # Skip empty lines at the start
        if not line and not html_lines:
            continue

        # Handle directives
        if line.startswith('{'):
            directive_lower = line.lower()

            if 'start_of_verse' in directive_lower or 'sov' in directive_lower:
                html_lines.append('<div class="verse my-6">')
                in_verse = True
                continue
            elif 'end_of_verse' in directive_lower or 'eov' in directive_lower:
                html_lines.append('</div>')
                in_verse = False
                continue
            elif 'start_of_chorus' in directive_lower or 'soc' in directive_lower:
                html_lines.append('<div class="chorus my-6 ml-8 border-l-4 border-blue-500 pl-4">')
                in_chorus = True
                continue
            elif 'end_of_chorus' in directive_lower or 'eoc' in directive_lower:
                html_lines.append('</div>')
                in_chorus = False
                continue
            elif 'comment' in directive_lower or 'c:' in directive_lower:
                comment = re.search(r'\{(?:comment:|c:)\s*(.+?)\}', line, re.IGNORECASE)
                if comment:
                    html_lines.append(f'<p class="text-gray-500 italic text-xl my-2">{comment.group(1)}</p>')
                continue
            else:
                # Skip other directives (title, artist, key already extracted)
                continue

        # Empty lines
        if not line:
            html_lines.append('<div class="h-4"></div>')
            continue

        # Parse chord lines
        html_line = parse_chord_line(line)
        html_lines.append(html_line)

    # Close any open sections
    if in_verse:
        html_lines.append('</div>')
    if in_chorus:
        html_lines.append('</div>')

    return {
        'title': title.group(1) if title else 'Unknown',
        'artist': artist.group(1) if artist else 'Unknown',
        'key': key.group(1) if key else '',
        'html': '\n'.join(html_lines)
    }


def parse_chord_line(line: str) -> str:
    """
    Parse a single line with chords in [brackets] and return HTML.

    Chords in brackets are displayed above the lyrics.
    Example: "When I [C]find myself in [G]times of trouble"

    Returns HTML with chords positioned above lyrics using spans.
    """
    if '[' not in line:
        # No chords, just lyrics
        return f'<div class="lyric-line text-2xl my-1 leading-relaxed">{line}</div>'

    # Split into chord and lyric segments
    result_html = '<div class="chord-line my-2 leading-loose">'

    # Find all chord positions
    chord_pattern = re.compile(r'\[([^\]]+)\]')
    last_end = 0

    for match in chord_pattern.finditer(line):
        chord = match.group(1)
        start = match.start()
        end = match.end()

        # Add any text before this chord
        before_text = line[last_end:start]

        # Create a span for chord + lyric segment
        result_html += f'<span class="chord-segment inline-block relative">'
        result_html += f'<span class="chord absolute -top-7 left-0 text-blue-600 font-bold text-xl whitespace-nowrap">{chord}</span>'
        result_html += f'<span class="lyric text-2xl">{before_text}</span>'
        result_html += '</span>'

        last_end = end

    # Add any remaining text after the last chord
    remaining = line[last_end:]
    if remaining:
        result_html += f'<span class="text-2xl">{remaining}</span>'

    result_html += '</div>'
    return result_html


def get_song_duration_seconds(audio_path: str) -> float:
    """
    Get the duration of an audio file in seconds.
    This is a placeholder - in production, you might use mutagen or similar.
    For now, we'll get duration from the browser.
    """
    # This will be handled in JavaScript by the HTML5 audio element
    return 0.0
