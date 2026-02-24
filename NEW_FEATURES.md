# Guitar Practice App - New Features

## 🎉 What's New

The Guitar Practice App now includes **automatic song fetching** from YouTube and online chord sources! No more manual ChordPro file creation or MP3 hunting.

## ✨ Key New Features

### 1. **Sidebar Navigation**
- Clean sidebar menu with Home and Library pages
- Responsive design (hamburger menu on mobile)
- Always accessible navigation

### 2. **Library Management Page**
- View all your songs in a organized table
- See play counts and when songs were added
- Edit and delete songs
- Search and add new songs automatically

### 3. **Automatic Song Fetching**
- **Search by song name** - Just type "Let It Be - Beatles"
- **YouTube Integration** - Automatically finds and downloads audio
- **Chords Fetching** - Searches Ultimate Guitar for chord charts
- **One-click add** - Select results and add to library instantly

### 4. **SQLite Database**
- Replaced JSON file with proper database
- Tracks play counts and last played date
- Download status tracking
- Better performance and reliability

### 5. **Background Downloads**
- Songs download in the background
- Continue browsing while audio downloads
- Automatic ChordPro conversion
- Error handling and status tracking

## 📋 How to Use the New Features

### Adding a Song Automatically

1. **Open Library Page**
   - Click "Library" in the sidebar
   - Or visit: http://localhost:5000/library

2. **Click "Add Song"**
   - Opens the search modal

3. **Search for Your Song**
   - Type: "Song Title - Artist Name"
   - Example: "Let It Be - Beatles"
   - Click "Search"

4. **Review Results**
   - **YouTube Results** - Audio options (automatically selected best match)
   - **Chord Results** - Guitar tab options (from Ultimate Guitar)
   - Click any result to select it

5. **Add to Library**
   - Click "Add to Library"
   - Download starts in background
   - Page refreshes when done

6. **Practice!**
   - Song appears in your library
   - Click Play to start practicing
   - Auto-scroll works with downloaded audio

### Managing Your Library

**View All Songs:**
- Go to Library page
- See all songs with details:
  - Title, Artist, Key
  - Date added
  - Play count
  - Actions (Play, Edit, Delete)

**Delete a Song:**
- Click the trash icon
- Confirm deletion
- Song and files are removed

**Play a Song:**
- Click the play icon
- Opens player page
- Play count increments automatically

## 🔧 Technical Details

### New Dependencies

```
yt-dlp          - YouTube audio downloader
requests        - HTTP library for web scraping
beautifulsoup4  - HTML parsing for chords
```

### New Files

1. **database.py** - SQLite database management
2. **youtube_downloader.py** - YouTube audio extraction
3. **chords_fetcher.py** - Chord fetching and conversion
4. **templates/library.html** - Library management page

### Updated Files

1. **app.py** - New routes for library management
2. **templates/base.html** - Added sidebar navigation
3. **templates/player.html** - Handle missing audio files
4. **requirements.txt** - Added new dependencies

### Database Schema

**songs table:**
- id (primary key)
- song_id (unique identifier)
- title, artist, key
- folder (where files are stored)
- youtube_url, chords_source
- date_added, last_played
- play_count

**downloads table:**
- id (primary key)
- song_id (foreign key)
- status (pending, downloading_audio, fetching_chords, completed, error)
- progress (0-100)
- error_message
- started_at, completed_at

## 🚀 Installation & Setup

### First Time Setup

```bash
# 1. Install new dependencies
source venv/bin/activate
pip install -r requirements.txt

# 2. Initialize database (automatic)
python database.py

# 3. Verify yt-dlp is installed
python youtube_downloader.py

# 4. Start the app
./start.sh
```

### Migrating from Old Version

If you were using the previous version with `songs.json`:

```bash
# The migration happens automatically
python database.py

# Your songs.json will be backed up as songs.json.backup
# Songs are imported into the database
# Original files (chords.cho, audio.mp3) remain unchanged
```

## 📖 Usage Examples

### Example 1: Adding "Amazing Grace"

1. Open Library → Click "Add Song"
2. Search: "Amazing Grace hymn guitar"
3. Select:
   - YouTube: "Amazing Grace Guitar Tutorial"
   - Chords: "Amazing Grace - John Newton"
4. Click "Add to Library"
5. Wait for download (30-60 seconds)
6. Song appears in library

### Example 2: Adding "Let It Be - Beatles"

1. Open Library → Click "Add Song"
2. Search: "Let It Be - Beatles"
3. Results show:
   - Multiple YouTube versions
   - Multiple chord versions
4. Select your preferred versions
5. Click "Add to Library"
6. Download happens in background

