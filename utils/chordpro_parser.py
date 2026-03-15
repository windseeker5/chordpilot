"""
ChordPro Parser for Guitar Practice App
Parses .cho files and converts to HTML with Tailwind CSS classes
"""
import html
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
    tempo_match = re.search(r'\{tempo:\s*(\d+)\}', content, re.IGNORECASE)
    tempo = int(tempo_match.group(1)) if tempo_match else None

    # Extract strumming patterns (multiple allowed)
    strumming_patterns = []
    pending_label = None
    for m in re.finditer(r'\{(strumming_label|strumming):\s*(.+?)\}', content, re.IGNORECASE):
        directive = m.group(1).lower()
        value = m.group(2).strip()
        if directive == 'strumming_label':
            pending_label = value
        else:
            strumming_patterns.append({'label': pending_label or '', 'pattern': value})
            pending_label = None

    # Parse lines and convert to HTML
    html_lines = []
    lines = content.split('\n')
    in_tab = False
    in_section = None  # tracks current open section type

    # Map from directive keyword to (css_classes, display_label)
    SECTION_MAP = {
        'verse':     ('verse my-3',                                              'Verse'),
        'chorus':    ('chorus my-3 ml-8 border-l-4 border-blue-500 pl-4',       'Chorus'),
        'bridge':    ('bridge my-3',                                             'Bridge'),
        'intro':     ('intro-section my-3',                                      'Intro'),
        'outro':     ('outro-section my-3',                                      'Outro'),
        'prechorus': ('prechorus my-3',                                          'Pre-Chorus'),
    }

    def _close_section():
        nonlocal in_section
        if in_section:
            html_lines.append('</div>')
            in_section = None

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
                in_section = None
            else:
                html_lines.append(original_line.rstrip())
            continue

        # Handle directives
        if line.startswith('{'):
            directive_lower = line.lower()

            if 'start_of_tab' in directive_lower:
                _close_section()
                label_match = re.search(r'\{start_of_tab:?\s*(.+?)\}', line, re.IGNORECASE)
                label = label_match.group(1).strip() if label_match else 'Tab'
                html_lines.append(
                    f'<div class="tab-section">'
                    f'<div class="tab-label">{label}</div>'
                    '<pre class="tab-pre">'
                )
                in_tab = True
                in_section = 'tab'
                continue
            elif 'end_of_tab' in directive_lower:
                html_lines.append('</pre></div>')
                in_tab = False
                in_section = None
                continue

            # Generic start_of_* handler
            start_match = re.match(r'\{start_of_(\w+)(?::?\s*(.+?))?\}', line, re.IGNORECASE)
            if start_match:
                _close_section()
                sec_key = start_match.group(1).lower()
                sec_label_override = start_match.group(2).strip() if start_match.group(2) else None
                css, default_label = SECTION_MAP.get(sec_key, ('my-6', sec_key.title()))
                display_label = sec_label_override or default_label
                html_lines.append(f'<div class="{css}">')
                html_lines.append(f'<div class="section-label">{display_label}</div>')
                in_section = sec_key
                continue

            # Generic end_of_* handler
            if re.match(r'\{end_of_\w+\}', line, re.IGNORECASE):
                _close_section()
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
    _close_section()

    return {
        'title': title.group(1) if title else 'Unknown',
        'artist': artist.group(1) if artist else 'Unknown',
        'key': key.group(1) if key else '',
        'html': '\n'.join(html_lines),
        'tempo': tempo,
        'strumming_patterns': strumming_patterns,
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

    # Only iterate over valid-chord matches; invalid brackets become inline text
    valid_matches = [m for m in all_matches if _CHORD_NAME_RE.match(m.group(1))]

    # Detect chord-only progression lines (no real lyric text anywhere on the line)
    def _all_lyrics_empty():
        if not valid_matches:
            return False
        # Check text BEFORE the first chord
        before_first = line[:valid_matches[0].start()]
        before_first = chord_pattern.sub(lambda mm: mm.group(1) if not _CHORD_NAME_RE.match(mm.group(1)) else '', before_first)
        if before_first.strip():
            return False
        # Check text AFTER each chord
        for i, m in enumerate(valid_matches):
            next_start = valid_matches[i + 1].start() if i + 1 < len(valid_matches) else len(line)
            after = line[m.end():next_start]
            after = chord_pattern.sub(lambda mm: mm.group(1) if not _CHORD_NAME_RE.match(mm.group(1)) else '', after)
            if after.strip():
                return False
        return True

    if _all_lyrics_empty():
        chips = ''.join(
            f'<span class="chord-chip">{m.group(1)}</span>'
            for m in valid_matches
        )
        return f'<div class="chord-prog-line my-3">{chips}</div>'

    result_html = '<div class="chord-line my-2">'

    pos = 0

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
                f'<span class="lyric text-2xl">{html.escape(before)}</span>'
                '</span>'
            )

        # Text following this chord up to the next valid chord
        next_start = valid_matches[i + 1].start() if i + 1 < len(valid_matches) else len(line)
        after = line[chord_end:next_start]
        # Strip brackets from invalid [bracket] content in 'after'
        after = chord_pattern.sub(lambda m: m.group(1) if not _CHORD_NAME_RE.match(m.group(1)) else m.group(0), after)

        # When trailing text has no real content, pad with nbsp proportional to chord name
        # so adjacent chords (e.g. [B] [Bsus4]) don't visually merge
        if not after.strip():
            display_after = '\u00a0' * max(len(chord_name) + 1, 3)
        else:
            display_after = after

        result_html += (
            '<span class="chord-segment">'
            f'<span class="chord text-blue-600 font-bold whitespace-nowrap">{chord_name}</span>'
            f'<span class="lyric text-2xl">{html.escape(display_after)}</span>'
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
