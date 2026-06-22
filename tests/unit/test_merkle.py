"""Unit tests for Merkle tree logic."""

from collections.abc import Iterator

import pytest

import app.zkp.merkle as merkle
from app.zkp.merkle import (
    DEFAULT_TREE_DEPTH,
    MerkleProof,
    MerkleTree,
    MerkleTreeError,
)
from app.zkp.poseidon import BN254_FIELD_MODULUS


def fake_poseidon_hash(values: list[int]) -> int:
    if len(values) == 1:
        return values[0] + 100

    left, right = values
    return left * 1_009 + right * 917 + 17


def fake_poseidon_hash_batch(inputs: list[list[int]]) -> list[int]:
    return [fake_poseidon_hash(values) for values in inputs]


@pytest.fixture(autouse=True)
def use_fast_poseidon(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(merkle, "poseidon_hash", fake_poseidon_hash)
    monkeypatch.setattr(merkle, "poseidon_hash_batch", fake_poseidon_hash_batch)
    yield


def build_sample_leaves() -> list[int]:
    return [101, 202, 303, 404]


def test_merkle_tree_builds_root_for_inserted_leaves() -> None:
    leaves = build_sample_leaves()

    tree = MerkleTree(leaves, depth=3)

    assert tree.depth == 3
    assert tree.leaf_count == len(leaves)
    assert tree.capacity == 8
    assert len(tree.levels) == 4
    assert tree.root == tree.levels[-1][0]


def test_merkle_proof_verifies_for_each_inserted_leaf() -> None:
    leaves = build_sample_leaves()
    tree = MerkleTree(leaves, depth=3)

    for index, leaf in enumerate(leaves):
        proof = tree.get_proof(index)

        assert len(proof.siblings) == 3
        assert len(proof.path_indices) == 3
        assert MerkleTree.verify(leaf, proof, tree.root)


def test_merkle_proof_rejects_modified_leaf() -> None:
    leaves = build_sample_leaves()
    tree = MerkleTree(leaves, depth=3)
    proof = tree.get_proof(0)

    assert not MerkleTree.verify(leaves[1], proof, tree.root)


def test_merkle_tree_rejects_empty_leaves() -> None:
    with pytest.raises(MerkleTreeError, match="no leaves"):
        MerkleTree([], depth=3)


def test_merkle_tree_rejects_too_many_leaves_for_depth() -> None:
    with pytest.raises(MerkleTreeError, match="Too many leaves"):
        MerkleTree([1, 2, 3, 4, 5], depth=2)


def test_merkle_tree_rejects_leaf_outside_field() -> None:
    with pytest.raises(MerkleTreeError, match="BN254 field"):
        MerkleTree([BN254_FIELD_MODULUS], depth=1)


def test_merkle_tree_rejects_invalid_leaf_index() -> None:
    tree = MerkleTree(build_sample_leaves(), depth=3)

    with pytest.raises(MerkleTreeError, match="out of bounds"):
        tree.get_proof(4)


def test_merkle_verify_rejects_inconsistent_proof_lengths() -> None:
    leaves = build_sample_leaves()
    tree = MerkleTree(leaves, depth=3)
    proof = MerkleProof(
        siblings=tree.get_proof(0).siblings,
        path_indices=[0],
    )

    with pytest.raises(MerkleTreeError, match="same length"):
        MerkleTree.verify(leaves[0], proof, tree.root)


def test_merkle_verify_rejects_invalid_path_index() -> None:
    leaves = build_sample_leaves()
    tree = MerkleTree(leaves, depth=3)
    proof = MerkleProof(
        siblings=tree.get_proof(0).siblings,
        path_indices=[0, 1, 2],
    )

    with pytest.raises(MerkleTreeError, match="0 or 1"):
        MerkleTree.verify(leaves[0], proof, tree.root)


def test_default_tree_depth_matches_token_limit() -> None:
    assert DEFAULT_TREE_DEPTH == 10
    assert 2**DEFAULT_TREE_DEPTH == 1024
