from dataclasses import dataclass
from typing import Final

from app.zkp.poseidon import BN254_FIELD_MODULUS, poseidon_hash, poseidon_hash_batch


DEFAULT_TREE_DEPTH: Final[int] = 10
EMPTY_LEAF: Final[int] = 0


@dataclass(frozen=True)
class MerkleProof:
    siblings: list[int]
    path_indices: list[int]


class MerkleTreeError(ValueError):
    """Raised when Merkle tree operations cannot be completed."""


class MerkleTree:
    def __init__(
        self,
        leaves: list[int],
        depth: int = DEFAULT_TREE_DEPTH,
    ) -> None:
        if not leaves:
            raise MerkleTreeError("Cannot create a Merkle tree with no leaves.")

        if depth < 1:
            raise MerkleTreeError("Merkle tree depth must be at least 1.")

        capacity: int = 2**depth

        if len(leaves) > capacity:
            raise MerkleTreeError("Too many leaves for the given tree depth.")

        for leaf in leaves:
            _validate_field_element(leaf)

        self.depth: int = depth
        self.leaf_count: int = len(leaves)
        self.capacity: int = capacity
        self.levels: list[list[int]] = self._build_levels(leaves, capacity)

    @property
    def root(self) -> int:
        return self.levels[-1][0]

    def get_proof(self, leaf_index: int) -> MerkleProof:
        if leaf_index < 0 or leaf_index >= self.leaf_count:
            raise MerkleTreeError("Leaf index is out of bounds.")

        siblings: list[int] = []
        path_indices: list[int] = []
        current_index: int = leaf_index

        for level in self.levels[:-1]:
            sibling_index = current_index ^ 1
            siblings.append(level[sibling_index])
            path_indices.append(current_index % 2)
            current_index //= 2

        return MerkleProof(
            siblings=siblings,
            path_indices=path_indices,
        )

    @staticmethod
    def verify(
        leaf: int,
        proof: MerkleProof,
        expected_root: int,
    ) -> bool:
        _validate_field_element(leaf)
        _validate_field_element(expected_root)

        if len(proof.siblings) != len(proof.path_indices):
            raise MerkleTreeError(
                "Proof siblings and path indices must have the same length."
            )

        computed_hash: int = leaf

        for sibling, path_index in zip(
            proof.siblings,
            proof.path_indices,
            strict=True,
        ):
            _validate_field_element(sibling)
            _validate_path_index(path_index)

            if path_index == 0:
                computed_hash = poseidon_hash([computed_hash, sibling])
            else:
                computed_hash = poseidon_hash([sibling, computed_hash])

        return computed_hash == expected_root

    @staticmethod
    def _build_levels(
        leaves: list[int],
        capacity: int,
    ) -> list[list[int]]:
        current_level: list[int] = leaves + [EMPTY_LEAF] * (capacity - len(leaves))
        levels: list[list[int]] = [current_level]

        while len(current_level) > 1:
            pairs = [
                [current_level[index], current_level[index + 1]]
                for index in range(0, len(current_level), 2)
            ]

            current_level = poseidon_hash_batch(pairs)
            levels.append(current_level)

        return levels


def _validate_field_element(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MerkleTreeError("Value must be an integer.")

    if not 0 <= value < BN254_FIELD_MODULUS:
        raise MerkleTreeError("Value must belong to the BN254 field.")


def _validate_path_index(path_index: int) -> None:
    if isinstance(path_index, bool) or path_index not in (0, 1):
        raise MerkleTreeError("Invalid path index in proof. Must be 0 or 1.")
