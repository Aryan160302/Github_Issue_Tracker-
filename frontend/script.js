// Simple JavaScript frontend – no framework needed.

const API_BASE_URL = "http://127.0.0.1:8000";

const form = document.getElementById("issue-form");
const repoInput = document.getElementById("repo-url");
const issueInput = document.getElementById("issue-number");
const analyzeBtn = document.getElementById("analyze-btn");
const sampleBtn = document.getElementById("sample-btn");
const resultsSection = document.getElementById("results-section");
const resultsContent = document.getElementById("results-content");
const rawJsonBlock = document.getElementById("raw-json-block");
const copyJsonBtn = document.getElementById("copy-json-btn");

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.textContent = isLoading ? "Analyzing..." : "Analyze Issue";
}

function showResults(data) {
  resultsSection.classList.remove("hidden");

  const labelsHtml = (data.suggested_labels || [])
    .map((l) => `<span class="pill">${l}</span>`)
    .join(" ");

  const html = `
    <div class="result-field">
      <span class="label">Summary</span>
      <p>${data.summary || "-"}</p>
    </div>

    <div class="result-two-column">
      <div class="result-field">
        <span class="label">Type</span>
        <p><code>${data.type}</code></p>
      </div>
      <div class="result-field">
        <span class="label">Priority</span>
        <p>${data.priority_score || "-"}</p>
      </div>
    </div>

    <div class="result-field">
      <span class="label">Suggested Labels</span>
      <p>${labelsHtml || "-"}</p>
    </div>

    <div class="result-field">
      <span class="label">Potential Impact</span>
      <p>${data.potential_impact || "-"}</p>
    </div>
  `;

  resultsContent.innerHTML = html;
  rawJsonBlock.textContent = JSON.stringify(data, null, 2);
}

function showError(message) {
  resultsSection.classList.remove("hidden");
  resultsContent.innerHTML = `
    <div class="error-box">
      <strong>Oops.</strong> ${message}
    </div>
  `;
  rawJsonBlock.textContent = "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const repoUrl = repoInput.value.trim();
  const issueNumber = Number(issueInput.value);

  if (!repoUrl || !issueNumber) {
    showError("Please provide both a repository URL and an issue number.");
    return;
  }

  setLoading(true);
  showError("Working on it...");

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze_issue`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        repo_url: repoUrl,
        issue_number: issueNumber,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      showError(data.detail || "Unknown error from backend.");
      return;
    }

    showResults(data);
  } catch (error) {
    console.error(error);
    showError("Failed to reach backend. Is the FastAPI server running on port 8000?");
  } finally {
    setLoading(false);
  }
});

sampleBtn.addEventListener("click", () => {
  repoInput.value = "https://github.com/facebook/react";
  issueInput.value = "30000";
});

copyJsonBtn.addEventListener("click", async () => {
  const text = rawJsonBlock.textContent.trim();
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    copyJsonBtn.textContent = "Copied!";
    setTimeout(() => {
      copyJsonBtn.textContent = "Copy JSON";
    }, 1200);
  } catch (error) {
    console.error(error);
    alert("Could not copy to clipboard. You can select the text manually.");
  }
});
