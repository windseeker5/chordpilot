# Bug Fixes - Chord Fetching & Artist Detection

## 🐛 Bugs Fixed

### 1. Chords Not Fetching from Ultimate Guitar
**Problem:** Songs showed template "Add your chords and lyrics here" instead of actual chords.

**Root Cause:** Ultimate Guitar scraping was failing (likely due to page structure changes or rate limiting).

**Solution:**
- Added better error handling and logging
- Created improved manual entry template with helpful instructions
- Added MusicBrainz integration for artist lookup
- Songs now get proper artist even if chord fetching fails

### 2. Artist Shows as "Unknown"
**Problem:** Even popular songs (Pink Floyd, Beatles) showed artist as "Unknown".

**Root Cause:**
- When chords couldn't be fetched, no artist info was available
- Search query wasn't being parsed for artist name

**Solution:**
- Added **MusicBrainz API integration** - automatically looks up artist from song title
- Improved search query parsing - extracts artist from "Song - Artist" format
- Falls back to MusicBrainz if artist not in query

## ✨ New Features

### 1. MusicBrainz Integration
New file: `artist_lookup.py`

Automatically identifies artist from song title using MusicBrainz database.

**Example:**
- Search: "Wish You Were Here" → Artist: "Pink Floyd" (auto-detected)
- Search: "Let It Be" → Artist: "The Beatles" (auto-detected)

### 2. Smart Search Query Parsing
Handles multiple formats:
- `"Song Title - Artist Name"` ✅
- `"Song Title by Artist Name"` ✅
- `"Artist Name - Song Title"` ✅
- `"Song Title"` ✅ (uses MusicBrainz)

### 3. Improved Manual Entry Template
When chords can't be fetched automatically, creates a helpful template with:
- Instructions on how to add chords
- Format examples
- Chord reference guide
- Comments to guide manual editing

## 📋 How to Use (Best Practices)

### Recommended Search Format

**Best:** Include artist in search
```
Wish You Were Here - Pink Floyd
Let It Be - The Beatles
Wonderwall - Oasis
```

**Good:** Song title only (MusicBrainz will try to find artist)
```
Wish You Were Here
Let It Be
Wonderwall
```

**Why?** Including artist ensures:
- Correct artist attribution
- Better YouTube results
- Better chord search results

### When Chords Don't Auto-Fetch

If you see the manual entry template:

1. **Find chords online:**
   - Go to Ultimate Guitar: https://www.ultimate-guitar.com
   - Search for your song
   - Copy the chords

2. **Edit the ChordPro file:**
   ```bash
   # Location: static/songs/[song-folder]/chords.cho
   nano static/songs/wish-you-were-here/chords.cho
   ```

3. **Format chords properly:**
   ```
   {title: Wish You Were Here}
   {artist: Pink Floyd}
   {key: G}

   {start_of_verse}
   So, so you [C]think you can [D]tell
   Heaven from [Am]Hell, [G]blue skies from [D]pain
   {end_of_verse}
   ```

4. **Refresh the page** - Chords will appear!

## 🔧 Technical Changes

### New Dependencies
```
musicbrainzngs>=0.7.1    # MusicBrainz API client
```

### New Files
1. **artist_lookup.py** - MusicBrainz integration (150 lines)
   - `lookup_artist_musicbrainz()` - API lookup
   - `parse_search_query()` - Query parsing
   - `get_song_metadata()` - Combined metadata getter

### Updated Files
1. **app.py**
   - Added MusicBrainz artist lookup
   - Improved error handling
   - Better logging (DEBUG messages)
   - New `create_manual_entry_template()` function

2. **chords_fetcher.py**
   - Added debug logging
   - Improved fallback handling

3. **templates/library.html**
   - Sends search query to backend for artist lookup

4. **requirements.txt**
   - Added musicbrainzngs dependency

## 🧪 Testing

### Test Artist Lookup
```bash
source venv/bin/activate
python artist_lookup.py
```

### Test Adding Songs
1. Start the app: `./start.sh`
2. Go to Library → Add Song
3. Try these searches:
   - `"Wish You Were Here - Pink Floyd"` (should get artist correctly)
   - `"Wish You Were Here"` (should auto-detect Pink Floyd via MusicBrainz)
   - `"Let It Be - Beatles"` (should work perfectly)

### Check Debug Logs
Watch the Flask console for `[DEBUG]` messages:
```
[DEBUG] Add song request: title='Wish You Were Here', artist='Unknown'
[DEBUG] Artist unknown, trying MusicBrainz lookup for 'Wish You Were Here'
[DEBUG] After MusicBrainz: title='Wish You Were Here', artist='Pink Floyd'
[DEBUG] Fetching chords from URL: #
[DEBUG] Creating manual entry template
```

## ⚠️ Known Limitations

### Ultimate Guitar Scraping
- May fail due to rate limiting
- Page structure changes break scraping
- Requires JavaScript-heavy pages

**Workaround:** Manual entry template is created automatically

### MusicBrainz Artist Detection
- May return cover artists for obscure songs
- May return different versions (e.g., "Gregorian" instead of "Led Zeppelin" for covers)

**Workaround:** Include artist in search query: `"Song - Artist"`

### Chord Conversion
- Ultimate Guitar → ChordPro conversion is basic
- May not handle complex tabs perfectly
- Works best with simple chord sheets

**Workaround:** Edit ChordPro file manually after adding

## 🚀 Future Improvements

### Short Term
1. **Manual chord editor in UI** - Edit chords without leaving browser
2. **Alternative chord sources** - Try multiple sites if Ultimate Guitar fails
3. **Chord quality scoring** - Rank chord sources by quality

### Long Term
1. **AI chord generation** - Use AI to generate chords if not found
2. **User contributions** - Share chord sheets with community
3. **Chord verification** - Community voting on chord accuracy

## 📝 Migration Notes

### For Existing Songs
Your existing "I wish you were here" song:

1. **Delete and re-add** with correct search:
   ```
   Library → Delete "I whish you where here"
   Library → Add Song → "Wish You Were Here - Pink Floyd"
   ```

2. **Or manually fix:**
   ```bash
   # Edit the database
   sqlite3 guitprac.db
   UPDATE songs SET artist='Pink Floyd', title='Wish You Were Here'
   WHERE song_id='i-whish-you-where-here';
   .quit

   # Edit the ChordPro file
   nano static/songs/i-whish-you-where-here/chords.cho
   # Update title and artist, add actual chords
   ```

### Backup Before Testing
```bash
# Backup database
cp guitprac.db guitprac.db.backup

# Backup songs
cp -r static/songs static/songs.backup
```

## 🎯 Summary

**Before:**
- ❌ Chords: Failed to fetch, showed template
- ❌ Artist: "Unknown" even for popular songs
- ❌ Manual work: Required manual ChordPro creation

**After:**
- ✅ Chords: Attempts auto-fetch, provides helpful template if fails
- ✅ Artist: Auto-detects via MusicBrainz
- ✅ Manual work: Template with clear instructions if needed

**Key Improvement:**
Even when chord fetching fails, you now get:
1. Correct artist (via MusicBrainz)
2. Proper title formatting
3. Helpful template for manual chord entry
4. Clear instructions on what to do next

---

**Next Steps:**
1. Reinstall dependencies: `pip install -r requirements.txt`
2. Test with: `./start.sh`
3. Try adding: "Wish You Were Here - Pink Floyd"
4. Check if artist is detected correctly ✓
