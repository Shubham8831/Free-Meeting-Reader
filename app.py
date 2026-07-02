# Meeting Reader — Step A: upload audio -> transcript -> AI summary.
# Run:  uvicorn app:app --reload
# open http://127.0.0.1:8000 in your browser.


import os
import uuid
import html

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse

from transcribe import transcribe
from summarize import summarize

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
      <p><button type="submit">Transcribe &amp; Summarize</button></p>
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
async def process(file: UploadFile = File(...)):
    
    # save the uploaded file
    ext = os.path.splitext(file.filename)[1] or ".mp3"
    saved_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    try:
        # transcribe (Whisper)
        transcript = transcribe(saved_path)

        # summarize (LangChain + Groq LLM)
        summary = summarize(transcript)
    except Exception as e:
        result = f'<div class="card"><h2>Error</h2><pre>{html.escape(str(e))}</pre></div>'
        return PAGE.format(result=result)
    finally:
        
        # clean up the audio file
        if os.path.exists(saved_path):
            os.remove(saved_path)

    result = f"""
    <div class="card">
      <h2>Summary</h2>
      <pre>{html.escape(summary)}</pre>
    </div>
    <div class="card">
      <h2>Full Transcript</h2>
      <pre>{html.escape(transcript)}</pre>
    </div>
    """
    return PAGE.format(result=result)
