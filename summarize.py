# step 2
# convert the transcript into a meeting summary
# done via gpt-oss via groq cloud (with automatic key rotation)

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from groq_pool import run_with_rotation

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# instruction
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a meeting assistant. You are given the raw transcript of a "
            "meeting. Produce a clear, well-structured summary in Markdown with "
            "these sections, and nothing else:\n"
            "## Summary\nA short paragraph.\n"
            "## Key Points\nBullet list of the main points discussed.\n"
            "## Decisions\nBullet list of decisions made (write 'None' if none).\n"
            "## Action Items\nBullet list as '- [Owner] task' (write 'None' if none).",
        ),
        ("human", "Meeting transcript:\n\n{transcript}"),
    ]
)


def summarize(transcript: str) -> str:
    """Return a Markdown summary of the given transcript."""
    def call(api_key: str):
        # low temperature to keep it factual, not creative
        llm = ChatGroq(model=LLM_MODEL, temperature=0.2, api_key=api_key)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"transcript": transcript})

    return run_with_rotation(call)


if __name__ == "__main__":
    sample = "shubham: Let's ship on Friday. bablu: I'll finish the login page by Thursday."
    print(summarize(sample))
