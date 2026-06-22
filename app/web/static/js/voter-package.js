import { setMessage } from "./shared.js";

const VOTER_PACKAGE_STORAGE_KEY = "voter_package";

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requirePackageField(packageData, fieldName) {
  if (packageData[fieldName] === undefined || packageData[fieldName] === null) {
    throw new Error(`Missing field ${fieldName}.`);
  }
}

function validateVoterPackage(packageData) {
  if (!isPlainObject(packageData)) {
    throw new Error("Voter package must be a JSON object.");
  }

  requirePackageField(packageData, "election_id");
  requirePackageField(packageData, "token_secret");
  requirePackageField(packageData, "merkle_root");
  requirePackageField(packageData, "merkle_index");
  requirePackageField(packageData, "merkle_proof");

  if (!isPlainObject(packageData.merkle_proof)) {
    throw new Error("merkle_proof must be a JSON object.");
  }

  if (!Array.isArray(packageData.merkle_proof.siblings)) {
    throw new Error("merkle_proof.siblings must be a list.");
  }

  if (!Array.isArray(packageData.merkle_proof.path_indices)) {
    throw new Error("merkle_proof.path_indices must be a list.");
  }

  return packageData;
}

export function getStoredVoterPackage() {
  const rawPackage = sessionStorage.getItem(VOTER_PACKAGE_STORAGE_KEY);

  if (!rawPackage) {
    return null;
  }

  try {
    return validateVoterPackage(JSON.parse(rawPackage));
  } catch {
    sessionStorage.removeItem(VOTER_PACKAGE_STORAGE_KEY);
    return null;
  }
}

function setVoterClearButtonVisibility(isVisible) {
  const button = document.querySelector("#voter-clear-button");

  if (!button) {
    return;
  }

  button.hidden = !isVisible;
}

function renderVoterPackageStatus(packageData) {
  const statusPanel = document.querySelector("#voter-package-status");

  if (!statusPanel) {
    setVoterClearButtonVisibility(packageData !== null);
    return;
  }

  if (!packageData) {
    statusPanel.hidden = true;
    setVoterClearButtonVisibility(false);
    return;
  }

  const electionId = statusPanel.querySelector("[data-voter-election-id]");
  const tokenIndex = statusPanel.querySelector("[data-voter-token-index]");
  const votingLink = statusPanel.querySelector("#voter-start-voting-link");

  if (electionId) {
    electionId.textContent = String(packageData.election_id);
  }

  if (tokenIndex) {
    tokenIndex.textContent = String(packageData.merkle_index);
  }

  if (votingLink) {
    votingLink.href = `/elections/${packageData.election_id}`;
  }

  statusPanel.hidden = false;
  setVoterClearButtonVisibility(true);
}

function clearStoredVoterPackage() {
  sessionStorage.removeItem(VOTER_PACKAGE_STORAGE_KEY);
  renderVoterPackageStatus(null);
}

export function setupVoterPackageEntry() {
  const form = document.querySelector("#voter-package-form");
  const storedPackage = getStoredVoterPackage();

  renderVoterPackageStatus(storedPackage);

  if (!form) {
    return;
  }

  const fileInput = form.querySelector("#voter-package-file");
  const textarea = form.querySelector("#voter-package-json");
  const clearButton = document.querySelector("#voter-entry-clear-button");

  if (storedPackage && textarea) {
    textarea.value = JSON.stringify(storedPackage, null, 2);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(form, "Loading package...", "");

    let rawPackage = textarea ? textarea.value.trim() : "";
    const selectedFile = fileInput && fileInput.files ? fileInput.files[0] : null;

    if (selectedFile) {
      rawPackage = await selectedFile.text();
    }

    if (!rawPackage) {
      setMessage(form, "Paste JSON or choose a package file.", "error");
      return;
    }

    try {
      const packageData = validateVoterPackage(JSON.parse(rawPackage));
      sessionStorage.setItem(
        VOTER_PACKAGE_STORAGE_KEY,
        JSON.stringify(packageData),
      );

      if (textarea) {
        textarea.value = JSON.stringify(packageData, null, 2);
      }

      if (fileInput) {
        fileInput.value = "";
      }

      renderVoterPackageStatus(packageData);
      setMessage(form, "Voter package loaded.", "success");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid voter package.";
      setMessage(form, message, "error");
    }
  });

  if (clearButton) {
    clearButton.addEventListener("click", () => {
      clearStoredVoterPackage();

      if (textarea) {
        textarea.value = "";
      }

      if (fileInput) {
        fileInput.value = "";
      }

      setMessage(form, "Package removed from this browser.", "success");
    });
  }
}

export function setupVoterClearPackage() {
  const button = document.querySelector("#voter-clear-button");

  if (!button) {
    return;
  }

  button.hidden = getStoredVoterPackage() === null;

  button.addEventListener("click", () => {
    clearStoredVoterPackage();
    window.location.href = "/voter";
  });
}
