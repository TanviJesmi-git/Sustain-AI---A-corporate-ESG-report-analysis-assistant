import os

from dotenv import load_dotenv
from google import genai

from retrieve import retrieve

load_dotenv()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL_NAME = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """You are an ESG report analysis assistant. Answer the user's question \
using ONLY the evidence provided below, which is extracted from corporate sustainability reports.

Rules:
- Ground every claim in the evidence provided. Do not use outside knowledge.
- Every numeric value you state MUST include a citation in the format (Company, FY Year, Page N).
- If a company's evidence does not contain a metric in the SAME form/unit as another company's, \
do not just say "not found." Instead, explicitly state what each company DOES report, and name \
the specific reason a direct comparison isn't possible (e.g. different units, different scope of \
measurement, a target instead of a current figure, a breakdown instead of a total).
- If evidence is genuinely absent for a company (not just differently formatted), say so clearly.
- Clearly distinguish between a company's CURRENT reported value and a stated TARGET or GOAL for \
a future year. Look for words like "target," "aim," "by 2030," "baseline," or "goal" that signal \
a figure is aspirational, not current. Never present a target as if it were an already-achieved \
current figure.
- Be concise and direct.
"""
def format_evidence(chunks: list[dict]) -> str:
    blocks = []

    for c in chunks:
        blocks.append(
            f"--- Source: {c['company']}, FY {c['year']}, "
            f"Page {c['page_number']} ---\n{c['content']}"
        )

    return "\n\n".join(blocks)


def answer_question(
    query: str,
    n_results: int = 6,
    where: dict | None = None
) -> str:

    chunks = retrieve(
        query,
        n_results=n_results,
        where=where
    )

    if not chunks:
        return "No relevant evidence was found for this question."

    evidence = format_evidence(chunks)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"EVIDENCE:\n{evidence}\n\n"
        f"QUESTION: {query}\n\n"
        f"ANSWER:"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


if __name__ == "__main__":

    query = "What are TCS's Scope 1 and Scope 2 emissions for FY 2023-24?"

    print(f"Q: {query}\n")

    print(answer_question(query))