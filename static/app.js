let currentJobId = null;
let currentJobMinScore = 7;
let jobRoles = [];

// Dashboard: auth boot, menu drawer tabs, upload/score, parsed list, highlights, archive.

const menuBtn = document.getElementById("menuBtn");
const sideNav = document.getElementById("sideNav");
const navBackdrop = document.getElementById("navBackdrop");
const logoutBtn = document.getElementById("logoutBtn");
const userEmail = document.getElementById("userEmail");
const jobRole = document.getElementById("jobRole");
const customTitleWrap = document.getElementById("customTitleWrap");
const customJobTitle = document.getElementById("customJobTitle");
const jobDescription = document.getElementById("jobDescription");
const minScoreInput = document.getElementById("minScore");
const shortlistHint = document.getElementById("shortlistHint");
const createJobBtn = document.getElementById("createJobBtn");
const jobStatus = document.getElementById("jobStatus");
const resumeFiles = document.getElementById("resumeFiles");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const refreshBtn = document.getElementById("refreshBtn");
const refreshParsedBtn = document.getElementById("refreshParsedBtn");
const shortlistTable = document.getElementById("shortlistTable");
const parsedTable = document.getElementById("parsedTable");
const parsedTextPanel = document.getElementById("parsedTextPanel");
const parsedTextLegend = document.getElementById("parsedTextLegend");
const parsedTextContent = document.getElementById("parsedTextContent");
const parsedTextExpandBtn = document.getElementById("parsedTextExpandBtn");
const closeParsedTextBtn = document.getElementById("closeParsedTextBtn");
const detailPanel = document.getElementById("detailPanel");
const detailContent = document.getElementById("detailContent");
const closeDetailBtn = document.getElementById("closeDetailBtn");

menuBtn.addEventListener("click", (event) => {
  event.stopPropagation();
  toggleSideNav();
});
navBackdrop.addEventListener("click", closeSideNav);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeSideNav();
  }
});
logoutBtn.addEventListener("click", logout);
createJobBtn.addEventListener("click", createJob);
uploadBtn.addEventListener("click", uploadResumes);
refreshBtn.addEventListener("click", loadShortlist);
refreshParsedBtn.addEventListener("click", loadParsedResumes);
closeDetailBtn.addEventListener("click", closeDetail);
closeParsedTextBtn.addEventListener("click", closeParsedText);
parsedTextExpandBtn.addEventListener("click", toggleParsedTextExpand);
jobRole.addEventListener("change", onRoleChange);

document.querySelectorAll('input[name="jdMode"]').forEach((input) => {
  input.addEventListener("change", onJdModeChange);
});

document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => switchTab(link.dataset.tab));
});

boot();

async function boot() {
  const me = await apiGet("/api/auth/me");
  if (!me) {
    window.location.href = "/login";
    return;
  }

  userEmail.textContent = me.email;
  document.body.classList.remove("auth-pending");
  await loadJobRoles();
  onRoleChange();
  onJdModeChange();
}

async function apiGet(url, options = {}) {
  const response = await fetch(url, { credentials: "include", ...options });
  if (response.status === 401) {
    window.location.href = "/login";
    return null;
  }
  return response;
}

async function loadJobRoles() {
  const response = await apiGet("/api/job-roles");
  if (!response || !response.ok) {
    return;
  }

  jobRoles = await response.json();
  jobRole.innerHTML = jobRoles
    .map((role) => `<option value="${role.key}">${escapeHtml(role.label)}</option>`)
    .join("");
}

function toggleSideNav() {
  if (sideNav.classList.contains("open")) {
    closeSideNav();
  } else {
    openSideNav();
  }
}

function openSideNav() {
  sideNav.classList.add("open");
  navBackdrop.hidden = false;
  menuBtn.setAttribute("aria-expanded", "true");
  menuBtn.setAttribute("aria-label", "Close menu");
}

function closeSideNav() {
  sideNav.classList.remove("open");
  navBackdrop.hidden = true;
  menuBtn.setAttribute("aria-expanded", "false");
  menuBtn.setAttribute("aria-label", "Open menu");
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabId);
  });
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.toggle("active", link.dataset.tab === tabId);
  });
  closeSideNav();

  if (tabId === "parsedTab") {
    loadParsedResumes();
  }
}

