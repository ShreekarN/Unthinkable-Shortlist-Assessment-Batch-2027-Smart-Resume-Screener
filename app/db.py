import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from app.config import dbPath

defaultEmail = "abc@gmail.com"
defaultPassword = "abc123"


def getConn():
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    return conn


def initDb():
    # Create all tables and seed demo login user on first startup.
    conn = getConn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            passwordHash TEXT NOT NULL,
            createdAt TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            userId INTEGER NOT NULL,
            expiresAt TEXT NOT NULL,
            FOREIGN KEY (userId) REFERENCES users(id)
        )
        """
    )
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
    ensureCandidateColumns(cur)
    ensureJobColumns(cur)
    seedDefaultUser(cur)
    conn.commit()
    conn.close()


def ensureCandidateColumns(cur):
    # Add archive columns for databases created before this feature existed.
    cur.execute("PRAGMA table_info(candidates)")
    columns = {row[1] for row in cur.fetchall()}
    if "archived" not in columns:
        cur.execute("ALTER TABLE candidates ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
    if "archivedAt" not in columns:
        cur.execute("ALTER TABLE candidates ADD COLUMN archivedAt TEXT")


def ensureJobColumns(cur):
    # Add per-job shortlist threshold for databases created before this feature.
    cur.execute("PRAGMA table_info(jobs)")
    columns = {row[1] for row in cur.fetchall()}
    if "minScore" not in columns:
        cur.execute("ALTER TABLE jobs ADD COLUMN minScore REAL NOT NULL DEFAULT 7")


def seedDefaultUser(cur):
    cur.execute("SELECT id FROM users WHERE email = ?", (defaultEmail,))
    if cur.fetchone():
        return
    createdAt = nowIso()
    passwordHash = hashlib.sha256(defaultPassword.encode("utf-8")).hexdigest()
    cur.execute(
        "INSERT INTO users (email, passwordHash, createdAt) VALUES (?, ?, ?)",
        (defaultEmail, passwordHash, createdAt),
    )


def nowIso():
    return datetime.now(timezone.utc).isoformat()


def getUserByEmail(email):
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def getUserById(userId):
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT id, email, createdAt FROM users WHERE id = ?", (userId,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def createSession(token, userId, expiresAt):
    conn = getConn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (token, userId, expiresAt) VALUES (?, ?, ?)",
        (token, userId, expiresAt),
    )
    conn.commit()
    conn.close()


def getSession(token):
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sessions WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def deleteSession(token):
    conn = getConn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def createJob(title, description, minScore):
    conn = getConn()
    cur = conn.cursor()
    createdAt = nowIso()
    cur.execute(
        "INSERT INTO jobs (title, description, createdAt, minScore) VALUES (?, ?, ?, ?)",
        (title, description, createdAt, minScore),
    )
    jobId = cur.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": jobId,
        "title": title,
        "description": description,
        "createdAt": createdAt,
        "minScore": minScore,
    }


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


def getAllCandidates(jobId):
    # Return every parsed resume for Parsed Resumes tab, not only shortlist.
    conn = getConn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM candidates
        WHERE jobId = ?
        ORDER BY score DESC, id DESC
        """,
        (jobId,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def archiveCandidate(candidateId):
    # Remove stored PDF or text content but keep parsed assessment data.
    conn = getConn()
    cur = conn.cursor()
    cur.execute("SELECT id, archived FROM candidates WHERE id = ?", (candidateId,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    archivedAt = nowIso()
    cur.execute(
        """
        UPDATE candidates
        SET rawText = '', archived = 1, archivedAt = ?
        WHERE id = ?
        """,
        (archivedAt, candidateId),
    )
    conn.commit()
    conn.close()
    return {"id": candidateId, "archived": True, "archivedAt": archivedAt}
