# Lab 5 — Static Code Analysis: Issue Log

**Student:** Mohammed Rizwan Shaikh (PES1UG24CS272)
**File analysed:** `dairy_collection.py`
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.5.0

## Baseline summary

| Tool | Before | After |
|------|--------|-------|
| Pylint | 2.00/10 (24 messages) | 10.00/10 (0 messages) |
| Bandit | 2 High, 1 Medium | 0 issues |
| Flake8 | 7 issues | 0 issues |

## Issues identified and fixed

| # | Issue | Type | Line(s) | Description | Fix Approach |
|---|-------|------|---------|-------------|--------------|
| 1 | SQL injection — B608 | Security (Medium) | 11 | `recordMilk` builds the INSERT with `.format()`, so a farmer name such as `x'); DROP TABLE milk;--` is executed as SQL. | Use a parameterised query: `VALUES (?, ?, ?, ?)` with the values passed as a tuple. |
| 2 | Weak hash — B324 (MD5) | Security (High) | 16 | `farmerToken` uses MD5, which is cryptographically broken, to derive a farmer token. | Replaced with SHA-256 (`hashlib.sha256`), which is collision resistant. |
| 3 | Shell injection — B605 (`os.system`) | Security (High) | 31 | `printSlip` concatenates the farmer name into `os.system("echo ...")`, so any shell metacharacters in the name are executed by the shell. | Removed the external process entirely and printed the slip directly, so no shell is involved. |
| 4 | Comparison to `None` — C0121 / E711 | Bug / Style | 36 | `fat == None` compares by value instead of identity and is always flagged; `NULL` rows must be compared with `is`. | Changed to `fat is None`. |
| 5 | Ambiguous variable name — E741 | Style | 26 | The variable `l` is easily confused with `1` and `I`. | Renamed to `best`. |
| 6 | Unused import — W0611 / F401 | Style | 2 (and `os` after fix 3) | `json` (and later `os`) were imported but never used. | Removed both imports. |
| 7 | Global connection redefined — W0621 | Design (Pylint) | 6, 10, 19, 24, 34 | `conn` was a module-level global that every function re-declared as a parameter, so the global was shadowed and the dependency was implicit. | Removed the global; the connection is created in `main()`, the schema is created by a `create_schema()` helper, and the connection is passed explicitly. |
| 8 | Missing docstrings — C0114 / C0116 | Style (Pylint) | 1, 10, 15, 19, 24, 30, 34, 39 | Module and all functions had no docstrings, so the purpose of each function was undocumented. | Added a module docstring and a one-line docstring per function. |
| 9 | Non-PEP 8 function names — C0103 | Style (Pylint) | 10, 15, 19, 24, 30, 34 | `recordMilk`, `farmerToken`, `dailyTotal`, `topFarmer`, `printSlip`, `lowFat` use camelCase instead of `snake_case`. | Renamed to `record_milk`, `farmer_token`, `daily_total`, `top_farmer`, `print_slip`, `low_fat`. |
| 10 | Line too long — C0301 / E501 | Style | 7, 11, 20, 25 | Lines exceeded the 79/100 character limits, making the code hard to read side by side. | Wrapped the SQL statements over multiple lines. |
| 11 | `.format()` / `%` instead of f-string — C0209 | Style (Pylint) | 11, 21 | Legacy string formatting was used for text built at runtime. | Used an f-string in `daily_total`; the INSERT now uses placeholders only. |
| 12 | Unprotected top-level call | Design (Pylint) | 47 | `main()` ran unconditionally on import, so the demo (and the database work) executed whenever the module was imported. | Added the `if __name__ == "__main__":` guard. |

## Verification

After the fixes, all three tools were re-run on the final file (see `reports/after/`):

- `pylint dairy_collection.py` → **10.00/10**, exit code 0
- `bandit -r dairy_collection.py` → **0 issues**, exit code 0
- `flake8 dairy_collection.py` → **no output**, exit code 0

The program still produces the expected output:

```
Total: 32.5 litres Lata ['Lata']
printing slip for Gopal
39c7991402a975ff68d16747d0fbb21806c339a035d22512301c5eef1dc9122b
```

The only intentional change in behaviour is the farmer token value, because SHA-256 replaces MD5.
