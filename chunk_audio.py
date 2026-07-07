# split long audio into smaller chunks so each fits under Groq's ~25 MB limit.
# uses a bundled ffmpeg binary (imageio-ffmpeg) so nothing needs to be installed manually.

import os
import glob
import shutil
import tempfile
import subprocess

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

CHUNK_SECONDS = 600          # 10-minute chunks
MAX_SINGLE_MB = 20           # files under this are transcribed in one shot


def needs_chunking(path: str) -> bool:
    return os.path.getsize(path) > MAX_SINGLE_MB * 1024 * 1024


def split_audio(path: str, out_dir: str, chunk_seconds: int = CHUNK_SECONDS) -> list[str]:
    """Split `path` into mono 16 kHz mp3 chunks in out_dir. Returns chunk paths in order.

    Downsampling to mono/16 kHz keeps each chunk small while staying good enough
    for speech recognition.
    """
    pattern = os.path.join(out_dir, "chunk_%03d.mp3")
    cmd = [
        FFMPEG, "-y", "-i", path,
        "-ac", "1", "-ar", "16000",          # mono, 16 kHz
        "-f", "segment", "-segment_time", str(chunk_seconds),
        pattern,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return sorted(glob.glob(os.path.join(out_dir, "chunk_*.mp3")))


def with_chunks(path: str, per_chunk):
    """Split audio, call per_chunk(chunk_path, index) for each, clean up temp files.

    Returns the list of per_chunk return values.
    """
    tmp_dir = tempfile.mkdtemp(prefix="mr_chunks_")
    try:
        chunks = split_audio(path, tmp_dir)
        return [per_chunk(chunk, i) for i, chunk in enumerate(chunks)]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
