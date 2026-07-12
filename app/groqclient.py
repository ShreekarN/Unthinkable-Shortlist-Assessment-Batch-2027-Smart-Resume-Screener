import json
import re

from groq import Groq

from app.config import groqApiKey, groqModel

extractSystemPrompt = (
    "You extract resume data. Return strict JSON only with keys: "
    "name (string), skills (array of strings), experience (array of strings), "
    "education (array of strings). No markdown."
)

matchSystemPrompt = (
    "Compare the following resume with this job description and rate fit on "
    "1-10 with justification. Return strict JSON only with keys: "
    "score (number 1-10), justification (string), strengths (array of strings), "
    "gaps (array of strings). No markdown."
)


def getClient():
    if not groqApiKey:
        raise ValueError("GROQAPIKEY is missing in .env")
    return Groq(api_key=groqApiKey)


def cleanJson(text):
    trimmed = text.strip()
    if trimmed.startswith("```"):
        trimmed = re.sub(r"^```(?:json)?\s*", "", trimmed)
        trimmed = re.sub(r"\s*```$", "", trimmed)
    return trimmed.strip()


def parseJson(text):
    cleaned = cleanJson(text)
    return json.loads(cleaned)


def callGroq(systemPrompt, userPrompt):
    client = getClient()
    response = client.chat.completions.create(
        model=groqModel,
        messages=[
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": userPrompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def callGroqJson(systemPrompt, userPrompt):
    lastError = None
    for attempt in range(2):
        try:
            raw = callGroq(systemPrompt, userPrompt)
            return parseJson(raw)
        except (json.JSONDecodeError, ValueError) as err:
            lastError = err
    raise ValueError(f"LLM returned invalid JSON: {lastError}")


def extractResume(resumeText):
    userPrompt = f"Resume text:\n{resumeText}"
    data = callGroqJson(extractSystemPrompt, userPrompt)
    return {
        "name": str(data.get("name", "Unknown")),
        "skills": list(data.get("skills", [])),
        "experience": list(data.get("experience", [])),
        "education": list(data.get("education", [])),
    }


def matchResume(parsedResume, jobDescription):
    resumeJson = json.dumps(parsedResume, indent=2)
    userPrompt = (
        f"Job description:\n{jobDescription}\n\n"
        f"Parsed resume:\n{resumeJson}"
    )
    data = callGroqJson(matchSystemPrompt, userPrompt)
    score = float(data.get("score", 0))
    score = max(1.0, min(10.0, score))
    return {
        "score": score,
        "justification": str(data.get("justification", "")),
        "strengths": list(data.get("strengths", [])),
        "gaps": list(data.get("gaps", [])),
    }
