# Preset job roles with structured default descriptions for screening.

jobRoleList = [
    {"key": "backend", "label": "Backend Developer"},
    {"key": "qa", "label": "QA / SDET"},
    {"key": "data", "label": "Data Analyst"},
    {"key": "frontend", "label": "Frontend Developer"},
    {"key": "other", "label": "Other"},
]

defaultJobMap = {
    "backend": {
        "title": "Backend Developer",
        "description": (
            "Core Skills:\n"
            "Python, FastAPI, REST API design, SQL, database modeling, "
            "authentication, error handling, pytest, Git\n\n"
            "Keywords:\n"
            "microservices, CRUD, JSON APIs, SQLite/PostgreSQL, file upload, "
            "resume parsing, LLM integration, async processing\n\n"
            "Impact Metrics:\n"
            "API response time, test coverage, successful resume parsing rate, "
            "scoring accuracy, reduced manual screening time"
        ),
    },
    "qa": {
        "title": "QA / SDET",
        "description": (
            "Core Skills:\n"
            "Manual testing, test case design, API testing, Selenium, "
            "Playwright, pytest, defect reporting, regression testing\n\n"
            "Keywords:\n"
            "functional testing, integration testing, acceptance testing, "
            "Jenkins, Git, test automation, bug triage, quality assurance\n\n"
            "Impact Metrics:\n"
            "Defect reduction percentage, improved test coverage, "
            "faster release cycles, fewer production incidents"
        ),
    },
    "data": {
        "title": "Data Analyst",
        "description": (
            "Core Skills:\n"
            "SQL, Excel, Python, data cleaning, dashboarding, "
            "statistical analysis, reporting, visualization\n\n"
            "Keywords:\n"
            "Power BI, Tableau, pandas, business insights, KPI tracking, "
            "data storytelling, ETL basics, stakeholder reporting\n\n"
            "Impact Metrics:\n"
            "Reporting accuracy, dashboard adoption, actionable insights delivered, "
            "improved decision speed for business teams"
        ),
    },
    "frontend": {
        "title": "Frontend Developer",
        "description": (
            "Core Skills:\n"
            "HTML, CSS, JavaScript, responsive UI, REST API consumption, "
            "component design, browser debugging\n\n"
            "Keywords:\n"
            "React or vanilla JS, fetch API, form validation, accessibility, "
            "UI state management, dashboard interfaces, Git\n\n"
            "Impact Metrics:\n"
            "Page load performance, UI usability, reduced user task time, "
            "cross-browser compatibility, clean handoff with backend APIs"
        ),
    },
}


def getRoleOptions():
    return jobRoleList


def getDefaultJob(roleKey):
    if roleKey == "other":
        return None
    return defaultJobMap.get(roleKey)
