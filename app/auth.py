import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from app import db

sessionHours = 24
cookieName = "sessionToken"


def hashPassword(rawPassword):
    # Stable hash for demo login storage in SQLite.
    return hashlib.sha256(rawPassword.encode("utf-8")).hexdigest()


def verifyPassword(rawPassword, storedHash):
    return hashPassword(rawPassword) == storedHash


def createSession(userId):
    token = secrets.token_urlsafe(32)
    expiresAt = datetime.now(timezone.utc) + timedelta(hours=sessionHours)
    db.createSession(token, userId, expiresAt.isoformat())
    return token


def clearSession(token):
    if token:
        db.deleteSession(token)


def getUserFromRequest(request: Request):
    # Read cookie token and validate session expiry before protected routes run.
    token = request.cookies.get(cookieName)
    if not token:
        return None

    session = db.getSession(token)
    if not session:
        return None

    expiresAt = datetime.fromisoformat(session["expiresAt"])
    if expiresAt < datetime.now(timezone.utc):
        db.deleteSession(token)
        return None

    return db.getUserById(session["userId"])


def requireUser(request: Request):
    user = getUserFromRequest(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user
