import pypdfium2 as pdfium
from pathlib import Path

PDF_PATH = Path("data\\infosys_2024_25.pdf")
OUTPUT_DIR = Path("data/page_images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(PDF_PATH)
print(f"Total pages: {len(pdf)}")

page = pdf[0]
text = page.get_textpage().get_text_range()
print(f"Text extracted: {text[:200]}")

bitmap = page.render(scale=200/72)
pil_image = bitmap.to_pil()
pil_image.save(OUTPUT_DIR / "test_dummy_page1.png")
print("Saved test_dummy_page1.png")