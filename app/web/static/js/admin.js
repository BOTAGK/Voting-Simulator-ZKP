import {
  downloadTextFile,
  readJsonResponse,
  setElementMessage,
  setMessage,
  toApiDateTime,
  toLocalDateTimeInput,
} from "./shared.js";
import { fetchAdminJson, fetchAdminText } from "./admin-api.js";
import { buildVoterTokenPackagesCsv } from "./csv.js";

let generatedAdminTokenPackages = [];

function getAdminElectionPanel() {
  return document.querySelector("#admin-election-panel");
}

function getSelectedAdminElectionId() {
  const panel = getAdminElectionPanel();
  return panel ? panel.dataset.electionId : null;
}

function setAdminElectionMessage(text, type) {
  setElementMessage(
    document.querySelector("#admin-election-message"),
    text,
    type,
  );
}

function buildElectionPayloadFromForm(form) {
  const formData = new FormData(form);

  return {
    name: formData.get("name"),
    description: formData.get("description") || null,
    starts_at: toApiDateTime(formData.get("starts_at")),
    ends_at: toApiDateTime(formData.get("ends_at")),
  };
}

function fillElectionUpdateForm(election) {
  const form = document.querySelector("#admin-election-update-form");

  if (!form) {
    return;
  }

  form.elements.name.value = election.name || "";
  form.elements.description.value = election.description || "";
  form.elements.starts_at.value = toLocalDateTimeInput(election.starts_at);
  form.elements.ends_at.value = toLocalDateTimeInput(election.ends_at);
  form.hidden = election.status !== "draft";
}

function updateAdminElectionRow(election) {
  const row = document.querySelector(`[data-election-row="${election.id}"]`);

  if (!row) {
    return;
  }

  row.children[0].textContent = election.name;
  row.children[1].innerHTML = `<span class="status-pill">${election.status}</span>`;
  row.children[2].textContent = election.starts_at || "not set";
  row.children[3].textContent = election.ends_at || "not set";
}

function updateAdminActionStates(status) {
  const panel = getAdminElectionPanel();

  if (!panel) {
    return;
  }

  const isDraft = status === "draft";
  const isActive = status === "active";

  panel.querySelector('[data-admin-action="open-election"]').disabled = !isDraft;
  panel.querySelector('[data-admin-action="close-election"]').disabled = !isActive;
  panel.querySelector('[data-admin-action="delete-election"]').disabled = false;

  const cancelButton = panel.querySelector('[data-admin-action="cancel-election"]');
  const candidateForm = document.querySelector("#admin-candidate-form");
  const candidateImportForm = document.querySelector("#admin-candidate-import-form");
  const tokenSection = document.querySelector("#admin-token-section");
  const tokenForm = document.querySelector("#admin-token-form");
  const tokenOutput = document.querySelector("#admin-token-output");

  if (cancelButton) {
    cancelButton.hidden = !isDraft;
  }

  if (candidateForm) {
    candidateForm.hidden = !isDraft;
  }

  if (candidateImportForm) {
    candidateImportForm.hidden = !isDraft;
  }

  if (tokenSection) {
    tokenSection.hidden = !isDraft;
  }

  if (tokenForm) {
    tokenForm.hidden = !isDraft;
  }

  if (tokenOutput) {
    tokenOutput.hidden = !isDraft;

    if (!isDraft) {
      tokenOutput.value = "";
    }
  }
}

function renderAdminElection(election) {
  const panel = getAdminElectionPanel();

  if (!panel) {
    return;
  }

  panel.hidden = false;
  panel.dataset.electionId = String(election.id);
  panel.querySelector("[data-admin-election-name]").textContent = election.name;
  panel.querySelector("[data-admin-election-description]").textContent =
    election.description || "No description.";
  panel.querySelector("[data-admin-election-status]").textContent = election.status;
  fillElectionUpdateForm(election);
  updateAdminActionStates(election.status);
  updateAdminElectionRow(election);
}

function renderAdminCandidates(candidates) {
  const container = document.querySelector("#admin-candidate-list");

  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (candidates.length === 0) {
    const emptyState = document.createElement("p");
    emptyState.className = "muted";
    emptyState.textContent = "No candidates.";
    container.appendChild(emptyState);
    return;
  }

  for (const candidate of candidates) {
    const row = document.createElement("div");
    row.className = "candidate-row";

    const content = document.createElement("span");
    const name = document.createElement("strong");
    const description = document.createElement("small");
    const deleteButton = document.createElement("button");

    name.textContent = candidate.name;
    description.textContent = candidate.description || "No description.";
    content.append(name, description);

    deleteButton.className = "button ghost compact";
    deleteButton.type = "button";
    deleteButton.dataset.adminAction = "delete-candidate";
    deleteButton.dataset.candidateId = String(candidate.id);
    deleteButton.textContent = "Delete";

    row.append(content, deleteButton);
    container.appendChild(row);
  }
}

