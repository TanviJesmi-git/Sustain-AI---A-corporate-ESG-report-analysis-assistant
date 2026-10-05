from retrieve import retrieve
from answer import format_evidence, SYSTEM_PROMPT
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL_NAME = "gemini-3.5-flash-lite"

# Simple known-company list — since your corpus is fixed at 2 companies,
# a hardcoded list is more reliable here than trying to auto-detect names
KNOWN_COMPANIES = ["TCS", "WIPRO"]


def detect_companies(query: str) -> list[str]:
    """Finds which known companies are mentioned in the question (case-insensitive)."""
    query_upper = query.upper()
    return [c for c in KNOWN_COMPANIES if c in query_upper]


def retrieve_for_comparison(query: str, companies: list[str], n_per_company: int = 6) -> list[dict]:
    """
    Runs one filtered retrieval per company and merges the results,
    so no company's evidence can be crowded out by the other's.
    """
    all_chunks = []
    for company in companies:
        company_chunks = retrieve(query, n_results=n_per_company, where={"company": company})
        all_chunks.extend(company_chunks)
    return all_chunks


def answer_comparison_question(query: str, n_per_company: int = 6) -> str:
    companies = detect_companies(query)

    if len(companies) < 2:
        return (
            f"This looks like a comparison question, but I could only detect "
            f"{companies} in it. Please mention at least two companies by name "
            f"(TCS, Wipro) so I can retrieve evidence for each separately."
        )

    chunks = retrieve_for_comparison(query, companies, n_per_company)

    if not chunks:
        return "No relevant evidence was found for this question."

    evidence = format_evidence(chunks)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"This is a COMPARISON question involving multiple companies: {', '.join(companies)}. "
        f"Make sure your answer addresses EVERY company listed, using only their respective evidence below. "
        f"If evidence for one company is missing a specific figure, say so explicitly rather than omitting that company.\n\n"
        f"EVIDENCE:\n{evidence}\n\n"
        f"QUESTION: {query}\n\nANSWER:"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text


if __name__ == "__main__":
    query = "How does TCS's water consumption compare to Wipro's?"
    print(f"Q: {query}\n")
    print(answer_comparison_question(query))