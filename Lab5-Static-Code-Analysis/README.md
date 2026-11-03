# Lab 5 — Static Code Analysis

Static-analysis deliverables for Software Engineering Lab 5: the assigned Python script was
analysed with Pylint, Bandit and Flake8, the findings were documented, and the issues were fixed
until all three tools reported clean.

**Student:** Mohammed Rizwan Shaikh — PES1UG24CS272
**Source repository:** [`SETAPESU26/L5_26_dairy_collection`](https://github.com/SETAPESU26/L5_26_dairy_collection)

## Result

| Tool | Before | After |
|------|--------|-------|
| Pylint | 2.00/10 (24 messages) | **10.00/10** (0 messages) |
| Bandit | 2 High, 1 Medium | **0 issues** |
| Flake8 | 7 issues | **0 issues** |

## Files

| File | Description |
|------|-------------|
| [`deliverables/dairy_collection.py`](deliverables/dairy_collection.py) | Cleaned version with all documented issues fixed |
| [`deliverables/issues.md`](deliverables/issues.md) | Issue table: type, line(s), description and fix for each finding |
| [`deliverables/reflection.md`](deliverables/reflection.md) | Answers to the four reflection questions |
| [`deliverables/reports/before/pylint_report.txt`](deliverables/reports/before/pylint_report.txt) | Pylint report on the original script |
| [`deliverables/reports/before/bandit_report.txt`](deliverables/reports/before/bandit_report.txt) | Bandit report on the original script |
| [`deliverables/reports/before/flake8_report.txt`](deliverables/reports/before/flake8_report.txt) | Flake8 report on the original script |
| [`deliverables/reports/after/pylint_report.txt`](deliverables/reports/after/pylint_report.txt) | Pylint report after the fixes (10.00/10) |
| [`deliverables/reports/after/bandit_report.txt`](deliverables/reports/after/bandit_report.txt) | Bandit report after the fixes (0 issues) |
| [`deliverables/reports/after/flake8_report.txt`](deliverables/reports/after/flake8_report.txt) | Flake8 report after the fixes (empty = clean) |

## Issues fixed

1. **SQL injection (Bandit B608)** — the `INSERT` was built with `.format()`; now uses `?` placeholders.
2. **Weak hash (Bandit B324)** — MD5 replaced with SHA-256 for farmer tokens.
3. **Shell injection (Bandit B605)** — `os.system("echo " + farmer)` replaced with a direct `print`.
4. **`fat == None`** — changed to `is None` (Pylint C0121 / Flake8 E711).
5. **Global connection shadowed** — module-level `conn` removed; `main()` owns the connection.
6. **Style** — `snake_case` names, docstrings, wrapped long lines, unused imports removed, `main()` guarded.

## Reproduce

```bash
python3 -m venv venv && source venv/bin/activate
pip install pylint bandit flake8

cd deliverables
python dairy_collection.py
pylint dairy_collection.py
bandit -r dairy_collection.py
flake8 dairy_collection.py
```

Expected: `10.00/10`, zero Bandit findings, no Flake8 output.
