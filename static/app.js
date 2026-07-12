let currentJobId = null;

const jobTitle = document.getElementById("jobTitle");
const jobDescription = document.getElementById("jobDescription");
const createJobBtn = document.getElementById("createJobBtn");
const jobStatus = document.getElementById("jobStatus");
const resumeFiles = document.getElementById("resumeFiles");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const refreshBtn = document.getElementById("refreshBtn");
const shortlistTable = document.getElementById("shortlistTable");
const detailPanel = document.getElementById("detailPanel");
const detailContent = document.getElementById("detailContent");
const closeDetailBtn = document.getElementById("closeDetailBtn");

createJobBtn.addEventListener("click", createJob);
uploadBtn.addEventListener("click", uploadResumes);
refreshBtn.addEventListener("click", loadShortlist);
closeDetailBtn.addEventListener("click", closeDetail);

async function createJob() {
  const title = jobTitle.value.trim();
  const description = jobDescription.value.trim();

  if (!title || !description) {
    jobStatus.textContent = "Enter both title and description.";
    return;
  }

  createJobBtn.disabled = true;
  jobStatus.textContent = "Creating job...";

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description }),
    });

    if (!response.ok) {
      throw new Error("Failed to create job");
    }

    const data = await response.json();
    currentJobId = data.id;
    uploadBtn.disabled = false;
    refreshBtn.disabled = false;
    jobStatus.textContent = `Job created with ID ${currentJobId}.`;
    await loadShortlist();
  } catch (error) {
    jobStatus.textContent = error.message;
  } finally {
    createJobBtn.disabled = false;
  }
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
}

async function loadShortlist() {
  if (!currentJobId) {
    shortlistTable.innerHTML = '<p class="empty">Create a job to see results.</p>';
    return;
  }

  refreshBtn.disabled = true;

  try {
    const response = await fetch(`/api/jobs/${currentJobId}/shortlist`);
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

function renderShortlist(items) {
  if (!items.length) {
    shortlistTable.innerHTML = '<p class="empty">No shortlisted candidates yet.</p>';
    return;
  }

  const rows = items
    .map((item) => {
      const strengths = (item.strengths || []).slice(0, 3).join(", ");
      const justification = item.justification || "";
      const snippet = justification.length > 120 ? `${justification.slice(0, 120)}...` : justification;

      return `
        <tr class="clickable" data-id="${item.id}">
          <td>${escapeHtml(item.name)}</td>
          <td>${escapeHtml(item.fileName)}</td>
          <td class="score">${item.score}</td>
          <td>${escapeHtml(strengths)}</td>
          <td>${escapeHtml(snippet)}</td>
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

  shortlistTable.querySelectorAll("tr.clickable").forEach((row) => {
    row.addEventListener("click", () => {
      const candidateId = row.getAttribute("data-id");
      loadCandidateDetail(candidateId);
    });
  });
}

async function loadCandidateDetail(candidateId) {
  try {
    const response = await fetch(`/api/candidates/${candidateId}`);
    if (!response.ok) {
      throw new Error("Failed to load candidate detail");
    }

    const data = await response.json();
    detailContent.innerHTML = `
      <div class="detail-block">
        <h3>${escapeHtml(data.name)}</h3>
        <p><strong>Score:</strong> <span class="score">${data.score}</span></p>
        <p><strong>File:</strong> ${escapeHtml(data.fileName)}</p>
      </div>
      <div class="detail-block">
        <h3>Justification</h3>
        <p>${escapeHtml(data.justification)}</p>
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
