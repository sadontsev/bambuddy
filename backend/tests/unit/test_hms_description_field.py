"""Tests for the `description` HMSErrorResponse carries alongside a fault's code.

The table has been in `hms_errors.py` all along and the status response has never exposed it,
so every client grew its own copy of the same sentences. These hold the two things that make
resolving it server-side safe: the key really is a `print_error` full_code split in half, and a
16-char `hms[]` full_code gets None rather than a truncation that would land on some other
error's text.
"""

from backend.app.schemas.printer import HMSErrorResponse
from backend.app.services.hms_errors import get_error_description


def _describe(full_code: str) -> str | None:
    """The rule as the status route applies it."""
    if len(full_code or "") != 8:
        return None
    return get_error_description(f"{full_code[:4]}_{full_code[4:]}")


def test_a_print_error_full_code_resolves():
    """0300_8003 and 0300_8004 are the two faults a user is most likely to be told about:
    the AI monitor spotting spaghetti, and running out of filament."""
    spaghetti = _describe("03008003")
    assert spaghetti is not None
    assert "spaghetti" in spaghetti.lower()

    runout = _describe("03008004")
    assert runout is not None
    assert "filament ran out" in runout.lower()


def test_a_sixteen_char_hms_code_resolves_to_nothing():
    """The `hms[]` family carries a 64-bit attr+code and has no entry in the table. Truncating
    it to eight characters would produce a key that hits an unrelated error's sentence, which is
    worse than saying nothing — this code was live on an H2C while the field was written."""
    assert _describe("050002000003000A") is None


def test_an_empty_or_missing_full_code_resolves_to_nothing():
    assert _describe("") is None
    assert _describe("0300") is None


def test_the_field_defaults_to_none_so_the_shape_is_unchanged_for_old_clients():
    """A client that has never seen this field keeps working, and a fault with no entry is
    reported exactly as it was before."""
    err = HMSErrorResponse(code="0x3000a", module=5, severity=2)
    assert err.description is None


def test_the_field_carries_the_sentence_when_set():
    err = HMSErrorResponse(
        code="0x8003",
        attr=0x03000000,
        module=3,
        severity=2,
        full_code="03008003",
        description=_describe("03008003"),
    )
    assert err.description is not None
    assert "spaghetti" in err.description.lower()
