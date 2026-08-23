"""Tests for main._format_hms_error_summary — the helper that turns MQTT hms_errors
into a human-readable PrintQueueItem.error_message on pre-print failures (#1111)."""


def _format(hms_errors):
    from backend.app.main import _format_hms_error_summary

    return _format_hms_error_summary(hms_errors)


def test_returns_none_for_empty_list():
    assert _format([]) is None
    assert _format(None or []) is None


def test_formats_known_nozzle_mismatch_code():
    """0500_4038 is the nozzle-size-mismatch code from the HMS table — the common
    trigger for issue #1111."""
    summary = _format([{"code": "0x4038", "attr": 0x05000000, "module": 0x5, "severity": 1}])
    assert summary is not None
    assert "0500_4038" in summary
    assert "nozzle diameter" in summary.lower()


def test_formats_unknown_code_as_bare_short_code():
    summary = _format([{"code": "0x9999", "attr": 0x99990000, "module": 0x99, "severity": 1}])
    assert summary == "[9999_9999]"


def test_joins_multiple_errors_with_semicolons():
    summary = _format(
        [
            {"code": "0x4038", "attr": 0x05000000, "module": 0x5, "severity": 1},
            {"code": "0x9999", "attr": 0x99990000, "module": 0x99, "severity": 1},
        ]
    )
    assert summary is not None
    assert "; " in summary
    assert summary.count("[") == 2


def test_tolerates_malformed_entry_and_skips_it():
    summary = _format(
        [
            {"code": "not-hex", "attr": "also-not-int"},
            {"code": "0x4038", "attr": 0x05000000, "module": 0x5, "severity": 1},
        ]
    )
    assert summary is not None
    assert "0500_4038" in summary


def test_all_malformed_returns_none():
    assert _format([{"code": "not-hex", "attr": "also-not-int"}]) is None


def test_an_error_number_wider_than_16_bits_is_masked():
    """`:04X` is a minimum width, so an unmasked wide code builds a ten-character key that can
    never match the table.

    Measured on a live H2C: code `0x3000a` with attr `0x05000000` produced `0500_3000A`, and the
    queue item's error_message degraded to a bare `[0500_3000A]`. The parser in bambu_mqtt.py
    masks both halves; this path masked only the module.
    """
    summary = _format([{"code": "0x3000a", "attr": 0x05000000, "module": 0x5, "severity": 2}])
    assert summary is not None
    assert "0500_3000A" not in summary, "the ten-character key is the bug"
    assert "0500_000A" in summary


def test_the_module_half_is_still_masked():
    """The half that was already correct stays correct."""
    summary = _format([{"code": "0x4038", "attr": 0xFFFF05000000 & 0xFFFFFFFF, "module": 0x5, "severity": 1}])
    assert summary is not None
    assert len(summary.split("]")[0].lstrip("[")) == 9
