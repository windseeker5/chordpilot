"""
Chord Converter Module

Converts raw chord text from sources like Ultimate Guitar
into ChordPro format for display in the guitar practice app.

Handles common formats like:
    [Verse 1]
          C              G
    Look at the stars
          Am             F
    Look how they shine for you
"""
import re
from typing import List, Tuple

# Lines that are clearly not musical content (UG page garbage)
_GARBAGE_RE = re.compile(
    r'^(difficulty|tuning|author|tab\s+by|tabbed\s+by|transcribed\s+by|rate|print|'
    r'speed\s*:|transpose$|report\s+bad\s+tab|views?\s*:|key\s*:|saves?\s*:|'
    r'comments?\s*:|\*+\s*$)',
    re.IGNORECASE
)

# All-caps no-space blobs like "BFEB" — transposition indicators, navigation cruft
# Minimum 3 chars: 2-char strings (F#, Eb, Ab…) are valid chord names, not garbage
_ALLCAPS_BLOB_RE = re.compile(r'^[A-G#b]{3,10}$')

def _is_garbage_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if _GARBAGE_RE.match(s):
        return True
    if 'ultimate-guitar.com' in s.lower():
        return True
    # "Yellow Chords by Coldplay" / "Song Name Tab by Artist" — UG page title
    if re.search(r'\b(chords|tabs?)\s+by\b', s, re.IGNORECASE):
        return True
    # "14,502,757 views566,330 saves292 comments" — view/save stats
    # (no \b needed — "views" glued to digits still counts as a stat line)
    if re.search(r'\d[\d,]*\s*views', s, re.IGNORECASE):
        return True
    # All-caps no-space blob like "BFEB" (transposition strip) — not a lyric
    if _ALLCAPS_BLOB_RE.match(s):
        return True
    return False


def is_chord_line(line: str) -> bool:
    """
    Detect if a line contains chords (vs lyrics)

    Heuristics:
    - Contains chord patterns like C, Am, F#m, Gsus4, etc.
    - Mostly uppercase letters and spaces
    - Few or no lowercase letters (unless it's a flat/sharp modifier)
    - Has at least 2 chords OR 1 chord if line is short

    Args:
        line: The line to analyze

    Returns:
        True if the line appears to be a chord line
    """
    if not line.strip():
        return False

    # Already ChordPro inline format [Chord]lyrics — not a raw chord line
    _cp_bracket = re.compile(
        r'\[[A-G][#b]?(?:m|maj|min|dim|aug|sus)?(?:2|4|5|6|7|9|11|13)?(?:/[A-G][#b]?)?\]'
    )
    if _cp_bracket.search(line):
        return False

    # Chord pattern: C, Am, F#m, Gsus4, Cmaj7, D/F#, etc.
    chord_pattern = r'\b[A-G][#b]?(?:m|maj|min|dim|aug|sus)?(?:2|4|5|6|7|9|11|13)?(?:/[A-G][#b]?)?(?![a-zA-Z0-9])'

    # Find all chord matches
    matches = re.findall(chord_pattern, line)

    # Need at least 1 chord (we'll use other heuristics too)
    if len(matches) < 1:
        return False

    # If we have 2+ chords, very likely a chord line
    if len(matches) >= 2:
        return True

    # For single chord, need more evidence
    # Check if line is mostly spaces and the chord(s)
    stripped = line.strip()
    # Remove all chord matches
    without_chords = re.sub(chord_pattern, '', stripped)
    # If what's left is mostly empty/spaces, it's a chord line
    return len(without_chords.strip()) < 3


