# Guitar Practice App - Usage Guide

## Quick Reference

### Starting the App

```bash
# Development mode (with auto-reload)
./start.sh

# Kiosk mode (fullscreen on Raspberry Pi)
./launch_kiosk.sh

# Or manually
source venv/bin/activate
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```

Access at: **http://localhost:5000**

### Adding a New Song

**Interactive method:**
```bash
python add_song.py
```

**Manual method:**

1. Create folder: `static/songs/song-name/`
2. Add `chords.cho` file (see ChordPro format below)
3. Add `audio.mp3` file
4. Update `songs.json`

## ChordPro Format Reference

### Basic Structure

```
{title: Song Title}
{artist: Artist Name}
{key: C}

{start_of_verse}
When I [C]find myself in [G]times of trouble
[Am]Mother Mary [F]comes to me
{end_of_verse}

{start_of_chorus}
Let it [C]be, let it [G]be
{end_of_chorus}
```

### Directives

| Directive | Alias | Description |
|-----------|-------|-------------|
| `{title: ...}` | `{t: ...}` | Song title |
| `{artist: ...}` | - | Artist name |
| `{key: ...}` | - | Song key (C, G, D, etc.) |
| `{start_of_verse}` | `{sov}` | Begin verse section |
| `{end_of_verse}` | `{eov}` | End verse section |
| `{start_of_chorus}` | `{soc}` | Begin chorus section |
| `{end_of_chorus}` | `{eoc}` | End chorus section |
| `{comment: ...}` | `{c: ...}` | Comment (instructions) |

### Chord Placement

Chords go in **square brackets** before the syllable where they're played:

```
When I [C]find my[G]self in [Am]times of [F]trouble
```

This displays:
```
        C       G             Am          F
When I find myself in times of trouble
```

### Tips for Good Formatting

1. **Align chords above lyrics** - Put the bracket right before the syllable
   ```
   Good: When I [C]find myself
   Bad:  When [C]I find myself  (chord on wrong syllable)
   ```

2. **Use sections** - Organize with verse/chorus markers
   ```
   {start_of_verse}
   Verse lyrics here
   {end_of_verse}
   ```

3. **Add comments** - Use for instructions or notes
   ```
   {comment: Capo on 2nd fret}
   {c: Strum pattern: D-DU-UDU}
   ```

4. **Empty lines** - Use for spacing between sections
   ```
   {end_of_verse}

   {start_of_chorus}
   ```

## Songs.json Format

```json
{
  "songs": [
    {
      "id": "unique-song-id",
      "title": "Song Title",
      "artist": "Artist Name",
      "key": "C",
      "folder": "folder-name"
    }
  ]
}
```

**Fields:**
- `id` - Unique identifier (usually same as folder name)
- `title` - Display name
- `artist` - Artist/composer name
- `key` - Musical key (C, G, D, Am, etc.)
- `folder` - Folder name in `static/songs/`

## Player Controls

### Main Controls

- **Play** - Start audio and auto-scroll
- **Pause** - Pause audio and scrolling
- **Restart** - Reset to beginning
- **Back** - Return to song list

### Auto-Scroll

- **Toggle** - Enable/disable auto-scrolling
- Automatically syncs with audio playback
- Speed calculated from song duration
- Pauses when audio is paused
- Resumes from correct position when seeking

### Browser Audio Controls

The native audio controls provide:
- **Volume** - Adjust playback volume
- **Timeline** - Seek to specific position
- **Download** - Download MP3 file
- **Speed** - Playback speed (some browsers)

## Raspberry Pi Setup

### First-Time Installation

```bash
# 1. Update system
sudo apt update
sudo apt upgrade

# 2. Install Python and dependencies
sudo apt install python3 python3-venv python3-pip

# 3. Install Chromium
sudo apt install chromium-browser

# 4. Clone/copy project
cd ~
git clone <repository> guitprac
# or copy files from another computer

# 5. Install Python dependencies
cd guitprac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Test run
./start.sh
```

### Auto-Start on Boot

**Option 1: Systemd Service (recommended)**

```bash
# 1. Copy service file
sudo cp guitprac.service /etc/systemd/system/

# 2. Edit paths if needed
sudo nano /etc/systemd/system/guitprac.service

# 3. Enable and start
sudo systemctl enable guitprac
sudo systemctl start guitprac

# 4. Check status
sudo systemctl status guitprac
```

**Option 2: Desktop Autostart**

Create `~/.config/autostart/guitprac.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Guitar Practice App
Exec=/home/kdresdell/Documents/DEV/guitprac/launch_kiosk.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

### Kiosk Mode Settings

For best TV experience, edit `launch_kiosk.sh` with additional flags:

```bash
chromium-browser \
  --kiosk \
  --disable-infobars \
  --noerrdialogs \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --start-fullscreen \
  --window-size=1920,1080 \
  http://localhost:5000
