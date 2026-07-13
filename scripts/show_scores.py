import sqlite3
from pathlib import Path

dbPath = Path(__file__).resolve().parent.parent / "resumes.db"
if not dbPath.exists():
    print("No database found")
    raise SystemExit(0)

conn = sqlite3.connect(dbPath)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute(
    """
    SELECT fileName, score, justification, jobId, id
    FROM candidates
    WHERE fileName LIKE '%.pdf'
    ORDER BY id DESC
    """
)
rows = cur.fetchall()
seen = set()
print("PDF|Score|Status|JobId")
for row in rows:
    name = row["fileName"]
    if name in seen:
        continue
    seen.add(name)
    status = "SELECTED" if row["score"] >= 7 else "REJECTED"
    print(f"{name}|{row['score']}|{status}|{row['jobId']}")

conn.close()
