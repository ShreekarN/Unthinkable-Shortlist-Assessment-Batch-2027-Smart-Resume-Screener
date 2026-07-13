from pathlib import Path

import pytest

from app import parser

pdfDir = Path(__file__).resolve().parent.parent.parent


def testExtractTxtFromBytes():
    text = parser.extractTxt(b"John Doe\nPython developer")
    assert "John Doe" in text


def testExtractTxtEmptyRaises():
    with pytest.raises(ValueError, match="empty"):
        parser.extractTxt(b"   ")


def testUnsupportedFileRaises():
    with pytest.raises(ValueError, match="Only PDF and TXT"):
        parser.extractText("resume.docx", b"data")


def testNormalizeTextFixesHyphenLineBreak():
    raw = "Python develop-\nment with FastAPI"
    normalized = parser.normalizeText(raw)
    assert "development" in normalized


def testNormalizeTextFixesSmartQuotes():
    normalized = parser.normalizeText("Candidate\u2019s profile")
    assert "Candidate's profile" in normalized


def testExtractPdfFromRealFiles():
    pdfPath = pdfDir / "N.pdf"
    if not pdfPath.exists():
        pytest.skip("N.pdf not found")

    fileBytes = pdfPath.read_bytes()
    text = parser.extractText("N.pdf", fileBytes)
    assert len(text) > 50


def testExtractAllProvidedPdfs(pdfFiles):
    if not pdfFiles:
        pytest.skip("No PDF files found")

    for pdfPath in pdfFiles:
        text = parser.extractText(pdfPath.name, pdfPath.read_bytes())
        assert text.strip(), f"No text extracted from {pdfPath.name}"
