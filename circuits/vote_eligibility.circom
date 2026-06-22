pragma circom 2.1.6;

include "../node_modules/circomlib/circuits/poseidon.circom";

template SelectMerklePair() {
    signal input current_hash;
    signal input sibling_hash;
    signal input path_index;

    signal output left;
    signal output right;

    path_index * (path_index - 1) === 0;

    left <== current_hash + path_index * (sibling_hash - current_hash);
    right <== sibling_hash + path_index * (current_hash - sibling_hash);
}

template VoteEligibility(depth) {
    signal input token_secret;
    signal input merkle_siblings[depth];
    signal input merkle_path_indices[depth];

    signal input election_id;
    signal input merkle_root;

    signal output nullifier_hash;

    signal current_hash[depth + 1];

    component token_hasher = Poseidon(1);
    token_hasher.inputs[0] <== token_secret;
    current_hash[0] <== token_hasher.out;

    component nullifier_hasher = Poseidon(2);
    nullifier_hasher.inputs[0] <== token_secret;
    nullifier_hasher.inputs[1] <== election_id;
    nullifier_hash <== nullifier_hasher.out;

    component selectors[depth];
    component parent_hashers[depth];

    for (var level = 0; level < depth; level++) {
        selectors[level] = SelectMerklePair();
        selectors[level].current_hash <== current_hash[level];
        selectors[level].sibling_hash <== merkle_siblings[level];
        selectors[level].path_index <== merkle_path_indices[level];

        parent_hashers[level] = Poseidon(2);
        parent_hashers[level].inputs[0] <== selectors[level].left;
        parent_hashers[level].inputs[1] <== selectors[level].right;

        current_hash[level + 1] <== parent_hashers[level].out;
    }

    current_hash[depth] === merkle_root;
}

component main { public [election_id, merkle_root] } = VoteEligibility(10);
