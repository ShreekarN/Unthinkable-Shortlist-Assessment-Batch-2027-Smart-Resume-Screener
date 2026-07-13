import io
import re

import fitz
import pdfplumber

# PDF path: run PyMuPDF and pdfplumber, normalize both, pick by textQualityScore.
# Normalization targets common resume PDF artifacts before LLM + UI highlighting.

LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
}

MOJIBAKE = {
    "â€™": "'",
    "â€˜": "'",
    "â€œ": '"',
    "â€": '"',
    "â€“": "-",
    "â€”": "-",
    "Â": "",
}


def extractText(fileName, fileBytes):
    # Route file parsing by extension so upload API stays simple.
    lowerName = fileName.lower()
    if lowerName.endswith(".pdf"):
        return extractPdf(fileBytes)
    if lowerName.endswith(".txt"):
        return extractTxt(fileBytes)
    raise ValueError("Only PDF and TXT files are supported")


def normalizeText(text):
    # Clean common PDF text issues before LLM extraction and UI highlighting.
    for src, dst in LIGATURES.items():
        text = text.replace(src, dst)
    for src, dst in MOJIBAKE.items():
        text = text.replace(src, dst)

    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00a0", " ")
        .replace("\u2022", " ")
    )

    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"([a-zA-Z0-9._%+-])\s*\n\s*(@|\.)", r"\1\2", text)
    text = re.sub(r"linkedin\s*\n\s*\.com", "linkedin.com", text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extractPdfPymupdf(fileBytes):
    doc = fitz.open(stream=fileBytes, filetype="pdf")
    parts = []
    for page in doc:
        pageText = page.get_text("text") or ""
        if pageText.strip():
            parts.append(pageText)
    doc.close()
    return normalizeText("\n".join(parts))


def extractPdfPlumber(fileBytes):
    parts = []
    with pdfplumber.open(io.BytesIO(fileBytes)) as pdf:
        for page in pdf.pages:
            pageText = page.extract_text() or ""
            if pageText.strip():
                parts.append(pageText)
    return normalizeText("\n".join(parts))


def textQualityScore(text):
    # Prefer outputs with readable contact info and fewer broken header patterns.
    score = len(text)
    if "@" in text and ".com" in text.lower():
        score += 200
    if re.search(r"[A-Z]{1,2}\n[A-Z]{3,}", text):
        score -= 150
    return score


def extractPdf(fileBytes):
    # Always extract with both engines, then keep the higher-quality normalized text.
    pymupdfText = extractPdfPymupdf(fileBytes)
    plumberText = extractPdfPlumber(fileBytes)

    if not pymupdfText and not plumberText:
        raise ValueError("Could not extract text from PDF")

    if not pymupdfText:
        return plumberText
    if not plumberText:
        return pymupdfText

    if textQualityScore(pymupdfText) >= textQualityScore(plumberText):
        return pymupdfText
    return plumberText


def extractTxt(fileBytes):
    text = normalizeText(fileBytes.decode("utf-8", errors="ignore"))
    if not text:
        raise ValueError("Text file is empty")
    return text
