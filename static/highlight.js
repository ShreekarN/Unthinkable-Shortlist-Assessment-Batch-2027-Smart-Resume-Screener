// Resume text highlighter for Parsed Resumes / candidate detail.
// Priority when ranges overlap: evidence (4) > strength (3) > gap (2) > skill (1).

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function findPhraseMatches(text, phrase, className, priority) {
  const trimmed = String(phrase || "").trim();
  if (trimmed.length < 2) {
    return [];
  }

  const pattern = escapeRegex(trimmed).replace(/\s+/g, "\\s+");
  const regex = new RegExp(pattern, "gi");
  const matches = [];
  let match = regex.exec(text);
  while (match) {
    matches.push({
      start: match.index,
      end: match.index + match[0].length,
      className,
      priority,
    });
    match = regex.exec(text);
  }
  return matches;
}

function pickNonOverlapping(matches) {
  const sorted = [...matches].sort((left, right) => {
    if (left.start !== right.start) {
      return left.start - right.start;
    }
    if (left.priority !== right.priority) {
      return right.priority - left.priority;
    }
    return right.end - right.start - (left.end - left.start);
  });

  const picked = [];
  for (const candidate of sorted) {
    const overlapIndex = picked.findIndex(
      (item) => !(candidate.end <= item.start || candidate.start >= item.end)
    );
    if (overlapIndex === -1) {
      picked.push(candidate);
      continue;
    }
    if (candidate.priority > picked[overlapIndex].priority) {
      picked[overlapIndex] = candidate;
    }
  }

  return picked.sort((left, right) => left.start - right.start);
}

function highlightResumeText(text, evidencePhrases, strengths, gaps, skills) {
  const safeText = String(text || "");
  if (!safeText) {
    return '<p class="empty">No extracted text available.</p>';
  }

  const groups = [
    { phrases: evidencePhrases || [], className: "hl-evidence", priority: 4 },
    { phrases: strengths || [], className: "hl-strength", priority: 3 },
    { phrases: gaps || [], className: "hl-gap", priority: 2 },
    { phrases: skills || [], className: "hl-skill", priority: 1 },
  ];

  const allMatches = [];
  for (const group of groups) {
    for (const phrase of group.phrases) {
      allMatches.push(
        ...findPhraseMatches(safeText, phrase, group.className, group.priority)
      );
    }
  }

  const picked = pickNonOverlapping(allMatches);
  let html = "";
  let cursor = 0;

  for (const item of picked) {
    html += escapeHtml(safeText.slice(cursor, item.start));
    html += `<mark class="${item.className}">${escapeHtml(
      safeText.slice(item.start, item.end)
    )}</mark>`;
    cursor = item.end;
  }

  html += escapeHtml(safeText.slice(cursor));
  return html;
}

function renderHighlightLegend() {
  return `
    <div class="highlight-legend">
      <span><mark class="hl-evidence">Evidence</mark> score support</span>
      <span><mark class="hl-strength">Strength</mark> match</span>
      <span><mark class="hl-gap">Gap</mark> area</span>
      <span><mark class="hl-skill">Skill</mark> keyword</span>
    </div>
  `;
}
