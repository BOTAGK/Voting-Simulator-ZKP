import { readJsonResponse, setMessage } from "./shared.js";
import { getStoredVoterPackage } from "./voter-package.js";

const VOTE_CIRCUIT_WASM_URL = "/zkp-artifacts/vote_eligibility.wasm";
const VOTE_CIRCUIT_ZKEY_URL = "/zkp-artifacts/vote_eligibility_final.zkey";

function buildVoteCircuitInput(voterPackage) {
  return {
    token_secret: String(voterPackage.token_secret),
    merkle_siblings: voterPackage.merkle_proof.siblings.map(String),
    merkle_path_indices: voterPackage.merkle_proof.path_indices.map(String),
    election_id: String(voterPackage.election_id),
    merkle_root: String(voterPackage.merkle_root),
  };
}

async function buildVotePayloadInBrowser(voterPackage, candidateId) {
  if (!window.snarkjs || !window.snarkjs.groth16) {
    throw new Error("The snarkjs library was not loaded.");
  }

  const circuitInput = buildVoteCircuitInput(voterPackage);
  const generatedProof = await window.snarkjs.groth16.fullProve(
    circuitInput,
    VOTE_CIRCUIT_WASM_URL,
    VOTE_CIRCUIT_ZKEY_URL,
  );
  const [nullifierHash, electionId, merkleRoot] =
    generatedProof.publicSignals.map(String);

  if (String(voterPackage.election_id) !== electionId) {
    throw new Error("Proof has an unexpected election ID.");
  }

  if (String(voterPackage.merkle_root) !== merkleRoot) {
    throw new Error("Proof has an unexpected Merkle root.");
  }

  return {
    candidate_id: Number(candidateId),
    nullifier_hash: nullifierHash,
    proof: generatedProof.proof,
    public_signals: {
      election_id: Number(electionId),
      merkle_root: merkleRoot,
      nullifier_hash: nullifierHash,
    },
  };
}

function formatVoteError(statusCode, data) {
  if (statusCode === 409) {
    return "This token has already been used in this election.";
  }

  if (statusCode === 404) {
    return "The election is not active or the candidate does not exist.";
  }

  if (statusCode === 503) {
    return "ZKP artifacts are unavailable. Run the ZKP setup.";
  }

  return data.detail || "Could not cast vote.";
}

export function setupVotePayload() {
  const form = document.querySelector("#vote-payload-form");

  if (!form) {
    return;
  }

  const electionId = form.dataset.electionId;
  const requiredPanel = document.querySelector("#vote-package-required");
  const voterPackage = getStoredVoterPackage();

  if (!voterPackage || String(voterPackage.election_id) !== String(electionId)) {
    form.hidden = true;

    if (requiredPanel) {
      requiredPanel.hidden = false;
    }

    return;
  }

  if (requiredPanel) {
    requiredPanel.hidden = true;
  }

  form.hidden = false;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(form, "", "");

    const selectedCandidate = document.querySelector('input[name="candidate_id"]:checked');

    if (!selectedCandidate) {
      setMessage(form, "Select a candidate before casting a vote.", "error");
      return;
    }

    setMessage(form, "Generating ZKP proof locally in the browser...", "");

    const submitButton = form.querySelector('button[type="submit"]');

    if (submitButton) {
      submitButton.disabled = true;
    }

    let payload;

    try {
      payload = await buildVotePayloadInBrowser(
        voterPackage,
        selectedCandidate.value,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not generate ZKP proof.";
      setMessage(form, message, "error");

      if (submitButton) {
        submitButton.disabled = false;
      }

      return;
    }

    setMessage(form, "Sending proof to the server...", "");

    const response = await fetch(`/api/elections/${electionId}/vote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await readJsonResponse(response);

    if (!response.ok) {
      setMessage(form, formatVoteError(response.status, data), "error");

      if (submitButton) {
        submitButton.disabled = false;
      }

      return;
    }

    setMessage(form, `Vote stored. ID: ${data.id}`, "success");

    for (const input of document.querySelectorAll('input[name="candidate_id"]')) {
      input.disabled = true;
    }
  });
}
