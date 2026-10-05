from pathlib import Path
from extract1 import extract_pdf
from chunking import chunk_document
from embed_store import add_chunks

UPLOAD_DIR = Path("data/uploaded_pdfs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def ingest_uploaded_pdf(file_bytes: bytes, filename: str, company: str, year: str, collection, model) -> dict:
    company = company.strip().upper()
    year = year.strip()

    save_path = UPLOAD_DIR / filename
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    result = extract_pdf(save_path)
    if not result.success:
        return {"success": False, "message": result.warning}

    for page in result.pages:
        page["company"] = company
        page["year"] = year

    chunks = chunk_document(result.pages)
    num_added = add_chunks(chunks, collection, model)

    return {
        "success": True,
        "message": f"Added {company} ({year}): {len(result.pages)} pages, {num_added} chunks.",
    }