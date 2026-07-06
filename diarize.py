# step 1.5  (accuracy booster)
# add speaker labels ("who said what") to the transcript.
# path A: no heavy diarization model -> we let the Groq LLM infer speakers,
# helped by the PAUSE GAPS between whisper segments (the strongest turn-change signal).

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# temperature=0 -> most consistent / deterministic labeling
# max_tokens high so long transcripts aren't truncated to empty
llm = ChatGroq(model=LLM_MODEL, temperature=0, max_tokens=16000)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert meeting transcript diarizer. You are given a transcript "
            "split into timed segments. A '(gap Xs)' marker shows the silence before a "
            "segment; a longer gap usually means a NEW speaker started talking.\n\n"
            "Your job: label who is speaking and output a clean, readable transcript.\n"
            "STRICT RULES:\n"
            "1. Keep every word EXACTLY as given. Do NOT paraphrase, translate, add, or drop words.\n"
            "2. Figure out how many distinct speakers there are from context, gaps, and "
            "conversational turns (questions -> answers, greetings, 'I/you' shifts).\n"
            "3. Label them 'Speaker 1', 'Speaker 2', etc. Be CONSISTENT: the same person "
            "must always get the same label. If a real name is clearly stated, you may use it.\n"
            "4. Merge consecutive segments from the same speaker into one paragraph.\n"
            "5. Output ONLY the labeled transcript, formatted as:\n"
            "Speaker 1: ...\nSpeaker 2: ...\n"
            "Do not add any commentary, headings, or explanation.",
        ),
        ("human", "Timed transcript:\n\n{segments}"),
    ]
)

chain = prompt | llm | StrOutputParser()


def _mmss(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


# format segments into text the LLM can reason over, exposing the pause gaps
def _format_segments(segments: list[dict]) -> str:
    lines = []
    prev_end = None
    for seg in segments:
        gap = 0.0 if prev_end is None else max(0.0, seg["start"] - prev_end)
        lines.append(f"[{_mmss(seg['start'])}] (gap {gap:.1f}s) {seg['text']}")
        prev_end = seg["end"]
    return "\n".join(lines)


def diarize(segments: list[dict]) -> str:
    """Return a speaker-labeled transcript.

    Always returns non-empty text when segments exist: if the LLM errors or
    returns a blank answer (can happen on long inputs), fall back to the plain
    joined transcript so the summary never sees empty content.
    """
    if not segments:
        return ""

    plain = " ".join(s["text"] for s in segments).strip()
    try:
        labeled = chain.invoke({"segments": _format_segments(segments)}).strip()
    except Exception:
        return plain
    return labeled if labeled else plain


if __name__ == "__main__":
    demo = [
        {"start": 0.0, "end": 2.0, "text": "Hey, are we still shipping on Friday?"},
        {"start": 3.5, "end": 6.0, "text": "Yes, I'll finish the login page by Thursday."},
        {"start": 6.2, "end": 8.0, "text": "Great, then QA can start Friday morning."},
    ]
    print(diarize(demo))
