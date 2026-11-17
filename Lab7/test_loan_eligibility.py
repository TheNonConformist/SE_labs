from hypothesis import given, strategies as st
from loan_eligibility import parse_income, monthly_emi, pan_category


def run(call):
    """Return the result, or None if the function rejects the input with ValueError."""
    try:
        return call()
    except ValueError:
        return None


@given(st.text() | st.none())
def test_parse_income_no_crash(income):
    run(lambda: parse_income(income))


@given(st.integers(), st.integers(), st.integers())
def test_monthly_emi_no_crash(principal, rate, years):
    run(lambda: monthly_emi(f"{principal},{rate},{years}"))


@given(st.text() | st.none())
def test_pan_category_no_crash(pan):
    run(lambda: pan_category(pan))