async function loadAdminCandidates(electionId) {
  const candidates = await fetchAdminJson(
    `/api/admin/elections/${electionId}/candidates`,
  );
  renderAdminCandidates(candidates);
}

function renderAdminResults(results) {
  const panel = document.querySelector("#admin-results-panel");

  if (!panel) {
    return;
  }

  const turnoutPercent = (results.turnout * 100).toFixed(2);
  const rows = results.results
    .map(
      (result) => `
        <tr>
          <td>${result.candidate_name}</td>
          <td>${result.votes}</td>
        </tr>
      `,
    )
    .join("");

  panel.className = "";
  panel.innerHTML = `
    <div class="stats-row">
      <div><span class="metric">${results.total_votes}</span><span class="muted">Votes</span></div>
      <div><span class="metric">${results.total_tokens}</span><span class="muted">Tokens</span></div>
      <div><span class="metric">${turnoutPercent}%</span><span class="muted">Turnout</span></div>
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Candidate</th>
          <th>Votes</th>
        </tr>
      </thead>
      <tbody>${rows || '<tr><td colspan="2">No votes.</td></tr>'}</tbody>
    </table>
  `;
}

function resetAdminResultsPanel() {
  const panel = document.querySelector("#admin-results-panel");

  if (!panel) {
    return;
  }

  panel.className = "empty-state";
  panel.textContent = 'Select "Results" to load election results.';
}

function resetAdminTokenOutput() {
  const output = document.querySelector("#admin-token-output");

  generatedAdminTokenPackages = [];

  if (!output) {
    return;
  }

  output.value = "";
}

async function loadAdminElection(electionId) {
  setAdminElectionMessage("Loading election...", "");
  const election = await fetchAdminJson(`/api/admin/elections/${electionId}`);

  renderAdminElection(election);
  resetAdminResultsPanel();
  resetAdminTokenOutput();
  await loadAdminCandidates(electionId);
  setAdminElectionMessage("Election loaded.", "success");
}

function buildTokenGeneratePayload(form) {
  const formData = new FormData(form);

  return {
    count: Number(formData.get("count")),
    label_prefix: formData.get("label_prefix") || null,
  };
}

