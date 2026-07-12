from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.config import staticDir
from app.routes import router

app = FastAPI(title="Smart Resume Screener", version="1.1.0")


@app.on_event("startup")
def startup():
    db.initDb()


app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory=staticDir), name="static")


@app.get("/")
def home():
    return FileResponse(Path(staticDir) / "index.html")


@app.get("/login")
def loginPage():
    return FileResponse(Path(staticDir) / "login.html")