function onRoleChange() {
  const roleKey = jobRole.value;
  const isOther = roleKey === "other";
  customTitleWrap.classList.toggle("hidden", !isOther);

  const useDefault = document.querySelector('input[name="jdMode"][value="default"]').checked;
  if (!isOther && useDefault) {
    loadDefaultTemplate(roleKey);
  }
}

function onJdModeChange() {
  const useDefault = document.querySelector('input[name="jdMode"][value="default"]').checked;
  const isOther = jobRole.value === "other";

  if (useDefault && !isOther) {
    jobDescription.readOnly = true;
    loadDefaultTemplate(jobRole.value);
    return;
  }

  jobDescription.readOnly = false;
  if (!jobDescription.value.trim()) {
    jobDescription.value = "";
  }
}

async function loadDefaultTemplate(roleKey) {
  const response = await apiGet(`/api/job-templates/${roleKey}`);
  if (!response || !response.ok) {
    return;
  }

  const template = await response.json();
  jobDescription.value = template.description;
}

function getJobTitleValue() {
  if (jobRole.value === "other") {
    return customJobTitle.value.trim();
  }

  const selected = jobRoles.find((role) => role.key === jobRole.value);
  return selected ? selected.label : "";
}

async function createJob() {
  const title = getJobTitleValue();
  const description = jobDescription.value.trim();
  const minScore = Number(minScoreInput.value);

  if (!title || !description) {
    jobStatus.textContent = "Enter job title and description.";
    return;
  }

  if (Number.isNaN(minScore) || minScore < 1 || minScore > 10) {
    jobStatus.textContent = "Threshold must be between 1 and 10.";
    return;
  }

  createJobBtn.disabled = true;
  jobStatus.textContent = "Creating job...";

  try {
    const response = await apiGet("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, minScore }),
    });

    if (!response.ok) {
      throw new Error("Failed to create job");
    }

    const data = await response.json();
    currentJobId = data.id;
    currentJobMinScore = data.minScore;
    updateShortlistHint();
    uploadBtn.disabled = false;
    refreshBtn.disabled = false;
    refreshParsedBtn.disabled = false;
    jobStatus.textContent = `Job created with ID ${currentJobId}. Threshold: ${currentJobMinScore}.`;
    await loadShortlist();
    await loadParsedResumes();
  } catch (error) {
    jobStatus.textContent = error.message;
  } finally {
    createJobBtn.disabled = false;
  }
}

function updateShortlistHint() {
  shortlistHint.textContent = `Candidates with score ${currentJobMinScore} or higher appear here.`;
}

