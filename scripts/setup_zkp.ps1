$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ArtifactsDir = Join-Path $ProjectRoot "zkp_artifacts"
$CircuitPath = Join-Path $ProjectRoot "circuits\vote_eligibility.circom"

$CircuitName = "vote_eligibility"
$PtauFilename = "powersOfTau28_hez_final_14.ptau"
$PtauFinal = Join-Path $ArtifactsDir $PtauFilename
$PtauUrl = if ($env:PTAU_URL) {
    $env:PTAU_URL
} else {
    "https://storage.googleapis.com/zkevm/ptau/$PtauFilename"
}
$InitialZkey = Join-Path $ArtifactsDir "$CircuitName`_0000.zkey"
$FinalZkey = Join-Path $ArtifactsDir "$CircuitName`_final.zkey"
$VerificationKey = Join-Path $ArtifactsDir "verification_key.json"
$VerifyPtauTranscript = $env:VERIFY_PTAU_TRANSCRIPT -eq "1"

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. Install it and try again."
    }
}

function Run-Step {
    param(
        [string]$Message,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Message"
    & $Command
}

function Ensure-PublicPtau {
    if (Test-Path $PtauFinal) {
        Write-Host "Using cached public Powers of Tau file: $PtauFinal"
    } else {
        Run-Step "Downloading public Powers of Tau file" {
            Invoke-WebRequest -Uri $PtauUrl -OutFile $PtauFinal
        }
    }
}

Require-Command "node"
Require-Command "npm"
Require-Command "npx"
Require-Command "circom"

Run-Step "Preparing zkp_artifacts directory" {
    if (Test-Path $ArtifactsDir) {
        Get-ChildItem -Path $ArtifactsDir -Force |
            Where-Object { $_.Name -ne ".gitkeep" -and $_.Name -ne $PtauFilename } |
            Remove-Item -Recurse -Force
    } else {
        New-Item -ItemType Directory -Path $ArtifactsDir | Out-Null
    }
}

Ensure-PublicPtau

if ($VerifyPtauTranscript) {
    Run-Step "Verifying public Powers of Tau transcript" {
        npx snarkjs powersoftau verify $PtauFinal
    }
} else {
    Write-Host "Skipping full Powers of Tau transcript verification."
    Write-Host "Set VERIFY_PTAU_TRANSCRIPT=1 to run snarkjs powersoftau verify."
}

Run-Step "Compiling Circom circuit" {
    circom $CircuitPath `
        --r1cs `
        --wasm `
        --sym `
        -o $ArtifactsDir
}

Run-Step "Running Groth16 setup" {
    npx snarkjs groth16 setup `
        (Join-Path $ArtifactsDir "$CircuitName.r1cs") `
        $PtauFinal `
        $InitialZkey
}

Run-Step "Contributing to final zkey" {
    npx snarkjs zkey contribute `
        $InitialZkey `
        $FinalZkey `
        --name="Voting Simulator final contribution" `
        -v `
        -e="local final entropy for voting simulator"
}

Run-Step "Exporting verification key" {
    npx snarkjs zkey export verificationkey `
        $FinalZkey `
        $VerificationKey
}

Write-Host ""
Write-Host "ZKP setup completed."
Write-Host "Generated artifacts:"
Write-Host " - $FinalZkey"
Write-Host " - $VerificationKey"
Write-Host " - $(Join-Path $ArtifactsDir "$CircuitName`_js\$CircuitName.wasm")"
Write-Host " - $(Join-Path $ArtifactsDir "$CircuitName`_js\generate_witness.js")"
