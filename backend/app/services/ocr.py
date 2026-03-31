import re
from pathlib import Path

try:
    import pdfplumber

    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    pdfplumber = None
    _PDFPLUMBER_AVAILABLE = False

try:
    from pypdf import PdfReader

    _PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    _PYPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image, ImageOps

    _TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    ImageOps = None
    _TESSERACT_AVAILABLE = False


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# Keep both real unicode and common mojibake variants from OCR/PDF extraction.
_MATH_CHAR_REPLACEMENTS = {
    "\u2212": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2011": "-",
    "\u00d7": "*",
    "\u00f7": "/",
    "\u00b7": "*",
    "\u2219": "*",
    "\u2217": "*",
    "\u2215": "/",
    "\u2236": ":",
    "\u2211": "Sigma",
    "\u220f": "Pi",
    "\u221a": "sqrt",
    "\u2248": "~=",
    "\u2260": "!=",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u03c0": "pi",
    "âˆ’": "-",
    "â€“": "-",
    "â€”": "-",
    "â€‘": "-",
    "Ã—": "*",
    "Ã·": "/",
    "Â·": "*",
    "âˆ™": "*",
    "âˆ—": "*",
    "âˆ•": "/",
    "âˆ¶": ":",
    "âˆ‘": "Sigma",
    "âˆ": "Pi",
    "âˆš": "sqrt",
    "â‰ˆ": "~=",
    "â‰ ": "!=",
    "â‰¤": "<=",
    "â‰¥": ">=",
    "Ï€": "pi",
}
_SUPERSCRIPT_REPLACEMENTS = {
    "\u2070": "^0",
    "\u00b9": "^1",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u2074": "^4",
    "\u2075": "^5",
    "\u2076": "^6",
    "\u2077": "^7",
    "\u2078": "^8",
    "\u2079": "^9",
    "\u207a": "^+",
    "\u207b": "^-",
    "\u207f": "^n",
    "â°": "^0",
    "Â¹": "^1",
    "Â²": "^2",
    "Â³": "^3",
    "â´": "^4",
    "âµ": "^5",
    "â¶": "^6",
    "â·": "^7",
    "â¸": "^8",
    "â¹": "^9",
    "âº": "^+",
    "â»": "^-",
}
_SUBSCRIPT_REPLACEMENTS = {
    "\u2080": "_0",
    "\u2081": "_1",
    "\u2082": "_2",
    "\u2083": "_3",
    "\u2084": "_4",
    "\u2085": "_5",
    "\u2086": "_6",
    "\u2087": "_7",
    "\u2088": "_8",
    "\u2089": "_9",
    "â‚€": "_0",
    "â‚": "_1",
    "â‚‚": "_2",
    "â‚ƒ": "_3",
    "â‚„": "_4",
    "â‚…": "_5",
    "â‚†": "_6",
    "â‚‡": "_7",
    "â‚ˆ": "_8",
    "â‚‰": "_9",
}
_MATH_TOKEN_PATTERN = re.compile(
    r"(?:\d+\s*[-+*/=^]\s*\d+|sqrt|pi|<=|>=|!=|~=\s*\d+|[a-zA-Z]\^\d)",
    re.IGNORECASE,
)


