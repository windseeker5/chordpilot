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
    in_tab = False

    for original_line in lines:
        line = original_line.strip()

        # Skip empty lines at the start
        if not line and not html_lines:
            continue

        # Inside a tab block: emit raw lines (whitespace preserved)
        if in_tab:
            if line.startswith('{') and 'end_of_tab' in line.lower():
                html_lines.append('</pre></div>')
                in_tab = False
            else:
                html_lines.append(original_line.rstrip())
            continue

        # Handle directives
        if line.startswith('{'):
            directive_lower = line.lower()

            if 'start_of_tab' in directive_lower:
                label_match = re.search(r'\{start_of_tab:?\s*(.+?)\}', line, re.IGNORECASE)
                label = label_match.group(1).strip() if label_match else 'Tab'
                html_lines.append(
                    f'<div class="tab-section"><div class="tab-label">{label}</div>'
                    '<pre class="tab-pre">'
                )
                in_tab = True
                continue
            elif 'end_of_tab' in directive_lower:
                html_lines.append('</pre></div>')
                in_tab = False
                continue
            elif 'start_of_verse' in directive_lower or 'sov' in directive_lower:
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
    if in_tab:
        html_lines.append('</pre></div>')
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


# Valid chord name: must start with a note letter (A-G) + optional modifiers
_CHORD_NAME_RE = re.compile(
    r'^[A-G][#b]?(?:m(?:aj)?|min|dim|aug|sus|add)?(?:\d+)?(?:/[A-G][#b]?)?$'
)


def parse_chord_line(line: str) -> str:
    """
    Parse a single line with chords in [brackets] and return HTML.

    Each chord is paired with the text that FOLLOWS it, so the chord
    name sits directly above the syllable where it is played.
    Text before the first chord gets an empty chord-slot for alignment.
    Bracket content that doesn't look like a chord (e.g. [Instrumental])
    is treated as plain text.

    Example: "When I [C]find myself in [G]times of trouble"
      → empty | "When I "
      → C     | "find myself in "
      → G     | "times of trouble"
    """
    if '[' not in line:
        return f'<div class="lyric-line text-2xl my-1 leading-relaxed">{line}</div>'

    chord_pattern = re.compile(r'\[([^\]]+)\]')
    all_matches = list(chord_pattern.finditer(line))

    # If no bracket contains a valid chord name, treat the whole line as a lyric
    if not any(_CHORD_NAME_RE.match(m.group(1)) for m in all_matches):
        # Strip any remaining brackets and emit as a plain lyric line
        plain = chord_pattern.sub(r'\1', line)
        return f'<div class="lyric-line text-2xl my-1 leading-relaxed">{plain}</div>'

    result_html = '<div class="chord-line my-2">'

    pos = 0
    # Only iterate over valid-chord matches; invalid brackets become inline text
    valid_matches = [m for m in all_matches if _CHORD_NAME_RE.match(m.group(1))]

    for i, match in enumerate(valid_matches):
        chord_name = match.group(1)
        chord_end = match.end()

        # Text before this chord (may include invalid [bracket] content)
        before = line[pos:match.start()]
        # Strip brackets from any non-chord bracket in 'before'
        before = chord_pattern.sub(lambda m: m.group(1) if not _CHORD_NAME_RE.match(m.group(1)) else m.group(0), before)
        if before:
            result_html += (
                '<span class="chord-segment">'
                '<span class="chord"></span>'
                f'<span class="lyric text-2xl">{before}</span>'
                '</span>'
            )

        # Text following this chord up to the next valid chord
        next_start = valid_matches[i + 1].start() if i + 1 < len(valid_matches) else len(line)
        after = line[chord_end:next_start]
        # Strip brackets from invalid [bracket] content in 'after'
        after = chord_pattern.sub(lambda m: m.group(1) if not _CHORD_NAME_RE.match(m.group(1)) else m.group(0), after)

        # Trailing chord with no lyric text looks like a subscript — give it a nbsp
        display_after = after if after.strip() else ('\u00a0' if not after else after)

        result_html += (
            '<span class="chord-segment">'
            f'<span class="chord text-blue-600 font-bold whitespace-nowrap">{chord_name}</span>'
            f'<span class="lyric text-2xl">{display_after}</span>'
            '</span>'
        )

        pos = next_start

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
