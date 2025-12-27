import os
import re
import shutil
import logging

import fitz                          # PyMuPDF for PDF
import pandas as pd                 # for Excel
from docx import Document           # for .docx

import io
import tesserocr
from PIL import Image

from config import domain, download_folder

# OCR configuration
TESSDATA_PREFIX = r"C:\Program Files\Tesseract-OCR\tessdata"
LANG            = "eng"
ZOOM            = 2.0    # 2× resolution for higher OCR accuracy

# 1. Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("leadCategorizer")

# 2. Define folders
INPUT_FOLDER = download_folder
OUTPUT_BASE  = fr"files\{domain}\sorted"
SUBFOLDERS = {
    "500": os.path.join(OUTPUT_BASE, "500plus"),
    "300": os.path.join(OUTPUT_BASE, "301to500"),
    "100": os.path.join(OUTPUT_BASE, "101to300"),
    "50":  os.path.join(OUTPUT_BASE, "50to100"),
}

# 3. Create output directories
os.makedirs(INPUT_FOLDER, exist_ok=True)
for path in SUBFOLDERS.values():
    os.makedirs(path, exist_ok=True)

# 4. Compile regex for Indian mobile numbers
mobile_pattern = re.compile(r'(?<!\d)(?:\+91[\-\s]?|0)?[6-9]\d{9}(?!\d)')

# 5a. Extraction function with OCR fallback for PDF
def extract_text_from_pdf(path):
    doc = fitz.open(path)
    mat = fitz.Matrix(ZOOM, ZOOM)
    full_text = []

    with tesserocr.PyTessBaseAPI(path=TESSDATA_PREFIX, lang=LANG) as ocr_api:
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            text = page.get_text("text") or ""
            if text.strip():
                full_text.append(text)
            else:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_bytes)).convert("L")
                ocr_api.SetImage(pil_img)
                ocr_text = ocr_api.GetUTF8Text().strip()
                full_text.append(ocr_text)

    doc.close()
    return "\n".join(full_text)

# 5b. Extraction for Excel
def extract_text_from_xlsx(path):
    chunks = []
    sheets = pd.read_excel(path, sheet_name=None, dtype=str)
    for df in sheets.values():
        vals = df.fillna("").astype(str).values.flatten()
        chunks.extend(vals.tolist())
    return " ".join(chunks)

# 5c. Extraction for Word (.docx)
def extract_text_from_docx(path):
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)

# 6. Process every file under INPUT_FOLDER (including subfolders)
all_paths = []
for root, _, files in os.walk(INPUT_FOLDER):
    for name in files:
        all_paths.append(os.path.join(root, name))

total = len(all_paths)

for idx, src in enumerate(all_paths, start=1):
    fname = os.path.basename(src)
    ext   = os.path.splitext(fname)[1].lower()

    # skip any oddball files
    if ext not in (".pdf", ".docx", ".xlsx", ".xls"):
        logger.debug(f"[{idx}/{total}] skipping unsupported: {fname}")
        continue

    try:
        # dispatch to the right extractor
        if ext == ".pdf":
            content = extract_text_from_pdf(src)
        elif ext in (".xlsx", ".xls"):
            content = extract_text_from_xlsx(src)
        else:  # .docx
            content = extract_text_from_docx(src)

        leads = re.findall(mobile_pattern, content)
        count = len(leads)
        msg   = f"[{idx}/{total}] {fname}: {count} leads"

        if count < 50:
            os.remove(src)
            logger.info(msg + " – deleted (<50 leads).")
            continue

        if   count > 500: dest_key = "500"
        elif count > 300: dest_key = "300"
        elif count > 100: dest_key = "100"
        else:              dest_key = "50"

        dest_folder = SUBFOLDERS[dest_key]
        shutil.move(src, os.path.join(dest_folder, fname))
        logger.info(msg + f" – moved to {os.path.basename(dest_folder)}.")

    except Exception as e:
        logger.error(f"[{idx}/{total}] Error processing {fname}: {e}")