### Example 3: Bulk Adding Songs

1. Add first song (e.g., "Wonderwall")
2. While it downloads, search for next song
3. Add multiple songs in sequence
4. Each downloads in its own background thread
5. Refresh to see completed downloads

## ⚙️ Configuration

### YouTube Download Quality

Edit `youtube_downloader.py`:

```python
'--audio-quality', '0',  # Best quality (0 = best, 9 = worst)
```

### Search Result Limits

Edit `app.py`:

```python
youtube_results = search_youtube(query, max_results=5)  # Change 5 to any number
```

### Download Timeout

Edit `youtube_downloader.py`:

```python
timeout=30  # Seconds
```

## 🐛 Troubleshooting

### "yt-dlp not installed" Warning

**Problem:** YouTube downloads won't work

**Solution:**
```bash
source venv/bin/activate
pip install yt-dlp
```

**Verify:**
```bash
yt-dlp --version
```

### Download Fails or Hangs

**Problem:** Song stuck in "downloading" status

**Possible causes:**
1. YouTube video is unavailable
2. Network connection issue
3. yt-dlp needs update

**Solutions:**
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Check YouTube URL manually
yt-dlp <youtube-url>

# Check database status
sqlite3 guitprac.db "SELECT * FROM downloads ORDER BY started_at DESC LIMIT 5;"
```

### Chords Not Found

**Problem:** No chord results appear

**Possible causes:**
1. Ultimate Guitar rate limiting
2. Song name spelling
3. Song not in database

**Solutions:**
- Try different search terms
- Add song manually with basic template
- Edit ChordPro file after adding

### Database Errors

**Problem:** Database locked or corrupted

**Solution:**
```bash
# Backup current database
cp guitprac.db guitprac.db.backup

# Reinitialize
rm guitprac.db
python database.py

# Manual migration if needed
```

## 🎯 Tips & Best Practices

### Search Tips

1. **Be specific** - Include artist name
   - Good: "Let It Be - Beatles"
   - Bad: "Let It Be"

2. **Include "guitar"** for better YouTube results
   - "Amazing Grace guitar tutorial"

3. **Try variations** if no results
   - "Wonderwall acoustic"
   - "Wonderwall Oasis"

### Library Organization

1. **Add key information** - Makes transposing easier later
2. **Check audio quality** - Listen before practicing
3. **Review chords** - Edit ChordPro if needed
4. **Regular backups** - Copy `guitprac.db` and `static/songs/`

### Performance

1. **Limit concurrent downloads** - Add 1-2 songs at a time
2. **Clean up old songs** - Delete unused songs to save space
3. **Monitor disk space** - Audio files can be large

## 🔮 Future Enhancements

Planned features:
- **Manual chord editing** - Edit chords in web interface
- **Batch import** - Add multiple songs at once
- **Playlist support** - Organize songs into playlists
- **Chord transposition** - Change key on-the-fly
- **Practice statistics** - Track practice time and progress
- **Export/Import** - Share song libraries
- **Advanced search** - Filter by key, artist, play count

## 📊 Comparison: Old vs New

| Feature | Old Version | New Version |
|---------|-------------|-------------|
| Add song | Manual (10-15 min) | Automatic (1-2 min) |
| Find chords | Copy/paste from web | Automatic search |
| Get audio | Find and download MP3 | Automatic from YouTube |
| Storage | JSON file | SQLite database |
| Library view | Simple list | Detailed table |
| Navigation | Top bar only | Sidebar + top bar |
| Track plays | No | Yes |
| Background download | No | Yes |
| Error handling | Basic | Advanced with status |

## 🤝 Contributing

If you improve these features:

1. **Test thoroughly** - Especially downloads
2. **Handle errors gracefully** - Network can fail
3. **Document changes** - Update this file
4. **Consider rate limits** - Don't abuse external services

## 📝 Notes

### Legal Considerations

- **YouTube**: Respect YouTube's Terms of Service
- **Chords**: Ultimate Guitar content has copyright
- **Personal use**: This app is for personal practice only
- **Distribution**: Don't redistribute downloaded content

### Performance Considerations

- YouTube downloads can be slow (30-120 seconds)
- Chord fetching is usually fast (< 5 seconds)
- Database is fast for up to 1000+ songs
- Audio files take disk space (~3-5 MB per song)

### Privacy

- No data is sent to external servers (except YouTube/Ultimate Guitar for search)
- All songs stored locally
- No tracking or analytics
- Database is local only

---

**Enjoy your enhanced guitar practice experience!** 🎸

For questions or issues, check the documentation or review the code comments.
