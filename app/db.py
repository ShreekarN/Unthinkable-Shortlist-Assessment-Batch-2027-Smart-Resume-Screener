import json
import sqlite3
from datetime import datetime, timezone

from app.config import dbPath


def getConn():
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    return conn


def initDb():
    conn = getConn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            createdAt TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jobId INTEGER NOT NULL,
            fileName TEXT NOT NULL,
            rawText TEXT NOT NULL,
            parsedJson TEXT NOT NULL,
            score REAL NOT NULL,
            justification TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            FOREIGN KEY (jobId) REFERENCES jobs(id)
        )
        """
    )
    conn.commit()
    conn.close()


def nowIso():
    return datetime.now(timezone.utc).isoformat()


def createJob(title, description):
    conn = getConn()
    cur = conn.cursor()
    createdAt = nowIso()
    cur.execute(
        "INSERT INTO jobs (title, description, createdAt) VALUES (?, ?, ?)",
        (title, description, createdAt),
    )
    jobId = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": jobId, "title": title, "description": description, "createdAt": createdAt}


def getJob(jobId):
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id = ?", (jobId,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def createCandidate(jobId, fileName, rawText, parsedData, score, justification):
    conn = getConn()
    cur = conn.cursor()
    createdAt = nowIso()
    parsedJson = json.dumps(parsedData)
    cur.execute(
        """
        INSERT INTO candidates
        (jobId, fileName, rawText, parsedJson, score, justification, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (jobId, fileName, rawText, parsedJson, score, justification, createdAt),
    )
    candidateId = cur.lastrowid
    conn.commit()
    conn.close()
    return candidateId


def getCandidate(candidateId):
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates WHERE id = ?", (candidateId,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def getShortlist(jobId, minScore):
    conn = getConn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM candidates
        WHERE jobId = ? AND score >= ?
        ORDER BY score DESC, id DESC
        """,
        (jobId, minScore),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows
