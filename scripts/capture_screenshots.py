import re
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

baseUrl = "http://127.0.0.1:8001"
projectDir = Path(__file__).resolve().parent.parent
shotDir = projectDir / "screenshots"
pdfDir = projectDir.parent

loginEmail = "abc@gmail.com"
loginPassword = "abc123"
pdfNames = ["N.pdf", "O.pdf", "P.pdf", "Q.pdf", "mynewcv (1).pdf"]


def snap(page, name):
    shotDir.mkdir(exist_ok=True)
    path = shotDir / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"saved {path.name}")


def waitForText(page, text, timeout=300000):
    page.wait_for_function(
        "expected => document.body.innerText.includes(expected)",
        arg=text,
        timeout=timeout,
    )


def waitForUploadDone(page, fileCount, timeout=300000):
    page.wait_for_function(
        """
        (count) => {
          const status = document.getElementById('uploadStatus');
          if (!status) return false;
          const text = status.innerText || '';
          if (text.includes('Uploading')) return false;
          const matches = text.match(/score/gi) || [];
          return matches.length >= count;
        }
        """,
        arg=fileCount,
        timeout=timeout,
    )


def getJobId(page):
    text = page.locator("#jobStatus").inner_text()
    match = re.search(r"ID (\d+)", text)
    if not match:
        raise ValueError("Job id not found on page")
    return int(match.group(1))


def getAnyCandidateId(jobId, cookies):
    parsed = httpx.get(
        f"{baseUrl}/api/jobs/{jobId}/parsed",
        cookies=cookies,
        timeout=60,
    ).json()
    if parsed:
        return parsed[0]["id"]
    return None


def clearOldScreenshots():
    if shotDir.exists():
        for oldFile in shotDir.glob("*.png"):
            oldFile.unlink()


def main():
    pdfPaths = [pdfDir / name for name in pdfNames if (pdfDir / name).exists()]
    if not pdfPaths:
        raise FileNotFoundError("No PDF files found for screenshot demo")

    clearOldScreenshots()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1200})
        page = context.new_page()

        page.goto(f"{baseUrl}/login", wait_until="networkidle")
        snap(page, "01-login-page")

        page.fill("#loginEmail", loginEmail)
        page.fill("#loginPassword", loginPassword)
        snap(page, "02-login-filled")

        page.click("#loginBtn")
        page.wait_for_url(f"{baseUrl}/**")
        waitForText(page, "Upload and Score")
        time.sleep(0.5)
        snap(page, "03-dashboard-upload-tab")

        page.select_option("#jobRole", "backend")
        page.wait_for_function(
            "() => (document.getElementById('jobDescription').value || '').includes('Core Skills')",
            timeout=30000,
        )
        snap(page, "04-default-jd-selected")

        page.click("#createJobBtn")
        waitForText(page, "Job created with ID")
        time.sleep(0.5)
        snap(page, "05-job-created")
        jobId = getJobId(page)

        page.set_input_files("#resumeFiles", [str(path) for path in pdfPaths[:3]])
        snap(page, "06-resumes-selected")

        page.click("#uploadBtn")
        waitForUploadDone(page, 3)
        time.sleep(1)
        snap(page, "07-upload-results")

        page.click("#refreshBtn")
        page.wait_for_timeout(1000)
        snap(page, "08-shortlist-view")

        page.click('button.nav-link[data-tab="parsedTab"]')
        page.wait_for_timeout(1000)
        snap(page, "09-parsed-resumes-tab")

        cookies = {c["name"]: c["value"] for c in context.cookies()}
        candidateId = getAnyCandidateId(jobId, cookies)
        if candidateId:
            page.evaluate("(id) => loadCandidateDetail(id)", candidateId)
            waitForText(page, "Justification")
            time.sleep(0.5)
            snap(page, "10-candidate-detail")

        browser.close()

    print(f"done folder {shotDir}")


if __name__ == "__main__":
    main()
