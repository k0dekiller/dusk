import pytest
from src.server.validator import *

@pytest.fixture
def validator() -> Validator:
    return Validator(r"[A-Z]{5}")

def test_match_true(validator: Validator) -> None:
    assert validator.match("ABCDE") == True

def test_match_false(validator: Validator) -> None:
    assert validator.match("abcd") == False

def test_check_success(validator: Validator) -> None:
    validator.check("ABCDE")

def test_check_fail(validator: Validator) -> None:
    with pytest.raises(NoMatchException):
        validator.check("abcd")

def test_call_true(validator: Validator) -> None:
    assert validator("ABCDE") == True

def test_call_false(validator: Validator) -> None:
    assert validator("abcd") == False

def test_repr(validator: Validator) -> None:
    assert repr(validator) == "'[A-Z]{5}'"