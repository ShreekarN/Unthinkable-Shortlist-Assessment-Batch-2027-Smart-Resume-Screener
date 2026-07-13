import re
import unicodedata
from pathlib import Path

import fitz
import pdfplumber

pdfDir = Path(__file__).resolve().parent.parent.parent
pdfNames = ["N.pdf", "O.pdf", "P.pdf", "Q.pdf", "mynewcv (1).pdf"]

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


def normalizeText(text):
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


def extractPdfplumber(fileBytes):
    import io

    parts = []
    with pdfplumber.open(io.BytesIO(fileBytes)) as pdf:
        for page in pdf.pages:
            pageText = page.extract_text() or ""
            if pageText.strip():
                parts.append(pageText)
    return "\n".join(parts).strip()


def extractPymupdf(fileBytes):
    doc = fitz.open(stream=fileBytes, filetype="pdf")
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    doc.close()
    return "\n".join(parts).strip()


def scoreText(text, nameHints):
    lower = text.lower()
    score = 0
    notes = []
    if len(text) > 500:
        score += 2
    else:
        notes.append("short")

    if "@" in text and ".com" in lower:
        score += 2
    else:
        notes.append("email-weak")

    if "linkedin" in lower:
        score += 1

    for hint in nameHints:
        if hint in lower.replace(" ", ""):
            score += 2
            break
    else:
        notes.append("name-weak")

    if re.search(r"[A-Z]{1,2}\n[A-Z]{3,}", text):
        notes.append("split-name")

    if text.count("") > 0:
        notes.append("replacement-char")

    weird = len(re.findall(r"[^\x00-\x7F]", text))
    if weird > 40:
        notes.append(f"nonAscii={weird}")

    return score, notes


def main():
    hints = {
        "N.pdf": ["mamidi", "satwik"],
        "O.pdf": ["prashant", "chauhan"],
        "P.pdf": ["amruta", "kulkarni"],
        "Q.pdf": ["raj", "upadhyaya"],
        "mynewcv (1).pdf": ["pankaj", "more"],
    }

    lines = []
    for name in pdfNames:
        path = pdfDir / name
        if not path.exists():
            continue
        raw = path.read_bytes()
        plain = extractPdfplumber(raw)
        fitzRaw = extractPymupdf(raw)
        fitzNorm = normalizeText(fitzRaw)

        plainScore, plainNotes = scoreText(plain, hints[name])
        fitzScore, fitzNotes = scoreText(fitzNorm, hints[name])

        lines.append("=" * 70)
        lines.append(name)
        lines.append(f"pdfplumber score={plainScore} notes={plainNotes}")
        lines.append(f"pymupdf+normalize score={fitzScore} notes={fitzNotes}")
        lines.append("pdfplumber preview:")
        lines.append(repr(plain[:350]))
        lines.append("pymupdf normalized preview:")
        lines.append(repr(fitzNorm[:350]))
        lines.append("")

    out = Path(__file__).parent / "pdf_compare.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"written {out}")


if __name__ == "__main__":
    main()
