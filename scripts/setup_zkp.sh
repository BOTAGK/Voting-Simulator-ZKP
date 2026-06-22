#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${PROJECT_ROOT}/zkp_artifacts"
CIRCUIT_NAME="vote_eligibility"
CIRCUIT_PATH="${PROJECT_ROOT}/circuits/${CIRCUIT_NAME}.circom"

PTAU_FILENAME="powersOfTau28_hez_final_14.ptau"
PTAU_FINAL="${ARTIFACTS_DIR}/${PTAU_FILENAME}"
PTAU_URL="${PTAU_URL:-https://storage.googleapis.com/zkevm/ptau/${PTAU_FILENAME}}"
PTAU_BLAKE2B="${PTAU_BLAKE2B:-eeefbcf7c3803b523c94112023c7ff89558f9b8e0cf5d6cdcba3ade60f168af4a181c9c21774b94fbae6c90411995f7d854d02ebd93fb66043dbb06f17a831c1}"
VERIFY_PTAU_TRANSCRIPT="${VERIFY_PTAU_TRANSCRIPT:-0}"

INITIAL_ZKEY="${ARTIFACTS_DIR}/${CIRCUIT_NAME}_0000.zkey"
FINAL_ZKEY="${ARTIFACTS_DIR}/${CIRCUIT_NAME}_final.zkey"
VERIFICATION_KEY="${ARTIFACTS_DIR}/verification_key.json"

require_command() {
    local name="$1"

    if ! command -v "$name" >/dev/null 2>&1; then
        echo "Required command '${name}' was not found." >&2
        exit 1
    fi
}

run_step() {
    local message="$1"
    shift

    echo ""
    echo "==> ${message}"
    "$@"
}

download_public_ptau() {
    if [[ -f "$PTAU_FINAL" ]]; then
        echo "Using cached public Powers of Tau file: ${PTAU_FINAL}"
    else
        run_step "Downloading public Powers of Tau file" \
            curl --fail --location --output "$PTAU_FINAL" "$PTAU_URL"
    fi

    verify_ptau_hash
}

verify_ptau_hash() {
    local actual_hash
    actual_hash="$(b2sum "$PTAU_FINAL" | awk '{print $1}')"

    if [[ "$actual_hash" != "$PTAU_BLAKE2B" ]]; then
        echo "Invalid Powers of Tau BLAKE2b hash." >&2
        echo "Expected: ${PTAU_BLAKE2B}" >&2
        echo "Actual:   ${actual_hash}" >&2
        exit 1
    fi
}

require_command node
require_command npm
require_command snarkjs
require_command circom
require_command curl
require_command b2sum

echo "Using Circom: $(circom --version)"
echo "Using snarkjs: $(command -v snarkjs)"

run_step "Preparing zkp_artifacts directory" mkdir -p "$ARTIFACTS_DIR"
find "$ARTIFACTS_DIR" -mindepth 1 ! -name ".gitkeep" ! -name "$PTAU_FILENAME" -exec rm -rf {} +

download_public_ptau

if [[ "$VERIFY_PTAU_TRANSCRIPT" == "1" ]]; then
    run_step "Verifying public Powers of Tau transcript" \
        snarkjs powersoftau verify "$PTAU_FINAL"
else
    echo "Skipping full Powers of Tau transcript verification."
    echo "Set VERIFY_PTAU_TRANSCRIPT=1 to run snarkjs powersoftau verify."
fi

run_step "Compiling Circom circuit" \
    circom "$CIRCUIT_PATH" \
        --r1cs \
        --wasm \
        --sym \
        -o "$ARTIFACTS_DIR"

run_step "Running Groth16 setup" \
    snarkjs groth16 setup \
        "${ARTIFACTS_DIR}/${CIRCUIT_NAME}.r1cs" \
        "$PTAU_FINAL" \
        "$INITIAL_ZKEY"

run_step "Contributing to final zkey" \
    snarkjs zkey contribute \
        "$INITIAL_ZKEY" \
        "$FINAL_ZKEY" \
        --name="Voting Simulator final contribution" \
        -v \
        -e="local final entropy for voting simulator"

run_step "Exporting verification key" \
    snarkjs zkey export verificationkey \
        "$FINAL_ZKEY" \
        "$VERIFICATION_KEY"

echo ""
echo "ZKP setup completed."
echo "Generated artifacts:"
echo " - ${FINAL_ZKEY}"
echo " - ${VERIFICATION_KEY}"
echo " - ${ARTIFACTS_DIR}/${CIRCUIT_NAME}_js/${CIRCUIT_NAME}.wasm"
echo " - ${ARTIFACTS_DIR}/${CIRCUIT_NAME}_js/generate_witness.js"
