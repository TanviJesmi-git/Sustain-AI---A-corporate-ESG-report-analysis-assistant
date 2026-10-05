from retrieve import retrieve
from answer import SYSTEM_PROMPT, format_evidence
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_NAME = "gemini-3.5-flash-lite"


def answer_query(query: str, known_companies: list[str], collection, embed_model,
                  recent_history: list[dict] | None = None) -> dict:
    """
    Core Q&A logic, shared by the Streamlit app and the evaluation script.
    recent_history: list of {"role": ..., "content": ...} dicts, most recent last.
    Returns {"answer": str, "chunks": list[dict], "mentioned": list[str]}.
    """
    recent_history = recent_history or []

    current_mentioned = [c for c in known_companies if c in query.upper()]
    is_short_followup = len(query.split()) <= 6

    if current_mentioned and not is_short_followup:
        retrieval_query = query
    else:
        recent_user_turns = [m["content"] for m in recent_history[-2:-1] if m["role"] == "user"]
        retrieval_query = query + " " + " ".join(recent_user_turns)

    if current_mentioned:
        mentioned = current_mentioned
    else:
        mentioned = [c for c in known_companies if c in retrieval_query.upper()]

    if len(mentioned) >= 2:
        n_per_company = 8 if len(mentioned) <= 2 else max(3, 16 // len(mentioned))
        chunks = []
        for company in mentioned:
            chunks.extend(retrieve(retrieval_query, collection, embed_model,
                                    n_results=n_per_company, where={"company": company}))
    elif len(mentioned) == 1:
        chunks = retrieve(retrieval_query, collection, embed_model,
                           n_results=20, where={"company": mentioned[0]})
    else:
        chunks = retrieve(retrieval_query, collection, embed_model, n_results=6)

    if not chunks:
        return {"answer": "No relevant evidence was found in the uploaded reports for this question.",
                "chunks": [], "mentioned": mentioned}

    evidence = format_evidence(chunks)
    history_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent_history[-2:-1])

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"CONVERSATION SO FAR (for context on follow-up questions only — "
        f"still ground all facts in EVIDENCE below):\n{history_text}\n\n"
        f"EVIDENCE:\n{evidence}\n\nQUESTION: {query}\n\nANSWER:"
    )
    response = client.models.generate_content(
        model=MODEL_NAME, contents=prompt, config={"temperature": 0.1}
    )
    return {"answer": response.text, "chunks": chunks, "mentioned": mentioned}