async function generateAdminTokensJson(form) {
  const electionId = getSelectedAdminElectionId();

  if (!electionId) {
    return;
  }

  setMessage(form, "Generating tokens...", "");
  const packages = await fetchAdminJson(
    `/api/admin/elections/${electionId}/tokens/generate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildTokenGeneratePayload(form)),
    },
  );
  generatedAdminTokenPackages = packages;
  const jsonContent = JSON.stringify(packages, null, 2);
  const output = document.querySelector("#admin-token-output");

  if (output) {
    output.value = jsonContent;
  }

  downloadTextFile(
    `election-${electionId}-voter-tokens.json`,
    jsonContent,
    "application/json",
  );
  setMessage(
    form,
    "Tokens generated. JSON downloaded, and CSV can be downloaded without generating again.",
    "success",
  );
}

async function generateAdminTokensCsv() {
  const electionId = getSelectedAdminElectionId();
  const form = document.querySelector("#admin-token-form");

  if (!electionId || !form) {
    return;
  }

  if (generatedAdminTokenPackages.length === 0) {
    setMessage(
      form,
      "Generate tokens first. CSV is exported from the same package set without a second generation.",
      "error",
    );
    return;
  }

  const csvContent = buildVoterTokenPackagesCsv(generatedAdminTokenPackages);

  downloadTextFile(
    `election-${electionId}-voter-tokens.csv`,
    csvContent,
    "text/csv",
  );
  setMessage(form, "Tokens downloaded as CSV.", "success");
}

async function downloadAdminResultsCsv() {
  const electionId = getSelectedAdminElectionId();

  if (!electionId) {
    return;
  }

  const csvContent = await fetchAdminText(
    `/api/admin/elections/${electionId}/results/csv`,
  );
  downloadTextFile(
    `election-${electionId}-results.csv`,
    csvContent,
    "text/csv",
  );
}

async function setupAdminDashboardAction(action, button) {
  const selectedElectionId = getSelectedAdminElectionId();
  const electionId = button.dataset.electionId || selectedElectionId;

  if (!electionId && action !== "generate-tokens-csv") {
    return;
  }

  if (action === "select-election") {
    await loadAdminElection(electionId);
    return;
  }

  if (action === "open-election" || action === "close-election") {
    const command = action === "open-election" ? "open" : "close";
    const election = await fetchAdminJson(
      `/api/admin/elections/${electionId}/${command}`,
      { method: "POST" },
    );
    renderAdminElection(election);
    setAdminElectionMessage("Election status updated.", "success");
    return;
  }

  if (action === "cancel-election") {
    if (!confirm("Cancel this election and mark it as closed?")) {
      return;
    }

    const election = await fetchAdminJson(
      `/api/admin/elections/${electionId}/cancel`,
      { method: "POST" },
    );
    renderAdminElection(election);
    resetAdminResultsPanel();
    resetAdminTokenOutput();
    setAdminElectionMessage("Election cancelled.", "success");
    return;
  }

  if (action === "delete-election") {
    if (!confirm("Delete the selected election?")) {
      return;
    }

    await fetchAdminText(
      `/api/admin/elections/${electionId}`,
      { method: "DELETE" },
    );
    window.location.reload();
    return;
  }

  if (action === "delete-candidate") {
    await fetchAdminText(
      `/api/admin/elections/${electionId}/candidates/${button.dataset.candidateId}`,
      { method: "DELETE" },
    );
    await loadAdminCandidates(electionId);
    setAdminElectionMessage("Candidate deleted.", "success");
    return;
  }

  if (action === "load-results") {
    const results = await fetchAdminJson(
      `/api/admin/elections/${electionId}/results`,
    );
    renderAdminResults(results);
    return;
  }

  if (action === "download-results-csv") {
    await downloadAdminResultsCsv();
    return;
  }

  if (action === "generate-tokens-csv") {
    await generateAdminTokensCsv();
  }
}

export function setupAdminLogin() {
  const form = document.querySelector("#admin-login-form");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(form, "Logging in...", "");

    const formData = new FormData(form);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });
    const data = await readJsonResponse(response);

    if (!response.ok) {
      setMessage(form, data.detail || "Login failed.", "error");
      return;
    }

    window.location.href = "/admin";
  });
}

export function setupAdminLogout() {
  const button = document.querySelector("#admin-logout-button");

  if (!button) {
    return;
  }

  button.addEventListener("click", async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
      });
    } finally {
      window.location.href = "/admin/login";
    }
  });
}

export function setupCreateElection() {
  const form = document.querySelector("#create-election-form");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(form, "Creating...", "");

    const response = await fetch("/api/admin/elections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildElectionPayloadFromForm(form)),
    });
    const data = await readJsonResponse(response);

    if (!response.ok) {
      setMessage(form, data.detail || "Could not create election.", "error");
      return;
    }

    setMessage(form, "Election created.", "success");
    window.location.reload();
  });
}

export function setupAdminDashboard() {
  const panel = getAdminElectionPanel();

  if (!panel) {
    return;
  }

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-admin-action]");

    if (!button) {
      return;
    }

    try {
      await setupAdminDashboardAction(button.dataset.adminAction, button);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Operation failed.";
      setAdminElectionMessage(message, "error");
    }
  });

  const updateForm = document.querySelector("#admin-election-update-form");
  const candidateForm = document.querySelector("#admin-candidate-form");
  const importForm = document.querySelector("#admin-candidate-import-form");
  const tokenForm = document.querySelector("#admin-token-form");

  if (updateForm) {
    updateForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      try {
        const election = await fetchAdminJson(
          `/api/admin/elections/${getSelectedAdminElectionId()}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildElectionPayloadFromForm(updateForm)),
          },
        );
        renderAdminElection(election);
        setMessage(updateForm, "Changes saved.", "success");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Could not save changes.";
        setMessage(updateForm, message, "error");
      }
    });
  }

  if (candidateForm) {
    candidateForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      try {
        const electionId = getSelectedAdminElectionId();
        const formData = new FormData(candidateForm);
        await fetchAdminJson(`/api/admin/elections/${electionId}/candidates`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: formData.get("name"),
            description: formData.get("description") || null,
          }),
        });
        candidateForm.reset();
        await loadAdminCandidates(electionId);
        setMessage(candidateForm, "Candidate added.", "success");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Could not add candidate.";
        setMessage(candidateForm, message, "error");
      }
    });
  }

  if (importForm) {
    importForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      try {
        const electionId = getSelectedAdminElectionId();
        const formData = new FormData(importForm);
        await fetchAdminJson(
          `/api/admin/elections/${electionId}/candidates/import`,
          {
            method: "POST",
            body: formData,
          },
        );
        importForm.reset();
        await loadAdminCandidates(electionId);
        setMessage(importForm, "Candidates imported.", "success");
      } catch (error) {
        const message = error instanceof Error ? error.message : "CSV import failed.";
        setMessage(importForm, message, "error");
      }
    });
  }

  if (tokenForm) {
    tokenForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      try {
        await generateAdminTokensJson(tokenForm);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Could not generate tokens.";
        setMessage(tokenForm, message, "error");
      }
    });
  }
}
