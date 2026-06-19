"""Integration tests for the Python Poseidon adapter."""

import pytest

from app.zkp.poseidon import BN254_FIELD_MODULUS, poseidon_hash, poseidon_hash_batch


def test_poseidon_hash_returns_known_value() -> None:
    result = poseidon_hash([1, 2])

    assert result == (
        7853200120776062878684798364095072458815029376092732009249414926327459813530
    )


def test_poseidon_hash_batch_returns_known_values() -> None:
    results = poseidon_hash_batch([[1, 2], [123]])

    assert results == [
        7853200120776062878684798364095072458815029376092732009249414926327459813530,
        9904028930859697121695025471312564917337032846528014134060777877259199866166,
    ]


def test_poseidon_hash_batch_accepts_empty_batch() -> None:
    assert poseidon_hash_batch([]) == []


def test_poseidon_rejects_value_outside_field() -> None:
    with pytest.raises(ValueError, match="BN254 field"):
        poseidon_hash([BN254_FIELD_MODULUS])


def test_poseidon_rejects_bool_input() -> None:
    with pytest.raises(TypeError, match="integers"):
        poseidon_hash([True])


def test_poseidon_rejects_too_many_inputs() -> None:
    with pytest.raises(ValueError, match="1-16 inputs"):
        poseidon_hash(list(range(17)))
