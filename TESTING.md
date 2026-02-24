# Testing Guide

This guide walks through testing the Guitar Practice App before deployment.

## Pre-Flight Checklist

### 1. Installation Test

```bash
# Check Python version (3.8+ required)
python --version

# Check virtual environment
ls -la venv/

# Check dependencies
source venv/bin/activate
pip list | grep Flask
```

Expected output:
```
Flask                  3.0.0
```

### 2. File Structure Test

```bash
# Check all required files exist
for file in app.py chordpro_parser.py requirements.txt songs.json; do
    [ -f "$file" ] && echo "✓ $file" || echo "✗ $file MISSING"
done

# Check templates
for file in templates/{base,song_list,player}.html; do
    [ -f "$file" ] && echo "✓ $file" || echo "✗ $file MISSING"
done

# Check static files
[ -f "static/js/player.js" ] && echo "✓ player.js" || echo "✗ player.js MISSING"

# Check song structure
for dir in static/songs/*/; do
    song=$(basename "$dir")
    echo "Checking $song..."
    [ -f "$dir/chords.cho" ] && echo "  ✓ chords.cho" || echo "  ✗ chords.cho MISSING"
    [ -f "$dir/audio.mp3" ] && echo "  ✓ audio.mp3" || echo "  ✗ audio.mp3 MISSING (optional for testing)"
done
```

### 3. ChordPro Parser Test

```bash
source venv/bin/activate
python << 'EOF'
from chordpro_parser import parse_chordpro
import os

# Test with Amazing Grace
cho_file = 'static/songs/amazing-grace/chords.cho'

if not os.path.exists(cho_file):
    print(f"✗ Test file not found: {cho_file}")
    exit(1)

try:
    result = parse_chordpro(cho_file)

    # Check metadata
    assert result['title'] == 'Amazing Grace', "Title mismatch"
    assert result['artist'] == 'John Newton', "Artist mismatch"
    assert result['key'] == 'G', "Key mismatch"

    # Check HTML was generated
    assert len(result['html']) > 0, "HTML not generated"
    assert '<div class="verse' in result['html'], "Verse div not found"
    assert 'chord' in result['html'], "Chords not found in HTML"

    print("✓ ChordPro parser test PASSED")
    print(f"  Title: {result['title']}")
    print(f"  Artist: {result['artist']}")
    print(f"  Key: {result['key']}")
    print(f"  HTML length: {len(result['html'])} chars")

except Exception as e:
    print(f"✗ ChordPro parser test FAILED: {e}")
    exit(1)
EOF
```

### 4. Flask App Test

```bash
source venv/bin/activate
python << 'EOF'
from app import app
import json

print("Testing Flask app...")

# Test app creation
assert app is not None, "App not created"
print("✓ App created")

# Test routes are registered
routes = [str(rule) for rule in app.url_map.iter_rules()]
expected_routes = ['/', '/song/<song_id>', '/api/songs', '/api/song/<song_id>']

for route in expected_routes:
    if any(route in r for r in routes):
        print(f"✓ Route {route}")
    else:
        print(f"✗ Route {route} MISSING")

# Test songs.json loads
with open('songs.json', 'r') as f:
    songs_data = json.load(f)
    assert 'songs' in songs_data, "songs.json missing 'songs' key"
    print(f"✓ songs.json loaded ({len(songs_data['songs'])} songs)")

print("\n✓ Flask app test PASSED")
EOF
```

## Functional Tests

### 5. Start Server Test

```bash
# Start server in background
source venv/bin/activate
export FLASK_APP=app.py
flask run --port=5000 &
FLASK_PID=$!

# Wait for startup
sleep 3

# Test homepage
echo "Testing homepage..."
curl -s http://localhost:5000 | grep -q "Guitar Practice" && echo "✓ Homepage loads" || echo "✗ Homepage failed"

# Test API
echo "Testing API..."
curl -s http://localhost:5000/api/songs | grep -q "amazing-grace" && echo "✓ API works" || echo "✗ API failed"

# Stop server
kill $FLASK_PID
wait $FLASK_PID 2>/dev/null
echo "✓ Server test complete"
```

### 6. Manual Browser Tests

Start the server:
```bash
./start.sh
```

