import pypdfium2 as pdfium
from pathlib import Path

PDF_PATH = Path("data/infosys_2024_25.pdf")
OUTPUT_DIR = Path("data/page_images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(PDF_PATH)
print(f"Total pages: {len(pdf)}")

for page_num in [1, 10, 30]:
    page = pdf[page_num - 1]

    # Try text extraction
    textpage = page.get_textpage()
    text = textpage.get_text_range()
    print(f"\n--- Page {page_num}: {len(text)} chars extracted ---")
    print(text[:200])

    # Render as image
    bitmap = page.render(scale=200/72)  # ~200 DPI
    pil_image = bitmap.to_pil()
    out_path = OUTPUT_DIR / f"pdfium_page_{page_num}.png"
    pil_image.save(out_path)
    print(f"Saved {out_path}")

pdf.close()