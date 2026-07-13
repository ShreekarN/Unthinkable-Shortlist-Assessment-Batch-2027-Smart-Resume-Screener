from pathlib import Path

from app import parser

pdfDir = Path(__file__).resolve().parent.parent.parent
pdfNames = ["N.pdf", "O.pdf", "P.pdf", "Q.pdf", "mynewcv (1).pdf"]

for name in pdfNames:
    path = pdfDir / name
    if not path.exists():
        print(f"MISSING {name}")
        continue
    raw = path.read_bytes()
    try:
        text = parser.extractText(name, raw)
    except Exception as err:
        print(f"FAIL {name}: {err}")
        continue

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    preview = "\n".join(lines[:8])
    weird = sum(1 for ch in text if ord(ch) > 127 and ch not in "–—•")
    gaps = text.count("  ") + text.count("\n\n\n")
    print("=" * 60)
    print(name)
    print(f"chars={len(text)} lines={len(lines)} nonAscii={weird}")
    print("PREVIEW:")
    print(preview[:500])
    print()
