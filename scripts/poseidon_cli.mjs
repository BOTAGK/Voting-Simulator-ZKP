import { buildPoseidon } from "circomlibjs";

const FIELD_MODULUS =
  21888242871839275222246405745257275088548364400416034343698204186575808495617n;

function parseFieldElement(value) {
  if (typeof value !== "string" || !/^\d+$/.test(value)) {
    throw new Error("Poseidon inputs must be decimal strings.");
  }

  const fieldElement = BigInt(value);

  if (fieldElement >= FIELD_MODULUS) {
    throw new Error("Poseidon input is outside the BN254 field.");
  }

  return fieldElement;
}

async function readInput() {
  let input = "";

  for await (const chunk of process.stdin) {
    input += chunk;
  }

  return input;
}

async function main() {
  const rawInput = await readInput();
  const batches = JSON.parse(rawInput);

  if (!Array.isArray(batches)) {
    throw new Error("Input must be an array of Poseidon input arrays.");
  }

  const poseidon = await buildPoseidon();

  const results = batches.map((values) => {
    if (!Array.isArray(values) || values.length < 1 || values.length > 16) {
      throw new Error("Each Poseidon operation requires 1-16 inputs.");
    }

    const fieldElements = values.map(parseFieldElement);
    const result = poseidon(fieldElements);

    return poseidon.F.toObject(result).toString();
  });

  process.stdout.write(JSON.stringify(results));
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});