def merge_chords_and_lyrics(chord_line: str, lyric_line: str) -> str:
    """
    Merge chord positions with lyrics into ChordPro format

    Example:
        chord_line: "     C              G     "
        lyric_line: "Look at the stars"
        result:     "Look [C]at the stars [G]"

    Args:
        chord_line: Line containing chords positioned above lyrics
        lyric_line: Line containing the actual lyrics

    Returns:
        ChordPro formatted line with inline chords
    """
    # Find all chords and their positions
    chord_pattern = r'\b[A-G][#b]?(?:m|maj|min|dim|aug|sus)?(?:2|4|5|6|7|9|11|13)?(?:/[A-G][#b]?)?(?![a-zA-Z0-9])'
    chords: List[Tuple[int, str]] = []

    for match in re.finditer(chord_pattern, chord_line):
        chords.append((match.start(), match.group()))

    # If no chords found, just return the lyric line
    if not chords:
        return lyric_line

    # Sort chords by position (should already be sorted, but just in case)
    chords.sort(key=lambda x: x[0])

    # Build result by inserting chords at appropriate positions
    result = []
    last_pos = 0

    for chord_pos, chord in chords:
        # Find the position in the lyric line
        # If chord position is beyond lyric length, append to end
        if chord_pos >= len(lyric_line):
            # Chord is past the end of lyrics
            result.append(lyric_line[last_pos:])
            result.append(f' [{chord}]')
            last_pos = len(lyric_line)
        else:
            # Insert chord at this position
            result.append(lyric_line[last_pos:chord_pos])
            result.append(f'[{chord}]')
            last_pos = chord_pos

    # Append any remaining lyrics
    if last_pos < len(lyric_line):
        result.append(lyric_line[last_pos:])

    return ''.join(result).strip()


def strip_ug_markup(text: str) -> str:
    """Pre-process Ultimate Guitar wiki_tab content to remove UG-specific tags."""
    # Convert UG section tags to plain markers the converter can handle
    text = re.sub(r'\[verse\s*\d*\]', '[Verse]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[chorus\]', '[Chorus]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[bridge\]', '[Bridge]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[intro\]', '[Intro]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[outro\]', '[Outro]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[pre.?chorus\]', '[Pre-Chorus]', text, flags=re.IGNORECASE)
    # Convert [ch]X[/ch] → [X] (ChordPro bracket format — keeps chords inline)
    text = re.sub(r'\[ch\](.*?)\[/ch\]', r'[\1]', text)
    # Strip [tab] / [/tab] wrappers
    text = re.sub(r'\[/?tab\]', '', text)
    return text


def detect_section_marker(line: str) -> Tuple[str, str]:
    """
    Detect section markers like [Verse 1], [Chorus], etc.

    Args:
        line: The line to check

    Returns:
        Tuple of (section_type, section_label) or (None, None)
        Examples:
            "[Verse 1]" → ("verse", "Verse 1")
            "[Chorus]" → ("chorus", "Chorus")
            "[Bridge]" → ("bridge", "Bridge")
    """
    # Match lines that are ONLY a section label like [Verse 1] or [Chorus]
    # fullmatch ensures [Am]lyrics lines are NOT treated as section markers
    match = re.fullmatch(r'\[([^\]]+)\]', line.strip())
    if not match:
        return None, None

    content = match.group(1).strip()
    content_lower = content.lower()

    # Determine section type
    if 'verse' in content_lower:
        return 'verse', content
    elif 'chorus' in content_lower:
        return 'chorus', content
    elif 'bridge' in content_lower:
        return 'bridge', content
    elif 'intro' in content_lower:
        return 'intro', content
    elif 'outro' in content_lower:
        return 'outro', content
    elif 'pre-chorus' in content_lower or 'prechorus' in content_lower:
        return 'prechorus', content
    elif 'solo' in content_lower:
        return 'verse', content  # treat solo as a verse block
    else:
        # Unknown label — don't assume it's a section (could be a chord abbreviation)
        return None, None