```

### Performance Tuning

If you experience performance issues on Raspberry Pi:

1. **Reduce DaisyUI animations** - Edit `templates/base.html`:
   ```html
   <html lang="en" data-theme="light" data-reduced-motion="true">
   ```

2. **Disable browser GPU** - Add to chromium flags:
   ```bash
   --disable-gpu
   --disable-software-rasterizer
   ```

3. **Lower scroll smoothness** - Edit `static/js/player.js`:
   ```javascript
   const scrollStep = diff * 0.05; // Lower = smoother but may lag
   ```

## Troubleshooting

### Songs Not Appearing

**Check songs.json syntax:**
```bash
python -m json.tool songs.json
```

**Verify folder structure:**
```bash
ls -la static/songs/
```

**Check Flask logs:**
```bash
# In terminal running Flask, look for errors
```

### Audio Not Playing

**Supported formats:**
- MP3 (most common, best compatibility)
- OGG (some browsers)
- WAV (large files)
- M4A (some browsers)

**Test audio file:**
```bash
# Play with system audio player
mpv static/songs/song-name/audio.mp3
# or
aplay static/songs/song-name/audio.mp3
```

**Check permissions:**
```bash
chmod 644 static/songs/*/audio.mp3
```

### Chords Overlapping or Misaligned

**Common causes:**
1. Too many chords in one line
2. Chords too close together
3. Font size too large for screen

**Solutions:**
1. Split long lines in ChordPro file
2. Add spaces between chords: `[C] [G]` not `[C][G]`
3. Adjust font sizes in `templates/base.html`

### Auto-Scroll Too Fast/Slow

**Check audio duration:**
- Make sure the page fully loaded
- Check browser console for JavaScript errors
- Try reloading the page

**Manual adjustment (future feature):**
Currently speed is calculated automatically. To manually adjust:
1. Edit `static/js/player.js`
2. Modify the `scrollStep` calculation
3. Refresh browser

### Raspberry Pi Performance Issues

**Check CPU usage:**
```bash
top
```

**Check memory:**
```bash
free -h
```

**Disable animations:**
```html
<!-- In templates/base.html -->
<style>
* {
  animation: none !important;
  transition: none !important;
}
</style>
```

**Use hardware acceleration:**
```bash
# Enable GL Driver in raspi-config
sudo raspi-config
# Advanced Options > GL Driver > GL (Fake KMS)
```

## Tips and Best Practices

### Creating Good Chord Sheets

1. **Keep it simple** - Don't overcrowd with chords
2. **Use sections** - Verse, chorus, bridge
3. **Add comments** - Capo, tempo, special techniques
4. **Test on TV** - Make sure it's readable from couch
5. **Match audio** - Ensure chords align with recording

### Organizing Songs

1. **Consistent naming** - Use lowercase, hyphens (e.g., `amazing-grace`)
2. **Group by artist** - Consider subfolders (future feature)
3. **Key tags** - Always specify the key
4. **Audio quality** - Use good-quality MP3s (128kbps minimum)

### Practice Workflow

1. **Preview on small screen** - Test formatting
2. **Test on TV** - Check readability from distance
3. **Adjust if needed** - Font sizes, spacing
4. **Play through once** - Check scroll speed
5. **Fine-tune** - Adjust ChordPro timing if needed

## Advanced Usage

### Custom Styling

Edit `templates/base.html` to customize appearance:

```html
<style>
/* Make chords larger */
.chord {
    font-size: 1.5rem !important;
}

/* Change chord color */
.chord {
    color: #ff6b6b !important;
}

/* Increase line spacing */
.chord-line {
    margin-top: 1rem !important;
}
</style>
```

### Multiple Users/Songbooks

Create separate `songs.json` files:

```bash
# songs-rock.json
# songs-folk.json
# songs-worship.json
```

Modify `app.py` to accept a query parameter:
```python
songbook = request.args.get('book', 'songs')
songs_file = f"{songbook}.json"
```

Access: `http://localhost:5000?book=songs-rock`

### API Usage

The app provides a simple API:

```bash
# Get all songs
curl http://localhost:5000/api/songs

# Get single song
curl http://localhost:5000/api/song/amazing-grace
```

Use for external integrations or automation.

## Keyboard Shortcuts (Future Feature)

Planned keyboard shortcuts:
- `Space` - Play/Pause
- `R` - Restart
- `Esc` - Back to list
- `←/→` - Seek backward/forward
- `↑/↓` - Scroll speed adjustment

## Getting Help

1. **Check logs** - Look at Flask output in terminal
2. **Browser console** - Press F12, check for JavaScript errors
3. **Verify files** - Make sure all files exist with correct names
4. **Test ChordPro** - Use the test script to verify parsing
5. **Check permissions** - Ensure files are readable

**Test ChordPro parsing:**
```bash
source venv/bin/activate
python -c "
from chordpro_parser import parse_chordpro
result = parse_chordpro('static/songs/your-song/chords.cho')
print(result)
"
```

## Resources

- **ChordPro format:** https://www.chordpro.org/
- **Ultimate Guitar:** https://www.ultimate-guitar.com/ (get chords)
- **Flask documentation:** https://flask.palletsprojects.com/
- **DaisyUI components:** https://daisyui.com/

## Contributing

If you improve the app or add features:
1. Test thoroughly on Raspberry Pi
2. Document changes
3. Keep it simple and maintainable
4. Share with the community

Enjoy your guitar practice! 🎸
