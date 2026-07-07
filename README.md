# 🎙️ Meeting Reader

A self-built **"Read AI" clone**. Upload a meeting recording and get:

- 📝 a **transcript** with **speaker labels** ("who said what")
- 🧠 an **AI summary** — Summary, Key Points, Decisions, Action Items
- 📧 a **beautifully formatted email** with the transcript attached
- ⬇️ **download** buttons for the summary and transcript
- ♾️ **long meetings** handled via automatic audio **chunking**
- 🔑 **multiple Groq keys** with auto-rotation when one hits its limit

> 📋 For the full roadmap, architecture, and future plans, see **[PROJECT_PLAN.md](PROJECT_PLAN.md)**.

---

## How it works

```
Browser  ──audio + email──►  FastAPI
                              │
                              ├─ 1. Groq Whisper      → timed transcript
                              ├─ 2. Groq LLM (diarize)→ Speaker 1 / Speaker 2…
                              ├─ 3. Groq LLM (summary)→ markdown summary
                              └─ 4. Gmail SMTP        → email to user
```

**Stack:** Groq Whisper · LangChain + Groq LLM (`openai/gpt-oss-120b`) · FastAPI · Gmail SMTP

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Web app: upload → transcribe → diarize → summarize → email + downloads |
| `transcribe.py` | Audio → text (Groq Whisper); auto-chunks long files |
| `diarize.py` | Adds speaker labels using the LLM + pause gaps (Path A) |
| `summarize.py` | Transcript → summary via **LangChain** `ChatGroq` |
| `send_email.py` | Emails a styled summary + attaches the transcript (**Gmail SMTP**) |
| `groq_pool.py` | Pool of Groq keys, auto-rotates on rate limits |
| `chunk_audio.py` | Splits long audio into chunks (bundled ffmpeg) |
| `.env` | API keys + model config (**never commit this**) |
| `PROJECT_PLAN.md` | Full plan, architecture, roadmap |

---

## Setup (one time)

Open PowerShell in this folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If activation is blocked, run once then retry:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Configure `.env`

Copy `.env.example` → `.env` and fill in:

```ini
# one or more Groq keys, comma-separated -> auto-rotates when one hits its limit
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3   # https://console.groq.com/keys
WHISPER_MODEL=whisper-large-v3             # or whisper-large-v3-turbo (faster)
LLM_MODEL=openai/gpt-oss-120b
GMAIL_ADDRESS=you@gmail.com                # sender
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx     # Google "App password", NOT your login password
```

> 💡 **Rate limits:** add several free Groq keys to `GROQ_API_KEYS` (comma-separated).
> When one key hits its daily/rate limit, the app automatically switches to the next.

> **Gmail App Password:** enable 2-Step Verification → Google Account → Security →
> App passwords → generate one for "Mail".

---

## Run

```powershell
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**, upload a recording, enter an email, and click
**Transcribe, Summarize & Email**.

---

## Test the pieces individually

```powershell
python transcribe.py "uploads\test.wav"   # prints transcript
python diarize.py                          # built-in speaker-labeling demo
python summarize.py                        # built-in summary sample
python send_email.py you@example.com       # sends a test email
```

---

## Limits to know

- **Long meetings are handled** — files over ~20 MB are auto-split into 10-min chunks, transcribed, and stitched. (No manual ffmpeg install needed; it's bundled.)
- Speaker labels are **inferred by the LLM**, not true voice fingerprinting (good for meetings; upgradeable to `pyannote` later).
- Gmail free sending cap ≈ **500 emails/day**.
- Very long (multi-hour) transcripts may still stress the LLM's token limit — see `PROJECT_PLAN.md` §11 for the map-reduce fallback plan.

---

## Security

- All secrets live in `.env`, which is **git-ignored**.
- The keys used during setup were shared in chat — **rotate them** when done:
  Groq key at https://console.groq.com/keys, and regenerate the Gmail App Password.

---

## What's next

See **[PROJECT_PLAN.md](PROJECT_PLAN.md)**. Immediate next step: **chunking** so long
meetings (>25 min) work, then local recording (Approach B) and a meeting bot (Approach C).
