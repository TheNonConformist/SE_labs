"""Code coverage tests for loan_eligibility.

Written for Lab 6: exercises every statement in the module so that line
coverage reaches at least 90%. Branch combinations that are not needed for
statement coverage are added in BranchCoverageTest_PES1UG24CS272_loan_eligibility.py.

Run with:
    coverage run --include=loan_eligibility.py -m pytest \
        CodeCoverageTest_PES1UG24CS272_loan_eligibility.py
    coverage report -m
"""

import pytest

from loan_eligibility import credit_band, interest_rate, is_eligible

# --- credit_band -----------------------------------------------------------


def test_credit_band_excellent():
    """A score in the top band is reported as excellent."""
    assert credit_band(800) == "excellent"


def test_credit_band_good():
    """A score in the second band is reported as good."""
    assert credit_band(650) == "good"


def test_credit_band_fair():
    """A score in the third band is reported as fair."""
    assert credit_band(550) == "fair"


def test_credit_band_poor():
    """A score in the bottom band is reported as poor."""
    assert credit_band(500) == "poor"


def test_credit_band_rejects_low_score():
    """A score below 300 is rejected."""
    with pytest.raises(ValueError):
        credit_band(299)


def test_credit_band_rejects_high_score():
    """A score above 900 is rejected."""
    with pytest.raises(ValueError):
        credit_band(901)


# --- is_eligible -----------------------------------------------------------


def test_is_eligible_true():
    """An adult with enough income and a good score is eligible."""
    assert is_eligible(30, 50000, "salaried", 800) is True


def test_is_eligible_rejects_underage():
    """An applicant younger than 21 is not eligible."""
    assert is_eligible(20, 50000, "salaried", 800) is False


def test_is_eligible_rejects_overage():
    """An applicant older than 60 is not eligible."""
    assert is_eligible(61, 50000, "salaried", 800) is False


def test_is_eligible_rejects_low_income():
    """Income below the employment minimum makes the applicant ineligible."""
    assert is_eligible(30, 24999, "salaried", 800) is False


def test_is_eligible_rejects_poor_credit():
    """A poor credit band makes the applicant ineligible."""
    assert is_eligible(30, 50000, "salaried", 500) is False


def test_is_eligible_rejects_unknown_employment():
    """An unknown employment type is rejected."""
    with pytest.raises(ValueError):
        is_eligible(30, 50000, "unemployed", 800)


# --- interest_rate ---------------------------------------------------------


def test_interest_rate_excellent_band():
    """An excellent score gets the lowest base rate."""
    assert interest_rate(800, "salaried", False) == 8


def test_interest_rate_good_band():
    """A good score gets the middle base rate."""
    assert interest_rate(700, "salaried", False) == 10


def test_interest_rate_fair_band():
    """A fair score gets the highest base rate."""
    assert interest_rate(600, "salaried", False) == 13
