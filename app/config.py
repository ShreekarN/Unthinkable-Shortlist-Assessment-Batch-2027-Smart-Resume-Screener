import os
from pathlib import Path

from dotenv import load_dotenv

baseDir = Path(__file__).resolve().parent.parent
load_dotenv(baseDir / ".env")

groqApiKey = os.getenv("GROQAPIKEY", "")
groqModel = os.getenv("GROQMODEL", "llama-3.3-70b-versatile")
dbPath = baseDir / "resumes.db"
staticDir = baseDir / "static"
shortlistMinScore = 7  # Default threshold when a job has no saved minScore
