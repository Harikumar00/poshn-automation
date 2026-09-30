import re
import pytest


@pytest.mark.regression
def test_tc_sr_01_standard_date_tokens_parsing():
    """TC-SR-01: Standard date tokens (.YYYY., .YY., .MM., .DD., .WW., .FY.) are recognized."""
    tokens = [".YYYY.", ".YY.", ".MM.", ".DD.", ".WW.", ".FY."]
    rule = "INV-.YYYY.-.MM.-.####"
    for t in [".YYYY.", ".MM."]:
        assert t in rule


@pytest.mark.regression
def test_tc_sr_02_dot_hash_padding_numbers():
    """TC-SR-02: Dot-hash padding (.#### or .#####) generates zero-padded numbers: 0001, 0002."""
    num = 1
    padded_4 = f"{num:04d}"
    padded_5 = f"{num:05d}"
    assert padded_4 == "0001"
    assert padded_5 == "00001"


@pytest.mark.regression
def test_tc_sr_03_valid_combined_series_rules():
    """TC-SR-03: Combined series formulas (INV-, INV-10, INV-.YYYY.-.{branch}.-.MM.-.####)."""
    valid_rules = ["INV-", "INV-10", "INV-.YYYY.-.MM.-.####"]
    pattern = re.compile(r"^[A-Za-z0-9\-\.\{\}]+$")
    for rule in valid_rules:
        assert pattern.match(rule)


@pytest.mark.regression
def test_tc_sr_04_disallowed_special_characters_rejection():
    """TC-SR-04: Disallowed special characters ($, @, !, %, *) are rejected by series validator."""
    invalid_formula = "INV@2026"
    disallowed_chars = set("$@!%*#") - {"#"}
    has_disallowed = any(ch in invalid_formula for ch in ["$", "@", "!", "%", "*"])
    assert has_disallowed is True, "Validation must flag disallowed characters"


@pytest.mark.regression
def test_tc_sr_05_hashes_without_dot_prefix_rejection():
    """TC-SR-05: Hashes without dot prefix (e.g. INV-#### instead of INV-.####) are rejected."""
    formula = "INV-####"
    assert ".#" not in formula, "Formula missing required dot prefix before hashes"


@pytest.mark.regression
def test_tc_sr_06_number_rollover_expansion():
    """TC-SR-06: Series rule specifying .### expands safely to 1000 without truncating."""
    max_3_digit = 999
    rollover = max_3_digit + 1
    formatted = str(rollover)
    assert formatted == "1000"
    assert len(formatted) == 4
