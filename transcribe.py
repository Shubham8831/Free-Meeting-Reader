# step 1
# turn audio file to text using openai whisper via groq
# uses a pool of Groq keys (auto-rotates on rate limits) and chunks long files.

import os
from groq import Groq
from dotenv import load_dotenv

from groq_pool import run_with_rotation
from chunk_audio import needs_chunking, with_chunks, CHUNK_SECONDS

load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3")


# send an audio file to whisper and get the plain-text transcript back
def transcribe(audio_path: str) -> str:
    def call(api_key: str):
        client = Groq(api_key=api_key)
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f.read()),
                model=WHISPER_MODEL,
                response_format="text",  # return the text only
            )
        # with response_format="text" the SDK returns the string directly
        return result if isinstance(result, str) else result.text

    return run_with_rotation(call)


# same, but returns timed segments -> [{"start":.., "end":.., "text":..}]
# the pauses between segments are the best clue for "who is speaking" (diarization)
def transcribe_segments(audio_path: str) -> list[dict]:
    def call(api_key: str):
        client = Groq(api_key=api_key)
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f.read()),
                model=WHISPER_MODEL,
                response_format="verbose_json",  # gives per-segment timestamps
            )
        segments = getattr(result, "segments", None) or []
        out = []
        for s in segments:
            # segments may be dicts or objects depending on SDK version
            get = (lambda k: getattr(s, k, None)) if not isinstance(s, dict) else s.get
            out.append({
                "start": round(float(get("start") or 0.0), 2),
                "end": round(float(get("end") or 0.0), 2),
                "text": (get("text") or "").strip(),
            })
        return out

    return run_with_rotation(call)


# chunk-aware transcription: small files go in one call; big files are split,
# transcribed piece by piece, and their timestamps stitched back together.
def transcribe_segments_auto(audio_path: str) -> list[dict]:
    if not needs_chunking(audio_path):
        return transcribe_segments(audio_path)

    def per_chunk(chunk_path: str, index: int) -> list[dict]:
        segs = transcribe_segments(chunk_path)
        offset = index * CHUNK_SECONDS  # shift times so chunk 2 continues after chunk 1
        for s in segs:
            s["start"] += offset
            s["end"] += offset
        return segs

    all_segments: list[dict] = []
    for chunk_segments in with_chunks(audio_path, per_chunk):
        all_segments.extend(chunk_segments)
    return all_segments


if __name__ == "__main__":
    # manual test:  python transcribe.py path\to\audio.mp3
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        raise SystemExit(1)
    print(transcribe(sys.argv[1]))