Then test in browser (http://localhost:5000):

#### Homepage Tests
- [ ] Page loads without errors
- [ ] Song list displays
- [ ] Song cards show title, artist, key
- [ ] Play button visible on each card
- [ ] Navigation bar shows app title
- [ ] Icons render (Lucide icons)

#### Song Player Tests
- [ ] Click a song card → player page loads
- [ ] Song title and artist display
- [ ] Key badge shows
- [ ] Audio player controls visible
- [ ] ChordPro content renders
- [ ] Chords display above lyrics
- [ ] Verse sections have proper styling
- [ ] Back button returns to list

#### Audio Tests (requires MP3 file)
- [ ] Audio player shows duration
- [ ] Play button starts audio
- [ ] Auto-scroll begins with audio
- [ ] Pause button stops audio and scroll
- [ ] Restart button resets position
- [ ] Seeking audio updates scroll position
- [ ] Auto-scroll toggle works
- [ ] Progress indicator updates

#### Responsive Tests
- [ ] Page looks good on desktop
- [ ] Page looks good on tablet (if testing)
- [ ] Text is readable at TV distance (3-4 meters)
- [ ] Controls are large enough

### 7. ChordPro Format Tests

Test various ChordPro features by creating test files:

**Test 1: Basic chords**
```
{title: Test 1}
{artist: Test}
{key: C}

When I [C]find my[G]self
```
Expected: Chords display above lyrics

**Test 2: Sections**
```
{start_of_verse}
Verse text
{end_of_verse}

{start_of_chorus}
Chorus text
{end_of_chorus}
```
Expected: Chorus has left border, proper spacing

**Test 3: Comments**
```
{comment: Capo 2}
{c: Strum pattern: DDUUDU}
```
Expected: Comments show in italic gray text

**Test 4: Empty lines**
```
First line

Second line
```
Expected: Spacing between lines

**Test 5: Long lines**
```
This is [C]a very [G]long line with [Am]many chords [F]that should [C]wrap properly [G]on the [Am]screen
```
Expected: Line wraps without chord overlap

### 8. Performance Tests (Raspberry Pi)

On Raspberry Pi:

```bash
# CPU usage test
top -b -n 1 | grep python

# Memory usage test
ps aux | grep python | awk '{print $4"%"}'

# Response time test
time curl http://localhost:5000 > /dev/null
```

Expected results:
- CPU: < 10% when idle
- Memory: < 100MB
- Response time: < 2 seconds

### 9. Auto-Scroll Tests

Create a short test song (30-60 seconds) and verify:

- [ ] Scroll starts when audio plays
- [ ] Scroll speed matches song duration
- [ ] Scroll reaches bottom at song end
- [ ] Scroll stops when audio pauses
- [ ] Scroll position syncs when seeking
- [ ] Smooth scroll (no jittering)
- [ ] Toggle disables scroll

### 10. Edge Case Tests

**Empty song list:**
```bash
# Backup songs.json
cp songs.json songs.json.bak

# Test with empty list
echo '{"songs": []}' > songs.json
# Check browser shows "No songs" message
```

**Missing audio file:**
- Remove audio.mp3 from a song folder
- Try to play the song
- Expected: Audio element shows error, but page doesn't crash

**Invalid ChordPro:**
```
Unmatched [C bracket
{unclosed directive
```
Expected: Parser handles gracefully or shows error

**Very long song:**
- Test with 10+ minute song
- Verify scroll calculation works
- Check no timeout errors

**Many chords:**
- Line with 10+ chords
- Verify no overlap
- Check rendering performance

## Automated Test Suite (Future)

Create `tests/test_app.py`:

```python
import pytest
from app import app
from chordpro_parser import parse_chordpro

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Guitar Practice' in rv.data

def test_api_songs(client):
    rv = client.get('/api/songs')
    assert rv.status_code == 200
    assert rv.is_json

def test_chordpro_parser():
    result = parse_chordpro('static/songs/amazing-grace/chords.cho')
    assert result['title'] == 'Amazing Grace'
    assert 'html' in result
```

Run with:
```bash
pip install pytest
pytest tests/
```

## Pre-Deployment Checklist

Before deploying to Raspberry Pi:

- [ ] All unit tests pass
- [ ] Manual browser tests complete
- [ ] At least one song with audio tested
- [ ] Auto-scroll verified
- [ ] Performance acceptable
- [ ] No console errors
- [ ] Audio playback works
- [ ] Mobile view tested (if applicable)
- [ ] Kiosk mode tested
- [ ] Documentation reviewed
- [ ] songs.json valid
- [ ] All dependencies in requirements.txt

## Deployment Verification

After deploying to Raspberry Pi:

```bash
# Check service status
sudo systemctl status guitprac

# Check logs
sudo journalctl -u guitprac -n 50

# Check port is listening
netstat -tuln | grep 5000

# Test from another device
# From phone/laptop on same network:
curl http://[raspberry-pi-ip]:5000
```

## Troubleshooting Tests

If tests fail:

1. **Check Python version:**
   ```bash
   python --version
   # Must be 3.8+
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

3. **Check file permissions:**
   ```bash
   chmod -R 755 .
   chmod 644 static/songs/*/*.cho
   ```

4. **Verify JSON syntax:**
   ```bash
   python -m json.tool songs.json
   ```

5. **Check Flask logs:**
   - Look at terminal output when running Flask
   - Check for Python tracebacks
   - Verify no import errors

6. **Browser console:**
   - Open browser DevTools (F12)
   - Check Console tab for JavaScript errors
   - Check Network tab for failed requests

## Test Data

For thorough testing, create multiple test songs:

1. **Short song** (30 seconds) - Test quick scroll
2. **Long song** (10+ minutes) - Test long scroll
3. **Dense chords** - Many chords per line
4. **Sparse chords** - Few chords, mostly lyrics
5. **Different keys** - Various keys (C, G, D, Am, etc.)
6. **Unicode** - Special characters in lyrics
7. **No sections** - Plain text without verse/chorus
8. **All sections** - Verse, chorus, bridge, etc.

## Success Criteria

The app is ready for use when:

✅ All automated tests pass
✅ Homepage loads in < 2 seconds
✅ Song player loads in < 2 seconds
✅ Audio plays without glitches
✅ Auto-scroll is smooth (no stuttering)
✅ Chords display correctly positioned
✅ Readable from TV distance
✅ No JavaScript errors
✅ Works in kiosk mode
✅ Performance acceptable on Raspberry Pi
✅ All songs in library load correctly

Happy testing! 🎸
