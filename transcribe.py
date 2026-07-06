# step 1 
# turn audio file to text using openai whisper via groq
# done via groq client

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3")


# this fn send audio file to whisper and take the plan text transcript back
def transcribe(audio_path: str) -> str:

    with open(audio_path, "rb") as f: # open the audio file

        result = client.audio.transcriptions.create(   
            file=(os.path.basename(audio_path), f.read()),
            model=WHISPER_MODEL,
            response_format="text",  # return the text only
        )

    # when response_format="text", the SDK returns the string directly.
    return result if isinstance(result, str) else result.text


# same transcription but returns timed segments -> [{"start":.., "end":.., "text":..}]
# the pauses between segments are the best clue for "who is speaking" (diarization)
def transcribe_segments(audio_path: str) -> list[dict]:
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model=WHISPER_MODEL,
            response_format="verbose_json",  # gives per-segment timestamps
        )

    segments = getattr(result, "segments", None) or []
    out = []
    for s in segments:
        # SDK segments behave like objects; fall back to dict access just in case
        get = (lambda k: getattr(s, k, None)) if not isinstance(s, dict) else s.get
        out.append({
            "start": round(float(get("start") or 0.0), 2),
            "end": round(float(get("end") or 0.0), 2),
            "text": (get("text") or "").strip(),
        })
    return out


if __name__ == "__main__":
    # manual test:  
    # python transcribe.py path\to\audio.mp3
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        raise SystemExit(1)
    print(transcribe(sys.argv[1]))
