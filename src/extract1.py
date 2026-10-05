from pathlib import Path
from dataclasses import dataclass
import json
import re
import pdfplumber


@dataclass
class ExtractionResult:
    success: bool
    pages: list[dict]
    warning: str | None = None


def extract_pdf(
    pdf_path: Path,
    min_text_ratio: float = 0.5
) -> ExtractionResult:
    """
    Extracts text and tables from a PDF using pdfplumber.

    Each page is stored as:
    {
        "page_number": 1,
        "text": "...",
        "tables": [
            [...],
            [...]
        ]
    }
    """

    pages = []
    empty_page_count = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page_num, page in enumerate(pdf.pages, start=1):

                # -------------------------
                # Extract normal text
                # -------------------------
                text = page.extract_text() or ""

                if len(text.strip()) < 20:
                    empty_page_count += 1

                # -------------------------
                # Extract tables
                # -------------------------
                tables = page.extract_tables()

                # Remove completely empty tables
                cleaned_tables = []

                for table in tables:
                    cleaned_table = []

                    for row in table:
                        if row is None:
                            continue

                        cleaned_row = [
                            cell.strip() if isinstance(cell, str) else cell
                            for cell in row
                        ]

                        # Keep row if it contains at least one value
                        if any(
                            cell is not None and str(cell).strip() != ""
                            for cell in cleaned_row
                        ):
                            cleaned_table.append(cleaned_row)

                    if cleaned_table:
                        cleaned_tables.append(cleaned_table)

                pages.append({
                    "page_number": page_num,
                    "text": text,
                    "tables": cleaned_tables
                })

    except Exception as e:
        return ExtractionResult(
            success=False,
            pages=[],
            warning=f"Could not open '{pdf_path.name}': {e}"
        )

    # -------------------------
    # Validate extraction
    # -------------------------
    total_pages = len(pages)

    empty_ratio = (
        empty_page_count / total_pages
        if total_pages
        else 1.0
    )

    if empty_ratio > (1 - min_text_ratio):
        return ExtractionResult(
            success=False,
            pages=pages,
            warning=(
                f"'{pdf_path.name}' has little/no extractable text "
                f"({empty_page_count}/{total_pages} pages empty). "
                f"It may be image-only or scanned. "
                f"Consider using OCR for this PDF."
            )
        )

    return ExtractionResult(
        success=True,
        pages=pages
    )


def parse_filename_metadata(filename: str) -> dict:
    """
    Expects filenames such as:

        tcs_2023_24.pdf
        infosys_2024_25.pdf

    Returns:

        {
            "company": "TCS",
            "year": "2023-2024"
        }
    """

    stem = Path(filename).stem

    match = re.match(r"([a-zA-Z]+)_(\d{4})_(\d{2})", stem)

    if match:
        company = match.group(1).upper()

        start_year = int(match.group(2))
        end_year = start_year + 1

        year = f"{start_year}-{end_year}"

    else:
        company = "UNKNOWN"
        year = "UNKNOWN"

    return {
        "company": company,
        "year": year
    }

def process_pdf(
    pdf_path: Path,
    output_dir: Path
) -> ExtractionResult:

    print(f"📄 Processing: {pdf_path.name}")

    result = extract_pdf(pdf_path)

    if not result.success:
        print(f"⚠️  {result.warning}")

        # Still save extracted content if available
        if result.pages:
            print("   Saving partially extracted content...")

    metadata = parse_filename_metadata(pdf_path.name)

    # Add metadata to every page
    for page in result.pages:
        page.update(metadata)

    # Create output directory
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Output JSON path
    out_path = output_dir / f"{pdf_path.stem}.json"

    # Save JSON
    with open(
        out_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result.pages,
            f,
            indent=2,
            ensure_ascii=False
        )

    total_tables = sum(
        len(page["tables"])
        for page in result.pages
    )

    print(
        f"✅ {pdf_path.name}: "
        f"{len(result.pages)} pages extracted, "
        f"{total_tables} tables found → {out_path}"
    )

    return result


if __name__ == "__main__":

    pdf_dir = Path("data/pdfs")
    output_dir = Path("data/extracted")

    # Process every PDF in the input directory
    for pdf_file in pdf_dir.glob("*.pdf"):

        process_pdf(
            pdf_file,
            output_dir
        )