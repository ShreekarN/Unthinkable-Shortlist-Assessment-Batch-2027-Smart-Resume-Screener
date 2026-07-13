const params = new URLSearchParams(window.location.search);
const candidateId = params.get("id");
const detailContent = document.getElementById("detailContent");
const archiveBtn = document.getElementById("archiveBtn");
const archiveStatus = document.getElementById("archiveStatus");

archiveBtn.addEventListener("click", archiveCandidate);
boot();

async function boot() {
  if (!candidateId) {
    detailContent.innerHTML = '<p class="empty">Missing candidate id.</p>';
    archiveBtn.disabled = true;
    return;
  }

  await loadDetail();
}

async function loadDetail() {
  const response = await fetch(`/api/candidates/${candidateId}`, {
    credentials: "include",
  });

  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }

  if (!response.ok) {
    detailContent.innerHTML = '<p class="empty">Candidate not found.</p>';
    archiveBtn.disabled = true;
    return;
  }

  const data = await response.json();
  renderDetail(data);
  document.body.classList.remove("auth-pending");

  if (data.archived) {
    archiveBtn.disabled = true;
    archiveBtn.textContent = "Archived";
    archiveStatus.textContent = "Resume file content removed from database. Assessment kept.";
  }
}

function renderDetail(data) {
  const parsedTextBlock = data.hasRawText
    ? `
      ${renderHighlightLegend()}
      <div id="detailParsedText" class="parsed-text-box">${highlightResumeText(
        data.rawText,
        data.evidencePhrases,
        data.strengths,
        data.gaps,
        data.skills
      )}</div>
    `
    : '<p class="empty">File content archived. Assessment data kept.</p>';

  detailContent.innerHTML = `
    <section class="card">
      <div class="detail-block">
        <h3>${escapeHtml(data.name)}</h3>
        <p><strong>Score:</strong> <span class="score">${data.score}</span></p>
        <p><strong>File:</strong> ${escapeHtml(data.fileName)}</p>
        <p><strong>Stored file content:</strong> ${data.hasRawText ? "Present" : "Archived"}</p>
      </div>
      <div class="detail-block">
        <h3>Justification</h3>
        <div id="detailJustification" class="justification-text">${escapeHtml(data.justification)}</div>
      </div>
      <div class="detail-block">
        <h3>Evidence Phrases</h3>
        ${renderPills(data.evidencePhrases)}
      </div>
      <div class="detail-block">
        <h3>Strengths</h3>
        ${renderPills(data.strengths)}
      </div>
      <div class="detail-block">
        <h3>Gaps</h3>
        ${renderPills(data.gaps)}
      </div>
      <div class="detail-block">
        <h3>Extracted Resume Text</h3>
        ${parsedTextBlock}
      </div>
      <div class="detail-block">
        <h3>Skills</h3>
        ${renderPills(data.skills)}
      </div>
      <div class="detail-block">
        <h3>Experience</h3>
        ${renderList(data.experience)}
      </div>
      <div class="detail-block">
        <h3>Education</h3>
        ${renderList(data.education)}
      </div>
    </section>
  `;
}

async function archiveCandidate() {
  if (!confirm("Archive this resume file content? Assessment score and parsed data will be kept.")) {
    return;
  }

  archiveBtn.disabled = true;
  archiveStatus.textContent = "Archiving...";

  try {
    const response = await fetch(`/api/candidates/${candidateId}/archive`, {
      method: "POST",
      credentials: "include",
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Archive failed");
    }

    archiveStatus.textContent = data.message;
    archiveBtn.textContent = "Archived";
    await loadDetail();
  } catch (error) {
    archiveStatus.textContent = error.message;
    archiveBtn.disabled = false;
  }
}

function renderPills(items) {
  if (!items || !items.length) {
    return '<p class="empty">None listed.</p>';
  }

  return `<div class="pill-list">${items
    .map((item) => `<span class="pill">${escapeHtml(item)}</span>`)
    .join("")}</div>`;
}

function renderList(items) {
  if (!items || !items.length) {
    return '<p class="empty">None listed.</p>';
  }

  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
