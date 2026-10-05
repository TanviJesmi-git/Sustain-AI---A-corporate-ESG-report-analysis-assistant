from embed_store import get_model, create_session_collection
from ingest import ingest_uploaded_pdf
from retrieve import retrieve

collection = create_session_collection()
embed_model = get_model()

with open("data/pdfs/wipro_2023_2024.pdf", "rb") as f:
    file_bytes = f.read()

ingest_uploaded_pdf(file_bytes, "wipro_2023_2024.pdf", "WIPRO", "2023-2024", collection, embed_model)

chunks = retrieve("Scope 1 emissions", collection, embed_model, n_results=30, where={"company": "WIPRO"})
for i, c in enumerate(chunks, 1):
    marker = " <== TARGET" if c["page_number"] == 43 and "6515" in c["content"] else ""
    print(f"{i}. Page {c['page_number']}{marker}")