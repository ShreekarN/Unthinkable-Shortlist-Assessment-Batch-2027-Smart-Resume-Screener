import json
import re

from groq import Groq

from app.config import groqApiKey, groqModel

# Two-step LLM pipeline:
# 1) extractResume — structured fields from normalized resume text
# 2) matchResume — score + justification + strengths/gaps + evidencePhrases
# Match also receives original resume text (truncated) so evidencePhrases can be quoted.

extractSystemPrompt = (
    "You are a resume parsing specialist for technical hiring workflows. "
    "Read the resume text and extract only factual information present in the document. "
    "Return strict JSON with keys: name (string), skills (array of strings), "
    "experience (array of concise role or project strings), "
    "education (array of concise education strings). "
    "Do not invent details. Do not use markdown. Return JSON only."
)

matchSystemPrompt = (
    "You are a technical recruiter evaluating candidate fit for a specific role. "
    "Compare the parsed resume data against the job description and produce a fair, "
    "evidence-based assessment. Score fit from 1 to 10 where 10 is an excellent match. "
    "Return strict JSON with keys: score (number 1-10), justification (string with 3-5 "
    "complete sentences explaining the score), strengths (array of role-relevant strengths), "
    "gaps (array of missing or weak areas), evidencePhrases (array of 3-8 short phrases "
    "copied from the resume wording that most directly support the score). "
    "Use exact resume phrasing in evidencePhrases when possible. "
    "Base conclusions only on provided data. Do not use markdown. Return JSON only."
)


def getClient():
    if not groqApiKey:
        raise ValueError("GROQAPIKEY is missing in .env")
    return Groq(api_key=groqApiKey)


def cleanJson(text):
    # Strip optional markdown fences before json.loads.
    trimmed = text.strip()
    if trimmed.startswith("```"):
        trimmed = re.sub(r"^```(?:json)?\s*", "", trimmed)
        trimmed = re.sub(r"\s*```$", "", trimmed)
    return trimmed.strip()


def parseJson(text):
    cleaned = cleanJson(text)
    return json.loads(cleaned)


def callGroq(systemPrompt, userPrompt):
    # Low temperature keeps extract/match responses more deterministic.
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
    # Retry once because models can occasionally return non-JSON text.
    lastError = None
    for attempt in range(2):
        try:
            raw = callGroq(systemPrompt, userPrompt)
            return parseJson(raw)
        except (json.JSONDecodeError, ValueError) as err:
            lastError = err
    raise ValueError(f"LLM returned invalid JSON: {lastError}")


def extractResume(resumeText):
    userPrompt = (
        "Extract structured resume fields from the text below.\n\n"
        f"Resume text:\n{resumeText}"
    )
    data = callGroqJson(extractSystemPrompt, userPrompt)
    return {
        "name": str(data.get("name", "Unknown")),
        "skills": list(data.get("skills", [])),
        "experience": list(data.get("experience", [])),
        "education": list(data.get("education", [])),
    }


def matchResume(parsedResume, jobDescription, resumeText=""):
    # Include original resume text so evidencePhrases can quote real wording.
    resumeJson = json.dumps(parsedResume, indent=2)
    resumeSnippet = resumeText[:8000] if resumeText else ""
    userPrompt = (
        "Evaluate candidate fit using the job description, original resume text, "
        "and parsed resume below.\n\n"
        f"Job description:\n{jobDescription}\n\n"
        f"Original resume text (quote evidencePhrases from this when possible):\n"
        f"{resumeSnippet}\n\n"
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
        "evidencePhrases": list(data.get("evidencePhrases", [])),
    }
