import io

import pdfplumber


def extractText(fileName, fileBytes):
    lowerName = fileName.lower()
    if lowerName.endswith(".pdf"):
        return extractPdf(fileBytes)
    if lowerName.endswith(".txt"):
        return extractTxt(fileBytes)
    raise ValueError("Only PDF and TXT files are supported")


def extractPdf(fileBytes):
    textParts = []
    with pdfplumber.open(io.BytesIO(fileBytes)) as pdf:
        for page in pdf.pages:
            pageText = page.extract_text() or ""
            if pageText.strip():
                textParts.append(pageText)
    text = "\n".join(textParts).strip()
    if not text:
        raise ValueError("Could not extract text from PDF")
    return text


def extractTxt(fileBytes):
    text = fileBytes.decode("utf-8", errors="ignore").strip()
    if not text:
        raise ValueError("Text file is empty")
    return text
