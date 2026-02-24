# 🤖 Ollama Setup Guide for Arch Linux

## 📦 **Installation (Super Easy on Arch)**

```bash
# Install Ollama from AUR
yay -S ollama

# OR use the official script
curl -fsSL https://ollama.com/install.sh | sh

# Start the service
sudo systemctl start ollama

# Enable on boot (optional)
sudo systemctl enable ollama
```

---

## 🎵 **Which Model to Download?**

For **guitar chord generation**, here are your options:

### **Recommended: Llama 3.1 8B** ⭐
```bash
ollama pull llama3.1:8b
```
**Why:**
- Best balance of speed and quality
- 8GB RAM usage
- Generates accurate chords for popular songs
- Fast enough (30-45 seconds)

---

### **Alternative Options:**

| Model | RAM | Speed | Quality | Command |
|-------|-----|-------|---------|---------|
| **Llama 3.1 8B** ⭐ | 8GB | Medium | Excellent | `ollama pull llama3.1:8b` |
| **Mistral 7B** | 7GB | Fast | Good | `ollama pull mistral:7b` |
| **Qwen 2.5 7B** | 7GB | Fast | Very Good | `ollama pull qwen2.5:7b` |
| **Llama 3.1 70B** | 40GB | Slow | Best | `ollama pull llama3.1:70b` |

**My recommendation:** Start with **llama3.1:8b**

---

## ⚙️ **Configure in Your App**

1. **Start Ollama** (if not running):
   ```bash
   sudo systemctl start ollama
   ```

2. **Open your app**: http://localhost:5000/settings

3. **Configure:**
   - **Ollama URL**: `http://localhost:11434` (default)
   - **Model**: `llama3.1:8b`
   - **Enable**: ✅ Check the box

4. **Test Connection** → Should show "Connected successfully!"

5. **Save Settings**

---

## 🧪 **Test It**

```bash
# Quick test
ollama run llama3.1:8b "Generate a simple chord progression for a song in the key of C major"
```

Should respond quickly with chord suggestions.

---

## 🚀 **Usage in Your App**

Once configured:

1. Search for a song (e.g., "Wonderwall - Oasis")
2. If Songsterr/Ultimate Guitar fail → Ollama kicks in automatically
3. Wait 30-60 seconds → AI generates complete ChordPro format
4. Song added with chords!

---

## 💾 **Systemd Service (Already Configured)**

Ollama runs as a systemd service:

```bash
# Check status
sudo systemctl status ollama

# View logs
journalctl -u ollama -f

# Restart if needed
sudo systemctl restart ollama
```

---

## 🎯 **Performance Notes**

- **First generation**: ~60 seconds (model loads into RAM)
- **Subsequent generations**: ~30 seconds (model cached)
- **RAM usage**: ~8GB for llama3.1:8b
- **CPU vs GPU**:
  - CPU only: Works fine, a bit slower
  - With GPU (NVIDIA): Much faster (5-10 seconds)

---

## 🔥 **GPU Acceleration (Optional but Fast)**

If you have an NVIDIA GPU:

```bash
# Install CUDA support (already have it probably)
yay -S cuda

# Ollama auto-detects GPU
# Check with:
ollama run llama3.1:8b --verbose
```

Should show: `using GPU`

---

## ✅ **Quick Setup Summary**

```bash
# 1. Install
yay -S ollama

# 2. Start service
sudo systemctl start ollama

# 3. Download model
ollama pull llama3.1:8b

# 4. Test
ollama run llama3.1:8b "Hi"

# 5. Configure in app at http://localhost:5000/settings
```

**Done! AI chord generation ready.** 🎸

---

## 🆘 **Troubleshooting**

**Port already in use?**
```bash
sudo netstat -tlnp | grep 11434
sudo systemctl restart ollama
```

**Model not found?**
```bash
ollama list  # See installed models
ollama pull llama3.1:8b  # Download if missing
```

**Can't connect from app?**
```bash
curl http://localhost:11434/api/tags
# Should return JSON with installed models
```

---

## 📝 **Notes**

- This guide is for the Guitar Practice App
- Ollama provides AI-powered chord generation as a fallback when Songsterr and Ultimate Guitar don't have the song
- The generated chords are in ChordPro format, ready to use in the app
- Generation time: 30-60 seconds per song (acceptable for rare/obscure songs)

---

**Last updated:** 2026-02-24
