# Lab 6 — Code and Branch Coverage

Coverage-analysis deliverables for Software Engineering Lab 6: the assigned `loan_eligibility.py`
was tested with `pytest` and `coverage`, first for statement (code) coverage and then for branch
coverage.

**Student:** Mohammed Rizwan Shaikh — PES1UG24CS272
**Source repository:** [`SETAPESU26/L6_L7_26_loan_eligibility`](https://github.com/SETAPESU26/L6_L7_26_loan_eligibility)

## Result

| Run | Test file | Statements | Branches | Coverage |
|-----|-----------|-----------|----------|----------|
| Code coverage | `CodeCoverageTest_PES1UG24CS272_loan_eligibility.py` | 33 (2 missed) | — | **94 %** |
| Branch coverage | `BranchCoverageTest_PES1UG24CS272_loan_eligibility.py` | 33 (0 missed) | 24, 0 partial | **100 %** |

## Files

| File | Description |
|------|-------------|
| [`deliverables/loan_eligibility.py`](deliverables/loan_eligibility.py) | Module under test (unmodified) |
| [`deliverables/CodeCoverageTest_PES1UG24CS272_loan_eligibility.py`](deliverables/CodeCoverageTest_PES1UG24CS272_loan_eligibility.py) | Code coverage tests — 15 cases, 94 % statements |
| [`deliverables/BranchCoverageTest_PES1UG24CS272_loan_eligibility.py`](deliverables/BranchCoverageTest_PES1UG24CS272_loan_eligibility.py) | Branch coverage tests — 24 cases, 100 % statements and branches |
| [`deliverables/screenshots/code_coverage_PES1UG24CS272.png`](deliverables/screenshots/code_coverage_PES1UG24CS272.png) | `coverage report -m` after ≥ 90 % code coverage |
| [`deliverables/screenshots/branch_coverage_PES1UG24CS272.png`](deliverables/screenshots/branch_coverage_PES1UG24CS272.png) | `coverage report -m` after ≥ 90 % branch coverage |

## Line coverage vs branch coverage

The code coverage run executes every statement except the two interest-rate adjustments
(self-employment `+1`, collateral `-2`), which leaves 2 of 33 statements and 2 of 24 branches
untested — 94 %.

The branch coverage run adds boundary values (score 300/900, ages 21/60, income exactly at the
25000 and 40000 minimums, a fair-band applicant) and the two missing decisions, so every `if` and
`elif` is taken in both directions. That is why the first file can show 94 % while the second shows
100 %: statement coverage only asks whether a line ran, branch coverage asks whether each decision
went both ways.

## Reproduce

```bash
pip install coverage pytest

cd deliverables

# code coverage
coverage run --include=loan_eligibility.py -m pytest -q CodeCoverageTest_PES1UG24CS272_loan_eligibility.py
coverage report -m

# branch coverage
coverage run --branch --include=loan_eligibility.py -m pytest -q BranchCoverageTest_PES1UG24CS272_loan_eligibility.py
coverage report -m
```