def _normalize_math_notation(text: str) -> str:
    if not text:
        return ""

    out = text
    for src, dst in _MATH_CHAR_REPLACEMENTS.items():
        out = out.replace(src, dst)
    for src, dst in _SUPERSCRIPT_REPLACEMENTS.items():
        out = out.replace(src, dst)
    for src, dst in _SUBSCRIPT_REPLACEMENTS.items():
        out = out.replace(src, dst)

    # OCR post-fixes around equations.
    out = re.sub(r"(?<=\d)\s*[xX]\s*(?=\d)", " * ", out)
    out = re.sub(r"(?<=\d)\s*[/]\s*(?=\d)", " / ", out)
    out = re.sub(r"(?<=\d)\s*-\s*(?=\d)", " - ", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _resampling_lanczos() -> int:
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def _prepare_image_for_ocr(img: "Image.Image") -> list["Image.Image"]:
    gray = ImageOps.grayscale(img)
    enhanced = ImageOps.autocontrast(gray)

    # Upscale small scans to improve symbol recognition (fractions, superscripts, etc.).
    if enhanced.width < 1600:
        ratio = 1600 / max(enhanced.width, 1)
        enhanced = enhanced.resize(
            (int(enhanced.width * ratio), int(enhanced.height * ratio)),
            _resampling_lanczos(),
        )

    # Two variants: grayscale+autocontrast and binarized.
    binary = enhanced.point(lambda x: 255 if x > 165 else 0)
    return [enhanced, binary]


def _score_ocr_candidate(text: str) -> int:
    cleaned = (text or "").strip()
    if not cleaned:
        return -1
    math_hits = len(_MATH_TOKEN_PATTERN.findall(cleaned))
    digit_hits = len(re.findall(r"\d", cleaned))
    return len(cleaned) + (math_hits * 12) + digit_hits


def _ocr_image_with_math(img: "Image.Image") -> str:
    prepared_variants = _prepare_image_for_ocr(img)
    attempts = [
        {"lang": "eng+fra+equ", "config": "--oem 3 --psm 6 -c preserve_interword_spaces=1"},
        {"lang": "eng+fra+equ", "config": "--oem 3 --psm 11 -c preserve_interword_spaces=1"},
        {"lang": "eng+fra", "config": "--oem 3 --psm 6 -c preserve_interword_spaces=1"},
        {"lang": "eng", "config": "--oem 3 --psm 6 -c preserve_interword_spaces=1"},
    ]

    candidates: list[str] = []
    for prepared in prepared_variants:
        for attempt in attempts:
            try:
                text = pytesseract.image_to_string(
                    prepared,
                    lang=attempt["lang"],
                    config=attempt["config"],
                )
            except Exception:
                continue
            if text and text.strip():
                candidates.append(text)

    if candidates:
        return max(candidates, key=_score_ocr_candidate)

    # Last fallback with default config.
    return pytesseract.image_to_string(img)


def _extract_pdf_with_pdfplumber(path: Path) -> list[str]:
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                text_parts.append(text)
            elif _TESSERACT_AVAILABLE:
                img = page.to_image(resolution=350).original
                if isinstance(img, Image.Image):
                    pil_img = img
                else:
                    pil_img = Image.fromarray(img)
                text_parts.append(_ocr_image_with_math(pil_img))
    return text_parts


def _extract_pdf_with_pypdf(path: Path) -> list[str]:
    text_parts: list[str] = []
    reader = PdfReader(str(path))
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            text_parts.append(text)
    return text_parts


def _extract_image_text(path: Path) -> str:
    if not _TESSERACT_AVAILABLE:
        raise RuntimeError(
            "OCR image non disponible. Installez: pip install pytesseract Pillow"
        )
    img = Image.open(path)
    return _ocr_image_with_math(img)


def extract_text(file_path: str) -> str:
    """Simple OCR/extraction pipeline: try text layer first, fallback to image OCR."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(file_path)

    suffix = path.suffix.lower()

    if suffix in _IMAGE_EXTENSIONS:
        return _normalize_math_notation(_extract_image_text(path))

    text_parts: list[str] = []
    if _PDFPLUMBER_AVAILABLE:
        text_parts = _extract_pdf_with_pdfplumber(path)
    elif _PYPDF_AVAILABLE:
        text_parts = _extract_pdf_with_pypdf(path)
    else:
        raise RuntimeError(
            "Extraction PDF indisponible. Installez: pip install pdfplumber ou pip install pypdf"
        )

    extracted = "\n\n".join(part for part in text_parts if part and part.strip()).strip()
    if extracted:
        return _normalize_math_notation(extracted)

    raise RuntimeError("Aucun texte extractible detecte dans ce fichier.")
