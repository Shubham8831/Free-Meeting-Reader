# 🎙️ Meeting Reader — Step A

Upload a meeting recording → get a **transcript** + an **AI summary**
(summary, key points, decisions, action items).

**Stack:** Groq Whisper (transcription) · LangChain + Groq LLM `openai/gpt-oss-120b` (summary) · FastAPI (web UI)

---

## What each file does

| File | Purpose |
|------|---------|
| `transcribe.py` | Audio → text using Groq Whisper |
| `summarize.py`  | Transcript → summary using **LangChain** (`ChatGroq`) |
| `app.py`        | Web page: upload → transcribe → summarize → show |
| `.env`          | Your Groq API key + model names (never share this) |
| `requirements.txt` | Python packages |

---

## Setup (one time)

Open PowerShell in this folder and run:

```powershell
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
.\venv\Scripts\Activate.ps1

# 3. Install packages
pip install -r requirements.txt
```

> If step 2 gives a "running scripts is disabled" error, run this once, then retry:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## Run it

```powershell
uvicorn app:app --reload
```

Then open **http://127.0.0.1:8000** in your browser, pick an audio file, and click
**Transcribe & Summarize**.

---

## Test the pieces on their own (optional)

```powershell
python transcribe.py "C:\path\to\meeting.mp3"   # prints the transcript
python summarize.py                              # runs a tiny built-in sample
```

---

## Notes & limits

- Groq's free tier caps audio uploads at **~25 MB**. For bigger files you'll later
  need to split the audio into chunks (a future step).
- Supported audio: mp3, m4a, wav, mp4, and more.
- **Security:** your API key is in `.env`. Since it was shared in chat, regenerate it
  at https://console.groq.com/keys after testing. `.gitignore` keeps `.env` out of git.

---

## What's next (from our plan)

- **Step B:** record audio locally (mic + system audio) instead of uploading.
- **Step C:** a bot that auto-joins Zoom/Meet/Teams.
- Nice-to-haves: speaker labels ("who said what"), save results to a database, email the summary.
