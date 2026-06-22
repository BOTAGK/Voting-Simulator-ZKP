from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETUP_ZKP_SCRIPT = PROJECT_ROOT / "scripts" / "setup_zkp.sh"


def read_setup_zkp_script() -> str:
    return SETUP_ZKP_SCRIPT.read_text(encoding="utf-8")


def test_setup_zkp_script_uses_public_ptau_with_b2sum_check() -> None:
    script = read_setup_zkp_script()

    assert "powersOfTau28_hez_final_14.ptau" in script
    assert "https://storage.googleapis.com/zkevm/ptau/" in script
    assert "b2sum" in script
    assert "PTAU_BLAKE2B" in script
    assert "Invalid Powers of Tau BLAKE2b hash." in script


def test_setup_zkp_cleanup_preserves_gitkeep_and_cached_ptau() -> None:
    script = read_setup_zkp_script()

    assert 'find "$ARTIFACTS_DIR"' in script
    assert '! -name ".gitkeep"' in script
    assert '! -name "$PTAU_FILENAME"' in script


def test_setup_zkp_full_ptau_verification_is_opt_in() -> None:
    script = read_setup_zkp_script()

    assert 'VERIFY_PTAU_TRANSCRIPT="${VERIFY_PTAU_TRANSCRIPT:-0}"' in script
    assert 'if [[ "$VERIFY_PTAU_TRANSCRIPT" == "1" ]]' in script
    assert "Skipping full Powers of Tau transcript verification." in script


def test_setup_zkp_generates_required_snarkjs_artifacts() -> None:
    script = read_setup_zkp_script()

    assert "circom \"$CIRCUIT_PATH\"" in script
    assert "snarkjs groth16 setup" in script
    assert "snarkjs zkey contribute" in script
    assert "snarkjs zkey export verificationkey" in script
