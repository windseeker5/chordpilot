# Guitar Practice App - Quick Start

## 🎸 Get Started in 5 Minutes

### Step 1: Test the App (30 seconds)

```bash
cd /home/kdresdell/Documents/DEV/guitprac
./start.sh
```

Open browser: **http://localhost:5000**

You should see the song list with "Amazing Grace" as a sample song.

### Step 2: Add Your First Real Song (3 minutes)

#### Option A: Interactive (Easiest)

```bash
python add_song.py
```

Follow the prompts to add a song.

#### Option B: Manual

1. **Create folder:**
   ```bash
   mkdir -p static/songs/my-favorite-song
   ```

2. **Create chords file:** `static/songs/my-favorite-song/chords.cho`
   ```
   {title: Let It Be}
   {artist: The Beatles}
   {key: C}

   {start_of_verse}
   When I [C]find myself in [G]times of trouble
   [Am]Mother Mary [F]comes to me
   [C]Speaking words of [G]wisdom, let it [F]be [C]
   {end_of_verse}

   {start_of_chorus}
   Let it [Am]be, let it [G]be, let it [F]be, let it [C]be
   [C]Whisper words of [G]wisdom, let it [F]be [C]
   {end_of_chorus}
   ```

3. **Add audio:** Copy your MP3 to `static/songs/my-favorite-song/audio.mp3`

4. **Update songs.json:**
   ```json
   {
     "songs": [
       {
         "id": "amazing-grace",
         "title": "Amazing Grace",
         "artist": "John Newton",
         "key": "G",
         "folder": "amazing-grace"
       },
       {
         "id": "my-favorite-song",
         "title": "Let It Be",
         "artist": "The Beatles",
         "key": "C",
         "folder": "my-favorite-song"
       }
     ]
   }
   ```

5. **Refresh browser** - Your song appears!

### Step 3: Get Chords from Ultimate Guitar (2 minutes)

1. Go to https://www.ultimate-guitar.com
2. Search for your song
3. Copy the chords
4. Convert to ChordPro format:
   - Add `{title:}`, `{artist:}`, `{key:}` at top
   - Put chords in brackets: `[C]` instead of just `C`
   - Add `{start_of_verse}` and `{end_of_verse}` around sections

**Example conversion:**

From Ultimate Guitar:
```
Verse 1:
C                G              Am        F
When I find myself in times of trouble
```

To ChordPro:
```
{start_of_verse}
When I [C]find myself in [G]times of trouble
[Am]Mother Mary [F]comes to me
{end_of_verse}
```

### Step 4: Test Your Song

1. Click the song card in the app
2. Press Play
3. Watch the auto-scroll in action! 🎵

## 📋 ChordPro Cheat Sheet

### Metadata
```
{title: Song Name}
{artist: Artist Name}
{key: C}
```

### Chords
```
[C]Put brackets [G]before the syllable
```

### Sections
```
{start_of_verse}
Verse lyrics here
{end_of_verse}

{start_of_chorus}
Chorus lyrics here
{end_of_chorus}
```

### Comments
```
{comment: Capo 2nd fret}
{c: Strum: D-DU-UDU}
```

## 🚀 Deploy to Raspberry Pi

### First Time Setup

```bash
# 1. Copy project to Raspberry Pi
scp -r guitprac pi@raspberrypi:~/

# 2. SSH into Raspberry Pi
ssh pi@raspberrypi

# 3. Install dependencies
cd ~/guitprac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Test run
./start.sh
```

### Launch in Kiosk Mode (TV Fullscreen)

```bash
./launch_kiosk.sh
```

### Auto-Start on Boot

```bash
# 1. Install service
sudo cp guitprac.service /etc/systemd/system/

# 2. Edit paths if needed
sudo nano /etc/systemd/system/guitprac.service
# Change user and paths to match your setup

# 3. Enable and start
sudo systemctl enable guitprac
sudo systemctl start guitprac

# 4. Check it's running
sudo systemctl status guitprac
```

## 🎯 Common Tasks

### Add Another Song
```bash
python add_song.py
```

### Change Song Key or Title
Edit `songs.json` and refresh browser

### Fix Chords
Edit the `.cho` file and refresh browser

### Change Styling
Edit `templates/base.html` (font sizes, colors, etc.)

### Adjust Scroll Speed
Edit `static/js/player.js` - look for `scrollStep` calculation

### Backup Songs
```bash
cp -r static/songs ~/my-songs-backup
cp songs.json ~/my-songs-backup/
```

## 🆘 Troubleshooting

### Song Not Appearing
- Check `songs.json` is valid JSON: `python -m json.tool songs.json`
- Verify folder name matches in `songs.json`
- Refresh browser (Ctrl+F5)

### Chords Not Displaying
- Make sure chords are in brackets: `[C]` not `C`
- Check file encoding is UTF-8
- Verify brackets are matched

### Audio Not Playing
- Confirm file is named exactly `audio.mp3`
- Try a different MP3 file
- Check browser console for errors (F12)

### Auto-Scroll Wrong Speed
- Wait for page to fully load
- Toggle auto-scroll off and on
- Refresh page

## 📚 Full Documentation

- **README.md** - Complete overview
- **USAGE.md** - Detailed usage guide
- **TESTING.md** - Testing procedures
- **PROJECT_SUMMARY.md** - Technical details

## ⚡ Pro Tips

1. **Start Simple** - Begin with 2-3 favorite songs
2. **Test on TV** - Make sure fonts are readable from couch (3-4 meters)
3. **Use Good MP3s** - 128kbps or higher for quality
4. **Consistent Naming** - Use lowercase, hyphens: `amazing-grace`
5. **Add Comments** - Use `{comment:}` for capo, tempo, etc.
6. **Section Everything** - Use `{start_of_verse}` for better formatting
7. **Preview First** - Test songs on computer before Raspberry Pi

## 🎵 Example Songs Library Structure

```
static/songs/
├── amazing-grace/
│   ├── chords.cho
│   └── audio.mp3
├── let-it-be/
│   ├── chords.cho
│   └── audio.mp3
├── hallelujah/
│   ├── chords.cho
│   └── audio.mp3
├── wonderwall/
│   ├── chords.cho
│   └── audio.mp3
└── sweet-child-o-mine/
    ├── chords.cho
    └── audio.mp3
```

## ✨ What's Next?

Once you have 5-10 songs:

1. Practice regularly with the app
2. Adjust scroll speeds if needed
3. Add more songs as you learn them
4. Consider features like:
   - Dark mode for evening practice
   - Chord diagrams
   - Transpose keys
   - Practice timer

## 🎸 Ready to Play!

You're all set! Start by:

1. ✅ Running `./start.sh`
2. ✅ Opening http://localhost:5000
3. ✅ Adding your favorite songs
4. ✅ Practicing! 🎵

**Need help?** Check USAGE.md for detailed instructions.

**Found a bug?** Check TESTING.md for troubleshooting.

Happy practicing! 🎸
