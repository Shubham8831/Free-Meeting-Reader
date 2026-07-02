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


if __name__ == "__main__":
    # manual test:  
    # python transcribe.py path\to\audio.mp3
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        raise SystemExit(1)
    print(transcribe(sys.argv[1]))
