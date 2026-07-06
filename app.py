# Meeting Reader — Step A: upload audio -> transcript -> AI summary.
# Run:  uvicorn app:app --reload
# open http://127.0.0.1:8000 in your browser.


import os
import uuid
import html

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse

from transcribe import transcribe, transcribe_segments
from diarize import diarize
from summarize import summarize
from send_email import send_summary_email

app = FastAPI(title="Meeting Reader")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Meeting Reader</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 40px auto; padding: 0 16px; }}
    h1 {{ margin-bottom: 4px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 24px; margin-top: 20px; }}
    button {{ background: #4f46e5; color: #fff; border: 0; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 15px; }}
    pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f6f6f6; padding: 16px; border-radius: 8px; }}
    .muted {{ color: #666; }}
  </style>
</head>
<body>
  <h1>🎙️ Meeting Reader</h1>
  <p class="muted">Upload a meeting recording (.mp3, .m4a, .wav, .mp4). You get a transcript and an AI summary.</p>
  <div class="card">
    <form action="/process" method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept="audio/*,video/mp4" required>
      <p><input type="email" name="email" placeholder="Email the summary to..." required
                style="padding:8px;width:100%;box-sizing:border-box;border:1px solid #ccc;border-radius:8px;"></p>
      <p><button type="submit">Transcribe, Summarize &amp; Email</button></p>
      <p class="muted">Large files take longer. Groq's free tier limits audio to ~25 MB.</p>
    </form>
  </div>
  {result}
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE.format(result="")


@app.post("/process", response_class=HTMLResponse)
async def process(file: UploadFile = File(...), email: str = Form(...)):
    
    # save the uploaded file
    ext = os.path.splitext(file.filename)[1] or ".mp3"
    saved_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    try:
        # transcribe with timestamps, then label speakers (path A diarization)
        segments = transcribe_segments(saved_path)
        try:
            transcript = diarize(segments) if segments else transcribe(saved_path)
        except Exception:
            # if speaker-labeling fails, fall back to a plain transcript
            transcript = " ".join(s["text"] for s in segments) if segments else transcribe(saved_path)

        # last-resort safety net: never summarize an empty transcript
        if not transcript.strip():
            transcript = transcribe(saved_path)

        # summarize (LangChain + Groq LLM)
        summary = summarize(transcript)

        # email the summary to the user (step 3)
        email_note = ""
        try:
            send_summary_email(email, summary)
            email_note = f'<p style="color:green">✅ Summary emailed to {html.escape(email)}</p>'
        except Exception as mail_err:
            email_note = f'<p style="color:#b00">⚠️ Could not send email: {html.escape(str(mail_err))}</p>'
    except Exception as e:
        result = f'<div class="card"><h2>Error</h2><pre>{html.escape(str(e))}</pre></div>'
        return PAGE.format(result=result)
    finally:
        
        # clean up the audio file
        if os.path.exists(saved_path):
            os.remove(saved_path)

    result = f"""
    <div class="card">
      {email_note}
      <h2>Summary</h2>
      <pre>{html.escape(summary)}</pre>
    </div>
    <div class="card">
      <h2>Full Transcript</h2>
      <pre>{html.escape(transcript)}</pre>
    </div>
    """
    return PAGE.format(result=result)