async function uploadResumes() {
  if (!currentJobId) {
    uploadStatus.textContent = "Create a job first.";
    return;
  }

  const files = Array.from(resumeFiles.files || []);
  if (!files.length) {
    uploadStatus.textContent = "Select at least one resume file.";
    return;
  }

  uploadBtn.disabled = true;
  uploadStatus.textContent = "Uploading and scoring resumes...";

  const results = [];
  for (const file of files) {
    const formData = new FormData();
    formData.append("jobId", String(currentJobId));
    formData.append("file", file);

    try {
      const response = await fetch("/api/resumes", {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        results.push(`${file.name}: ${data.detail || "Upload failed"}`);
      } else {
        results.push(`${file.name}: score ${data.score} - ${data.message}`);
      }
    } catch (error) {
      results.push(`${file.name}: ${error.message}`);
    }
  }

  uploadStatus.innerHTML = results.map((line) => `<div>${line}</div>`).join("");
  uploadBtn.disabled = false;
  resumeFiles.value = "";
  await loadShortlist();
  await loadParsedResumes();
}

async function loadShortlist() {
  if (!currentJobId) {
    shortlistTable.innerHTML = '<p class="empty">Create a job to see results.</p>';
    return;
  }

  refreshBtn.disabled = true;
  try {
    const response = await apiGet(`/api/jobs/${currentJobId}/shortlist`);
    if (!response.ok) {
      throw new Error("Failed to load shortlist");
    }
    const items = await response.json();
    renderShortlist(items);
  } catch (error) {
    shortlistTable.innerHTML = `<p class="empty">${error.message}</p>`;
  } finally {
    refreshBtn.disabled = false;
  }
}

async function loadParsedResumes() {
  if (!currentJobId) {
    parsedTable.innerHTML = '<p class="empty">Create a job to view parsed resumes.</p>';
    return;
  }

  refreshParsedBtn.disabled = true;
  try {
    const response = await apiGet(`/api/jobs/${currentJobId}/parsed`);
    if (!response.ok) {
      throw new Error("Failed to load parsed resumes");
    }
    const items = await response.json();
    renderParsedTable(items);
  } catch (error) {
    parsedTable.innerHTML = `<p class="empty">${error.message}</p>`;
  } finally {
    refreshParsedBtn.disabled = false;
  }
}

function renderShortlist(items) {
  if (!items.length) {
    shortlistTable.innerHTML = '<p class="empty">No shortlisted candidates yet.</p>';
    return;
  }

  const rows = items
    .map((item) => {
      const strengths = (item.strengths || []).slice(0, 3).join(", ");
      return `
        <tr class="clickable" data-id="${item.id}">
          <td>${escapeHtml(item.name)}</td>
          <td>${escapeHtml(item.fileName)}</td>
          <td class="score">${item.score}</td>
          <td>${escapeHtml(strengths)}</td>
          <td>${renderJustificationCell(item.justification, `short-${item.id}`)}</td>
        </tr>
      `;
    })
    .join("");

  shortlistTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>File</th>
          <th>Score</th>
          <th>Strengths</th>
          <th>Justification</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  bindRowClicks(shortlistTable);
  bindExpandButtons(shortlistTable);
}

function renderParsedTable(items) {
  if (!items.length) {
    parsedTable.innerHTML = '<p class="empty">No parsed resumes stored yet.</p>';
    return;
  }

  const rows = items
    .map((item) => {
      const skillPreview = (item.skills || []).slice(0, 4).join(", ");
      let badge = item.shortlisted
        ? '<span class="badge yes">Shortlisted</span>'
        : `<span class="badge no">Below ${currentJobMinScore}</span>`;
      if (item.archived) {
        badge += ' <span class="badge archived">Archived</span>';
      }

      return `
        <tr data-id="${item.id}">
          <td>${escapeHtml(item.name)}</td>
          <td>${escapeHtml(item.fileName)}</td>
          <td class="score">${item.score}</td>
          <td>${badge}</td>
          <td>${escapeHtml(skillPreview)}</td>
          <td>${renderJustificationCell(item.justification, `parsed-${item.id}`)}</td>
          <td>
            <button class="open-btn" data-open-id="${item.id}" type="button">Open</button>
            <button class="text-btn" data-text-id="${item.id}" type="button" ${
        item.hasRawText ? "" : "disabled"
      }>Text</button>
            <button class="action-btn" data-archive-id="${item.id}" type="button" ${item.archived ? "disabled" : ""}>
              ${item.archived ? "Archived" : "Archive"}
            </button>
          </td>
        </tr>
      `;
    })
    .join("");

  parsedTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>File</th>
          <th>Score</th>
          <th>Status</th>
          <th>Skills</th>
          <th>Justification</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  bindParsedActions(parsedTable);
  bindExpandButtons(parsedTable);
}

function bindParsedActions(container) {
  container.querySelectorAll("[data-open-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const candidateId = button.getAttribute("data-open-id");
      window.open(`/candidate?id=${candidateId}`, "_blank");
    });
  });

  container.querySelectorAll("[data-text-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const candidateId = button.getAttribute("data-text-id");
      await showParsedText(candidateId);
    });
  });

  container.querySelectorAll("[data-archive-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const candidateId = button.getAttribute("data-archive-id");
      if (!confirm("Archive file content for this resume? Assessment will be kept.")) {
        return;
      }

      button.disabled = true;
      try {
        const response = await apiGet(`/api/candidates/${candidateId}/archive`, {
          method: "POST",
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Archive failed");
        }
        await loadParsedResumes();
        await loadShortlist();
      } catch (error) {
        alert(error.message);
        button.disabled = false;
      }
    });
  });
}

function renderJustificationCell(text, key) {
  const safeText = escapeHtml(text || "");
  const needsExpand = (text || "").length > 110;
  if (!needsExpand) {
    return `<div class="justification-wrap"><div>${safeText}</div></div>`;
  }

  return `
    <div class="justification-wrap">
      <div id="${key}" class="justification-text collapsed">${safeText}</div>
      <button class="expand-btn" data-target="${key}" type="button">Show more</button>
    </div>
  `;
}

