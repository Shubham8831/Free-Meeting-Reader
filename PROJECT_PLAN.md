# 📋 Meeting Reader — Full Project Plan & Architecture

> A self-built "Read AI" clone: it takes meeting audio and produces a transcript,
> speaker labels, an AI summary, and emails it out.
> This document is the **master reference** for all future development.

Last updated: 2026-07-06

---

## 1. Vision

Build, from scratch, a meeting-intelligence tool like [Read.ai](https://read.ai):

> **Audio in → transcript + "who said what" + AI summary (key points, decisions, action items) → delivered to the user.**

We grow it in three input stages (A → B → C), reusing the same AI "core" each time.

---

## 2. The three input approaches (how audio gets in)

All three feed the **same core** (transcribe → diarize → summarize → deliver).
Only the *audio input path* changes.

| Approach | How audio arrives | Difficulty | Status |
|----------|-------------------|------------|--------|
| **A. Upload & summarize** | User uploads a recording file | 🟢 Easy | ✅ **DONE** |
| **B. Record locally** | An app records mic + system audio during a call | 🟡 Medium | ⬜ Planned |
| **C. Bot joins the meeting** | A bot auto-joins Zoom/Meet/Teams | 🔴 Hard | ⬜ Planned |

**Golden rule:** never rebuild the core. A, B, and C are the same product with different front doors.

---

## 3. Current architecture (Approach A — implemented)

```
                          ┌───────────────────────────────────────────────┐
  ┌──────────┐  upload    │                 FastAPI (app.py)              │
  │  Browser │  audio +   │                                               │
  │  (form)  │──email────►│  1. save file to uploads/                     │
  │          │            │  2. transcribe_segments()  ── Groq Whisper ──►│  timed segments
  │          │            │  3. diarize()              ── Groq LLM ───────►│  Speaker 1/2 labels
  │          │◄───────────│  4. summarize()            ── Groq LLM ───────►│  summary markdown
  │  results │  HTML page │  5. send_summary_email()   ── Gmail SMTP ─────►│  email to user
  └──────────┘            │  6. delete audio file                         │
                          └───────────────────────────────────────────────┘
```

### Data flow (step by step)
1. **Upload** — user submits an audio/video file + their email via the web form.
2. **Transcribe** — `transcribe_segments()` calls Groq Whisper with `verbose_json`,
   returning timed segments `[{start, end, text}]`.
3. **Diarize (Path A)** — `diarize()` sends segments (with pause gaps) to the Groq LLM,
   which labels `Speaker 1 / Speaker 2…`. Falls back to plain text if it returns empty.
4. **Summarize** — `summarize()` turns the labeled transcript into markdown
   (Summary / Key Points / Decisions / Action Items).
5. **Email** — `send_summary_email()` sends the summary via Gmail SMTP.
6. **Cleanup** — the uploaded audio file is deleted; results shown in the browser.

---

## 4. File map

| File | Responsibility | Key functions |
|------|----------------|---------------|
| `app.py` | FastAPI web app: upload UI, orchestrates the pipeline, download links | `home()`, `process()`, `_download_link()` |
| `transcribe.py` | Audio → text via Groq Whisper (auto-chunks long files) | `transcribe()`, `transcribe_segments()`, `transcribe_segments_auto()` |
| `diarize.py` | Add speaker labels via Groq LLM (Path A) | `diarize()`, `_format_segments()` |
| `summarize.py` | Transcript → summary via LangChain `ChatGroq` | `summarize()` |
| `send_email.py` | Email a styled summary + transcript attachment via Gmail SMTP | `send_summary_email()` |
| `groq_pool.py` | Pool of Groq keys with auto-rotation on rate limits | `get_keys()`, `run_with_rotation()` |
| `chunk_audio.py` | Split long audio into chunks (bundled ffmpeg) | `needs_chunking()`, `split_audio()`, `with_chunks()` |
| `.env` | Secrets + model config (git-ignored) | — |
| `requirements.txt` | Python dependencies | — |
| `uploads/` | Temporary audio storage (cleared after each run) | — |

---

## 5. Tech stack & why

| Layer | Choice | Why |
|-------|--------|-----|
| Transcription | **Groq Whisper** (`whisper-large-v3`) | Cheap, fast, accurate; OpenAI-compatible |
| AI / summary / diarization | **Groq LLM** `openai/gpt-oss-120b` via **LangChain** | Fast, capable; LangChain keeps chains clean |
| Web framework | **FastAPI + Uvicorn** | Simple, async, easy file uploads |
| Email | **Gmail SMTP** (`smtplib`) | Free, sends to anyone, no extra package |
| Config | **python-dotenv** | Keep secrets out of code |

> Note: LangChain has no wrapper for Groq's *audio* endpoint, so transcription uses the
> raw `groq` client. All **LLM** work (diarize, summarize) is pure LangChain.

---

## 6. Environment variables (`.env`)

| Variable | Purpose | Example |
|----------|---------|---------|
| `GROQ_API_KEYS` | One or more Groq keys, comma-separated (auto-rotates on limits) | `gsk_a,gsk_b,gsk_c` |
| `GROQ_API_KEY` | Single-key fallback (still supported) | `gsk_...` |
| `WHISPER_MODEL` | Whisper model | `whisper-large-v3` (or `-turbo` for speed) |
| `LLM_MODEL` | Summary/diarize model | `openai/gpt-oss-120b` |
| `GMAIL_ADDRESS` | Sender Gmail/Workspace address | `you@domain.com` |
| `GMAIL_APP_PASSWORD` | Google **App Password** (not your login password) | `xxxx xxxx xxxx xxxx` |

⚠️ **Rotate all keys** once development is done — they were shared in chat during setup.

---

## 7. Roadmap (tiers)

### ✅ Tier 0 — Core (DONE)
- [x] Upload audio → transcript → summary (Approach A)
- [x] Email summary via Gmail SMTP
- [x] Speaker labels via LLM (Path A diarization)
- [x] Robustness: empty-output guards + fallbacks

### 🥇 Tier 1 — Polish the current app
- [x] **Chunking for long meetings** — auto-splits big files into 10-min chunks, transcribes each, stitches timestamps. (`chunk_audio.py`)
- [x] **Multi-key rotation** — several Groq keys in `.env`, auto-rotate on rate limits. (`groq_pool.py`)
- [x] **Include transcript in the email** — attached as `transcript.txt`.
- [x] **Download summary/transcript** — download buttons on the results page.
- [x] **Beautiful email** — styled HTML template (markdown-rendered).
- [ ] **Progress + logging** — show status ("Transcribing… Summarizing…") and log transcript length while developing. *(NEXT)*
- [ ] **File-size / type pre-check** — warn before uploading something too big.
- [ ] **Download as PDF** (currently `.md` / `.txt`).

### 🥈 Tier 2 — New input method (Approach B: local recording)
- [ ] Capture mic + system audio (browser `MediaRecorder` or a small Electron/desktop app).
- [ ] Send the recording (or live chunks) to the existing core.
- [ ] Optional: near-live transcription by streaming chunks.

### 🥉 Tier 3 — The full product (Approach C: meeting bot)
- [ ] Bot joins Zoom/Meet/Teams. Options:
  - **Recall.ai** (paid, reliable) — fastest path.
  - **Vexa** / **MeetingBot** (open-source, self-host) — free but more setup.
  - **Puppeteer/Playwright** DIY Google Meet bot — free, fragile.
- [ ] Stream live audio/transcript from the bot into the core.
- [ ] Live in-meeting transcription + post-meeting summary.

### 🌟 Tier 4 — Product features (later)
- [ ] **Database** (Supabase/Postgres) — meeting history, search past summaries.
- [ ] **User accounts / auth**.
- [ ] **True diarization (Path B)** with `pyannote.audio` for best "who said what".
- [ ] **Analytics** — talk-time per speaker, sentiment, engagement (like real Read AI).
- [ ] **Integrations** — Slack/Notion/calendar; auto-send summaries.
- [ ] **Multi-language** support.
- [ ] **Deploy** to Render/Railway/Fly.io.

---

## 8. Target architecture (where we're heading — Tiers 2–4)

```
   INPUTS                        CORE ENGINE                       OUTPUTS
 ┌──────────────┐          ┌──────────────────────┐          ┌────────────────┐
 │ A. Upload    │          │  Transcribe (Whisper)│          │  Web dashboard │
 │ B. Local rec │───audio─►│  Diarize (LLM/pyannote)──text──►│  Email         │
 │ C. Meeting   │          │  Summarize (LLM)     │          │  Download file │
 │    bot       │          │  Analytics           │          │  Slack/Notion  │
 └──────────────┘          └───────────┬──────────┘          └────────────────┘
                                        │
                                  ┌─────▼─────┐
                                  │ Database  │  (history, search, accounts)
                                  └───────────┘
```

---

## 9. Known limitations (today)

| Limit | Detail | Fix (planned) |
|-------|--------|---------------|
| ~~File size~~ | ~~Groq rejects audio > ~25 MB~~ | ✅ Fixed — auto-chunking |
| ~~Rate limits~~ | ~~one key runs out~~ | ✅ Fixed — multi-key rotation |
| **Diarization accuracy** | LLM *infers* speakers; not true voice fingerprinting | pyannote (Tier 4) |
| **No persistence** | Results vanish after the page/email | Database (Tier 4) |
| **Email = summary only** | Labeled transcript not emailed yet | Tier 1 |
| **Single user, local** | Runs on `localhost`, no auth | Deploy + auth (Tier 4) |
| **Gmail cap** | ~500 emails/day free | Fine for now |

---

## 10. Testing guidance

- **First test any change on a short clip (1–3 min).** Don't debug on a 1-hour file.
- Use **MP3 / M4A**, not WAV (WAV hits the 25 MB limit in ~2–3 min).
- Realistic test size: **10–20 min MP3** (well under 25 MB).
- Generate a quick test WAV on Windows:
  ```powershell
  Add-Type -AssemblyName System.Speech
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SetOutputToWaveFile("uploads\test.wav")
  $s.Speak("This is a test meeting about shipping on Friday.")
  $s.Dispose()
  ```
- Test modules individually:
  ```powershell
  python transcribe.py "uploads\test.wav"   # prints transcript
  python diarize.py                          # runs built-in demo
  python summarize.py                        # runs built-in sample
  python send_email.py you@example.com       # sends a test email
  ```

---

## 11. Immediate next step

Most of Tier 1 is now done (chunking, multi-key rotation, downloads, beautiful email).
Remaining Tier 1 polish:
1. **Progress + logging** — surface "Transcribing… Diarizing… Summarizing…" to the user
   (e.g. via a status endpoint or streaming), and log transcript length while developing.
2. **File-size / type pre-check** — warn in the browser before uploading something huge.
3. **PDF download** — add a PDF export option alongside `.md` / `.txt`.

After that, move to **Tier 2 — Approach B (local recording)**: capture mic + system audio
in the browser (`MediaRecorder`) and POST it to the existing `/process` pipeline.

### Watch-outs for very long meetings (already chunked)
- Diarize/summary LLM calls have a token ceiling; a multi-hour transcript may still be large.
  If it ever fails, add **map-reduce summarization** (summarize each chunk, then summarize the
  summaries) via LangChain.
- Chunk boundaries can split a sentence; a small overlap between chunks would improve accuracy.



"done now lets move to next one, i want to add / fix the chunking part for longer meetings and also ( i want to add many groq cloud keys in env and use them in loop (if limit reaches) and then option to download the summary and transcript and make the mail more beautiful"