def convert_raw_to_chordpro(raw_text: str, title: str = '', artist: str = '', key: str = '') -> str:
    """
    Convert raw chord text from Ultimate Guitar to ChordPro format

    Handles formats like:
        [Verse 1]
              C              G
        Look at the stars
              Am             F
        Look how they shine for you

    Converts to:
        {title: Yellow}
        {artist: Coldplay}
        {start_of_verse}
        Look [C]at the stars [G]
        Look how they [Am]shine for you [F]
        {end_of_verse}

    Args:
        raw_text: Raw chord text from Ultimate Guitar or similar
        title: Song title (optional)
        artist: Artist name (optional)
        key: Musical key (optional)

    Returns:
        ChordPro formatted text
    """
    if not raw_text or not raw_text.strip():
        return ""

    raw_text = strip_ug_markup(raw_text)
    lines = [l for l in raw_text.split('\n') if not _is_garbage_line(l)]
    chordpro_lines = []

    # Only add metadata headers if not already present in the raw text
    has_title = bool(re.search(r'\{title\s*:', raw_text, re.IGNORECASE))
    has_artist = bool(re.search(r'\{artist\s*:', raw_text, re.IGNORECASE))
    has_key = bool(re.search(r'\{key\s*:', raw_text, re.IGNORECASE))

    if title and not has_title:
        chordpro_lines.append(f'{{title: {title}}}')
    if artist and not has_artist:
        chordpro_lines.append(f'{{artist: {artist}}}')
    if key and not has_key:
        chordpro_lines.append(f'{{key: {key}}}')

    if (title and not has_title) or (artist and not has_artist) or (key and not has_key):
        chordpro_lines.append('')  # Blank line after headers

    # Tab line pattern: e|---, E|---, B|---, G|---, D|---, A|---, or sequences of -|0-9phb/\
    _TAB_LINE_RE = re.compile(r'^[eEBGDAd]\|', re.IGNORECASE)

    def _looks_like_tab_section(lookahead_lines):
        """Return True if any of the upcoming lines look like ASCII tab."""
        for l in lookahead_lines:
            if _TAB_LINE_RE.match(l.lstrip()):
                return True
        return False

    # Process the chord/lyric content
    in_section = None
    is_tab_section = False
    chord_line = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Pass through existing ChordPro directives verbatim (tempo, strumming, key, title, etc.)
        if re.match(r'^\s*\{[^}]+\}', line):
            chordpro_lines.append(line.rstrip())
            i += 1
            continue

        # Check for section markers like [Verse], [Chorus], [Bridge]…
        section_type, section_label = detect_section_marker(line)
        if section_type:
            # Close previous section if open
            if in_section:
                chordpro_lines.append(f'{{end_of_{in_section}}}')
                chordpro_lines.append('')  # Blank line between sections

            # For intro sections, look ahead to detect ASCII tab content
            if section_type == 'intro':
                lookahead = lines[i + 1:i + 10]
                if _looks_like_tab_section(lookahead):
                    in_section = 'tab'
                    is_tab_section = True
                    chordpro_lines.append('{start_of_tab: Intro}')
                    i += 1
                    continue

            in_section = section_type
            is_tab_section = False
            chordpro_lines.append(f'{{start_of_{section_type}}}')
            i += 1
            continue

        # Unknown [Label] line (e.g. [Instrumental], [Solo]) — skip it
        if re.fullmatch(r'\[[^\]]+\]', line.strip()):
            i += 1
            continue

        # Tab sections: pass lines through verbatim (no chord/lyric processing)
        if is_tab_section:
            chordpro_lines.append(line.rstrip())
            i += 1
            continue

        # Check if this is a chord line
        if is_chord_line(line):
            chord_line = line
            i += 1
            continue

        # This is a lyric line (or blank line)
        if chord_line:
            # We have a pending chord line - merge it with this lyric line
            merged = merge_chords_and_lyrics(chord_line, line)
            chordpro_lines.append(merged)
            chord_line = None
        else:
            # No pending chord line - just add the lyric
            chordpro_lines.append(line.rstrip())

        i += 1

    # Close final section if still open
    if in_section:
        chordpro_lines.append(f'{{end_of_{in_section}}}')

    return '\n'.join(chordpro_lines)


if __name__ == '__main__':
    # Test the converter
    raw_example = """[Verse 1]
     C              G
Look at the stars
     Am             F
Look how they shine for you

[Chorus]
     C              G
And it was all yellow
     Am             F
Your skin, oh yeah, your skin and bones"""

    print("Testing chord converter...\n")
    print("Input (raw text):")
    print("-" * 50)
    print(raw_example)
    print("\n" + "=" * 50 + "\n")

    result = convert_raw_to_chordpro(
        raw_example,
        title="Yellow",
        artist="Coldplay",
        key="C"
    )

    print("Output (ChordPro):")
    print("-" * 50)
    print(result)