function bindExpandButtons(container) {
  container.querySelectorAll(".expand-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const target = document.getElementById(button.dataset.target);
      const collapsed = target.classList.toggle("collapsed");
      button.textContent = collapsed ? "Show more" : "Show less";
    });
  });
}

function bindRowClicks(container) {
  container.querySelectorAll("tr.clickable").forEach((row) => {
    row.addEventListener("click", () => {
      loadCandidateDetail(row.getAttribute("data-id"));
    });
  });
}

async function showParsedText(candidateId) {
  try {
    const response = await apiGet(`/api/candidates/${candidateId}`);
    if (!response.ok) {
      throw new Error("Failed to load parsed text");
    }

    const data = await response.json();
    parsedTextLegend.innerHTML = renderHighlightLegend();
    if (!data.hasRawText) {
      parsedTextContent.innerHTML = '<span class="empty">File content archived. Assessment data kept.</span>';
      parsedTextExpandBtn.classList.add("hidden");
    } else {
      parsedTextContent.innerHTML = highlightResumeText(
        data.rawText,
        data.evidencePhrases,
        data.strengths,
        data.gaps,
        data.skills
      );
      parsedTextExpandBtn.classList.remove("hidden");
      parsedTextContent.classList.add("collapsed");
      parsedTextExpandBtn.textContent = "Show more";
    }

    parsedTextPanel.classList.remove("hidden");
    parsedTextPanel.scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    alert(error.message);
  }
}

function toggleParsedTextExpand() {
  const collapsed = parsedTextContent.classList.toggle("collapsed");
  parsedTextExpandBtn.textContent = collapsed ? "Show more" : "Show less";
}

function closeParsedText() {
  parsedTextPanel.classList.add("hidden");
  parsedTextContent.innerHTML = "";
  parsedTextLegend.innerHTML = "";
}

async function loadCandidateDetail(candidateId) {
  try {
    const response = await apiGet(`/api/candidates/${candidateId}`);
    if (!response.ok) {
      throw new Error("Failed to load candidate detail");
    }

    const data = await response.json();
    detailContent.innerHTML = `
      <div class="detail-block">
        <h3>${escapeHtml(data.name)}</h3>
        <p><strong>Score:</strong> <span class="score">${data.score}</span></p>
        <p><strong>File:</strong> ${escapeHtml(data.fileName)}</p>
        <p><strong>Stored file content:</strong> ${data.hasRawText ? "Present" : "Archived"}</p>
      </div>
      <div class="detail-block">
        <h3>Justification</h3>
        <div id="detailJustification" class="justification-text collapsed">${escapeHtml(data.justification)}</div>
        <button id="detailExpandBtn" class="expand-btn" type="button">Show more</button>
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
        ${renderHighlightLegend()}
        ${
          data.hasRawText
            ? `<div id="detailParsedText" class="parsed-text-box collapsed">${highlightResumeText(
                data.rawText,
                data.evidencePhrases,
                data.strengths,
                data.gaps,
                data.skills
              )}</div><button id="detailTextExpandBtn" class="expand-btn" type="button">Show more</button>`
            : '<p class="empty">File content archived. Assessment data kept.</p>'
        }
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
    `;

    const detailExpandBtn = document.getElementById("detailExpandBtn");
    const detailJustification = document.getElementById("detailJustification");
    if ((data.justification || "").length <= 220) {
      detailExpandBtn.classList.add("hidden");
      detailJustification.classList.remove("collapsed");
    } else {
      detailExpandBtn.addEventListener("click", () => {
        const collapsed = detailJustification.classList.toggle("collapsed");
        detailExpandBtn.textContent = collapsed ? "Show more" : "Show less";
      });
    }

    const detailTextExpandBtn = document.getElementById("detailTextExpandBtn");
    const detailParsedText = document.getElementById("detailParsedText");
    if (detailTextExpandBtn && detailParsedText) {
      detailTextExpandBtn.addEventListener("click", () => {
        const collapsed = detailParsedText.classList.toggle("collapsed");
        detailTextExpandBtn.textContent = collapsed ? "Show more" : "Show less";
      });
    }

    detailPanel.classList.remove("hidden");
    detailPanel.scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    detailContent.innerHTML = `<p class="empty">${error.message}</p>`;
    detailPanel.classList.remove("hidden");
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

function closeDetail() {
  detailPanel.classList.add("hidden");
  detailContent.innerHTML = "";
}

async function logout() {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  window.location.href = "/login";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
