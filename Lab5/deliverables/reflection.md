# Lab 5 — Reflection

**Student:** Mohammed Rizwan Shaikh (PES1UG24CS272)

## 1. What is static code analysis, and how does it differ from running the program?

Static code analysis inspects the source code without executing it. The tools read the abstract
syntax tree and look for patterns that are known to be risky or hard to maintain: unused imports,
camelCase names, over-long lines, string-built SQL, weak hashes, shell calls. Because the code is
never run, the analysis can be applied to every line, including error paths that a test run might
never reach.

Running the program is different: `python dairy_collection.py` only showed me that the happy path
works — it printed the total, the top farmer, the slip and the token. It told me nothing about the
farmer name `x'); DROP TABLE milk;--`, which would have broken the INSERT, or about the MD5 token,
which looks perfectly correct on screen. The static tools found exactly those defects while the
program was behaving normally. In short: running proves behaviour on the inputs I chose; static
analysis points at the code I would have had to think of myself.

## 2. Which issues did you find, and which was the most serious?

Bandit reported three issues, two of them High: MD5 used for the farmer token (B324) and
`os.system("echo ..." + farmer)` (B605). It also reported the SQL injection in `recordMilk` (B608)
as Medium.

I consider the shell injection (B605) the most serious. The farmer name comes from user input and is
concatenated straight into a command string, so a name containing `;` or `$(...)` would execute
arbitrary commands with the privileges of whoever runs the ledger. The SQL injection is a close
second: the same input reached the database as SQL. Both are High impact because they turn ordinary
data into code. The MD5 finding is less immediately dangerous — a token is not a password here — but
MD5 is broken for any security purpose, so it had to go.

Pylint and Flake8 mostly reported style and design issues: missing docstrings, camelCase names,
over-long lines, `fat == None`, the ambiguous variable `l`, unused imports, and a global `conn` that
every function shadowed with a parameter. These are not exploitable, but the global connection and
the missing docstrings made the code harder to read, and `fat == None` is a genuine correctness bug
waiting for a `NULL` fat reading.

## 3. How did you fix the issues, and how did you check the fixes?

I fixed the security issues structurally rather than by silencing the warnings:

- the INSERT was rewritten as a parameterised query, so the farmer name is always data;
- MD5 was replaced with SHA-256;
- `os.system` was dropped in favour of printing the slip directly, so no shell is involved at all;
- the global connection was replaced by one created in `main()` and passed explicitly, with a
  `create_schema()` helper for the table;
- names were converted to `snake_case`, docstrings added, long SQL statements wrapped, and the
  ambiguous `l` renamed to `best`.

Then I re-ran all three tools on the fixed file and compared against the saved reports:
Pylint went from 2.00/10 to 10.00/10, Bandit from 2 High + 1 Medium to zero, Flake8 from 7 issues to
zero. I also re-ran the program and checked that the output was unchanged apart from the token value,
which necessarily changed when SHA-256 replaced MD5. Fixing the findings by editing the code — not by
adding `# pylint: disable` or `# nosec` — is what makes the second report meaningful.

## 4. What did you learn about the contribution of static analysis to code quality?

The most useful thing was how much the three tools overlap and how they differ. Flake8 is purely
mechanical: line length, spacing, unused imports, and it is fast to satisfy. Pylint is a reviewer
with opinions about design — naming, docstrings, shadowed globals — and its score is a rough proxy
for readability. Bandit is the only one that looked for security, and it found the three issues that
actually mattered, which is why "the code runs" is a weak definition of "the code is correct".

I also saw the limits. Static analysis cannot know whether the total for a day is the right total;
it flags patterns, so it produces false positives and can be silenced without being fixed. A clean
run is a floor, not a guarantee — it means nothing obvious is wrong, and it still needs tests and
review on top. Still, on a 47-line file it found three real security defects and a latent `None`
comparison bug in under a minute, which is a very good return. The habit worth keeping is running the
tools early and often, so the diff stays small and the warnings never pile up.
