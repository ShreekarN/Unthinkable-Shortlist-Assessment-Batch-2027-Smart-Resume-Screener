from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import auth, db
from app.config import staticDir
from app.routes import router

app = FastAPI(title="Smart Resume Screener", version="1.1.0")


@app.on_event("startup")
def startup():
    db.initDb()


app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory=staticDir), name="static")


@app.get("/")
def home(request: Request):
    # Redirect before HTML loads so the dashboard never flashes for guests.
    if not auth.getUserFromRequest(request):
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(Path(staticDir) / "index.html")


@app.get("/login")
def loginPage(request: Request):
    if auth.getUserFromRequest(request):
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(Path(staticDir) / "login.html")


@app.get("/candidate")
def candidatePage(request: Request):
    if not auth.getUserFromRequest(request):
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(Path(staticDir) / "candidate.html")
