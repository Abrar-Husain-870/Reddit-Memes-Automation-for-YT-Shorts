# GTA V Brainrot Shorts Pipeline

Creates high-quality GTA V brainrot-style YouTube Shorts / Instagram Reels locally on your PC.

## Quick Start

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_your_key_here
```

## Usage

**Full pipeline (download → process → script → voiceover → render):**
```bash
python run.py
```

**Use existing clips (skip download):**
```bash
python run.py --skip-download
```

**Pick a specific style:**
```bash
python run.py --style chaotic
python run.py --style meme
python run.py --style story
python run.py --style npc
```

## Individual Steps

```bash
python download.py --count 2              # Download 2 gameplay videos
python process.py                          # Extract short clips from raw videos
python script.py --style chaotic           # Generate brainrot script
python voiceover.py --text "your script"   # Synthesize TTS audio
python render.py --clip clip.mp4 --audio voiceover.mp3 --narration "your script"
```

## Output

- Rendered short: `data/output/final_short.mp4`
- Voiceover: `data/output/voiceover.mp3`
- Clips: `data/clips/`
- Raw downloads: `data/raw/`

Upload the final MP4 to YouTube Shorts or Instagram Reels manually.

## Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and in PATH
- [Groq API key](https://console.groq.com) (free tier)
- Internet connection (for downloading clips and TTS)