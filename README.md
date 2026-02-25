# ChordPilot

A personal guitar practice web app. Build a song library with chords and audio, play along, and optionally use Ollama AI to generate chord charts.

## What it does

- Song library — add songs with chords + audio, track play history
- Chord display in ChordPro format (verses, chorus, bridge, inline chords)
- YouTube audio download via yt-dlp
- Auto-scroll synchronized to playback
- Chord input: copy-paste from Ultimate Guitar OR AI generation via Ollama
- Multi-source fallback: Songsterr → Ultimate Guitar → Ollama AI → manual paste

## Quick Start

**Prerequisites:** Python 3.10+, yt-dlp, Ollama (optional)

```bash
git clone git@github.com:windseeker5/chordpilot.git
cd chordpilot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start.sh
```

Open http://localhost:5000

## Adding a Song

1. Go to **Library → Add Song**
2. Search for a song (e.g. "Let It Be - Beatles")
3. Select a YouTube audio source
4. Chords are auto-fetched: Songsterr first, then Ultimate Guitar, then Ollama AI
5. If all sources fail, paste chords manually from Ultimate Guitar

## Project Structure

```
chordpilot/
├── app.py
├── utils/
│   ├── database.py
│   ├── chords_fetcher.py
│   ├── chord_converter.py
│   ├── chordpro_parser.py
│   ├── artist_lookup.py
│   └── youtube_downloader.py
├── templates/
├── static/
│   └── songs/          # user song library (not in git)
├── docs/
│   └── how-to-install-ollama.md
└── requirements.txt
```

## Chord Sources (fallback chain)

1. **Songsterr API** — fast, reliable primary source
2. **Ultimate Guitar** — scrape search results
3. **Ollama AI** — local AI generation (optional, requires setup)
4. **Manual paste** — copy from Ultimate Guitar yourself

## Ollama Setup (optional)

Ollama enables AI chord generation when Songsterr and Ultimate Guitar both fail.

```bash
# Install (Arch Linux)
yay -S ollama
sudo systemctl start ollama
ollama pull deepseek-r1:7b
```

Then in the app go to **Settings**, set the Ollama URL and model, and enable AI chord generation.

See [docs/how-to-install-ollama.md](docs/how-to-install-ollama.md) for a detailed setup guide.

## Tech Stack

Flask, SQLite, TailwindCSS/DaisyUI, yt-dlp, Ollama
