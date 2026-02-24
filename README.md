# 🎸 ChordPilot

**AI-Powered Guitar Practice App with Multi-Source Chord Fetching**

ChordPilot is a Flask-based web application that helps guitarists practice by automatically fetching chords, downloading audio from YouTube, and displaying synchronized chord charts in ChordPro format.

---

## ✨ Features

- 🎵 **Multi-Source Chord Fetching**
  - Songsterr API (primary source)
  - Ultimate Guitar fallback
  - AI chord generation via Ollama (optional)
  - Manual entry as last resort

- 🎧 **YouTube Audio Integration**
  - Automatic audio download via yt-dlp
  - Search and select from YouTube results
  - Integrated audio player

- 📊 **ChordPro Format**
  - Industry-standard chord notation
  - Verse/Chorus/Bridge sections
  - Inline chord placement
  - Auto-scrolling during playback

- 🤖 **AI Chord Generation** (Optional)
  - Local Ollama integration
  - DeepSeek-R1, Llama 3.1, Qwen2.5 support
  - GPU acceleration for fast generation
  - Remote server support

- 📚 **Song Library Management**
  - Track play counts
  - Edit and delete songs
  - Organized file structure
  - SQLite database

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- yt-dlp (for YouTube audio)
- Ollama (optional, for AI chord generation)

### Installation

```bash
# Clone the repository
git clone git@github.com:windseeker5/chordpilot.git
cd chordpilot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open http://localhost:5000 in your browser.

---

## 🎯 Usage

### Adding a Song

1. Click **"Add Song"** in the library
2. Search for a song (format: "Song Title - Artist")
3. Select YouTube audio source
4. Select chord source (auto-detected)
5. Click **"Add to Library"**

The app will:
- ✅ Download audio from YouTube
- ✅ Fetch chords from Songsterr/Ultimate Guitar
- ✅ Generate chords with AI if needed
- ✅ Create ChordPro file
- ✅ Add to your library

### Manual Chord Entry

If automatic fetching fails:
1. The app will prompt for manual entry
2. Open Ultimate Guitar in a new tab
3. Copy/paste chords into the text area
4. Click **"Convert & Save"**

The app automatically converts raw chords to ChordPro format.

---

## 🤖 Ollama AI Setup (Optional)

For AI-powered chord generation when automatic sources fail:

### Install Ollama (Arch Linux)

```bash
# Install from AUR
yay -S ollama

# Start service
sudo systemctl start ollama

# Download model (recommended)
ollama pull deepseek-r1:7b
```

### Configure in App

1. Go to **Settings** in the app
2. Set Ollama URL: `http://localhost:11434`
3. Select model: `deepseek-r1:7b`
4. Enable AI chord generation
5. Save settings

**See [docs/how-to-install-ollama.md](docs/how-to-install-ollama.md) for detailed setup guide.**

---

## 📁 Project Structure

```
chordpilot/
├── app.py                 # Flask application
├── chords_fetcher.py      # Multi-source chord fetching
├── youtube_downloader.py  # YouTube audio download
├── chordpro_parser.py     # ChordPro format parser
├── database.py            # SQLite database management
├── templates/             # HTML templates
│   ├── base.html
│   ├── library.html
│   ├── player.html
│   └── settings.html
├── static/
│   └── songs/             # User song library (not in git)
├── docs/                  # Documentation
└── requirements.txt
```

---

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, TailwindCSS, DaisyUI
- **Icons**: Lucide
- **Audio**: yt-dlp
- **AI**: Ollama (optional)
- **Chord Format**: ChordPro

---

## 🎵 Multi-Source Chord Fetching Flow

```
User searches for song
        ↓
1. Try Songsterr API (2-3 seconds)
        ↓ (not found)
2. Try Ultimate Guitar (3-5 seconds)
        ↓ (not found)
3. Generate with Ollama AI (30-60 seconds, if enabled)
        ↓ (disabled/failed)
4. Prompt for manual entry
```

**Expected success rate: 95%+ automatic**

---

## ⚙️ Configuration

### Settings File

The app creates a `settings.json` file for user preferences:

```json
{
  "ollama_url": "http://localhost:11434",
  "ollama_model": "deepseek-r1:7b",
  "ollama_enabled": true
}
```

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

---

## 📝 License

MIT License - Feel free to use and modify for your own projects.

---

## 🙏 Acknowledgments

- **Songsterr** - For their chord API
- **Ultimate Guitar** - Chord database
- **Ollama** - Local AI models
- **yt-dlp** - YouTube audio extraction
- **ChordPro** - Chord notation standard

---

## 📧 Contact

Created by [@windseeker5](https://github.com/windseeker5)

---

**Built with ❤️ for guitarists everywhere** 🎸
