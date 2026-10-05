from pathlib import Path
import json
import re



def table_to_markdown(table: list[list]) -> str:
    """Converts a pdfplumber-style table (list of rows) into a Markdown table string."""
    if not table:
        return ""

    def clean_cell(cell):
        if cell is None:
            return ""
        return str(cell).replace("\n", " ").strip()

    lines = []
    header = [clean_cell(c) for c in table[0]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    for row in table[1:]:
        row_cells = [clean_cell(c) for c in row]
        # pad short rows so the table stays well-formed
        while len(row_cells) < len(header):
            row_cells.append("")
        lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(lines)


TARGET_CHUNK_SIZE = 500  # was 900 — lowered since real chunks were coming out much larger than target


def split_into_paragraphs(text: str) -> list[str]:
    """
    Splits page text into line-based blocks. pdfplumber's output rarely has true
    blank-line paragraph breaks, so splitting on single newlines (and filtering
    empty lines) gives group_paragraphs() actual small units to work with,
    instead of receiving the whole page as one unsplittable block.
    """
    lines = text.split("\n")
    return [line.strip() for line in lines if line.strip()]

def group_paragraphs(paragraphs: list[str], target_size: int) -> list[str]:
    """Greedily merges paragraphs into chunks close to target_size characters."""
    chunks = []
    current = ""

    for para in paragraphs:
        if not current:
            current = para
        elif len(current) + len(para) + 1 <= target_size:
            current += "\n" + para
        else:
            chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


def build_header(company: str, year: str, page_number: int) -> str:
    return f"[{company} | FY {year} | Page {page_number}]"


def chunk_page(page: dict) -> list[dict]:
    """Turns one page record into a list of chunk dicts (text chunks + table chunks)."""
    company = page["company"]
    year = page["year"]
    page_number = page["page_number"]
    header = build_header(company, year, page_number)

    chunks = []

    # --- Text chunks ---
    paragraphs = split_into_paragraphs(page["text"])
    text_groups = group_paragraphs(paragraphs, TARGET_CHUNK_SIZE)

    for i, group in enumerate(text_groups):
        chunks.append({
            "chunk_type": "text",
            "company": company,
            "year": year,
            "page_number": page_number,
            "content": f"{header}\n{group}",
        })

    # --- Table chunks ---
    for i, table in enumerate(page.get("tables", [])):
        table_md = table_to_markdown(table)
        if not table_md.strip():
            continue
        chunks.append({
            "chunk_type": "table",
            "company": company,
            "year": year,
            "page_number": page_number,
            "content": f"{header} (Table {i + 1})\n{table_md}",
        })

    return chunks


def chunk_document(pages: list[dict]) -> list[dict]:
    all_chunks = []
    for page in pages:
        all_chunks.extend(chunk_page(page))

    # assign a stable, human-readable chunk_id after ordering is final
    for idx, chunk in enumerate(all_chunks):
        chunk["chunk_id"] = f"{chunk['company']}_{chunk['year']}_p{chunk['page_number']}_{idx}"

    return all_chunks


if __name__ == "__main__":
    input_dir = Path("data/extracted")
    output_dir = Path("data/chunks")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    for json_file in input_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            pages = json.load(f)

        doc_chunks = chunk_document(pages)
        all_chunks.extend(doc_chunks)

        text_count = sum(1 for c in doc_chunks if c["chunk_type"] == "text")
        table_count = sum(1 for c in doc_chunks if c["chunk_type"] == "table")
        print(f"✅ {json_file.name}: {text_count} text chunks, {table_count} table chunks")

    out_path = output_dir / "all_chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nTotal chunks: {len(all_chunks)} → {out_path}")