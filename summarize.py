# step 2
# convert the transcript into a meeting summary
# done via gpt oss via groq cloud


import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# low temperature to keep it factual not cretive
llm = ChatGroq(model=LLM_MODEL, temperature=0.2)

#instruction
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

# chain:  prompt -> LLM -> plain string
chain = prompt | llm | StrOutputParser()


def summarize(transcript: str) -> str:
    """Return a Markdown summary of the given transcript."""
    return chain.invoke({"transcript": transcript})


if __name__ == "__main__":
    sample = "shubham: Let's ship on Friday. bablu: I'll finish the login page by Thursday."
    print(summarize(sample))
