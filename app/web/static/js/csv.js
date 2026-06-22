const TOKEN_CSV_COLUMNS = [
  "election_id",
  "token_secret",
  "merkle_root",
  "merkle_index",
  "merkle_siblings",
  "merkle_path_indices",
];

function escapeCsvValue(value) {
  const text = value === null || value === undefined ? "" : String(value);
  const needsQuotes =
    text.includes(";") ||
    text.includes('"') ||
    text.includes("\n") ||
    text.includes("\r");

  if (!needsQuotes) {
    return text;
  }

  const escapedText = text.replaceAll('"', '""');
  return `"${escapedText}"`;
}

export function buildVoterTokenPackagesCsv(packages) {
  const rows = [TOKEN_CSV_COLUMNS.join(";")];

  for (const packageData of packages) {
    const row = [
      packageData.election_id,
      packageData.token_secret,
      packageData.merkle_root,
      packageData.merkle_index,
      JSON.stringify(packageData.merkle_proof.siblings),
      JSON.stringify(packageData.merkle_proof.path_indices),
    ];

    rows.push(row.map(escapeCsvValue).join(";"));
  }

  return `${rows.join("\n")}\n`;
}
