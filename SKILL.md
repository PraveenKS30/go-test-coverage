---
name: go-test-standard
description: Team standard for writing Go unit tests and enforcing 80% test coverage via SonarQube. Use this whenever writing, adding, or fixing Go unit tests, whenever someone asks to raise test coverage on a Go repo, whenever a SonarQube coverage gate is failing, or when setting up a new Go repo's CI/testing pipeline. Enforces table-driven tests with real assertions and blocks common "coverage stub" anti-patterns that inflate coverage % without testing anything. Also covers wiring go test coverage into sonar-project.properties and CI quality gates.
---

# Go Test Coverage Standard

## Philosophy (read this first)

Coverage % measures whether a line *ran* during tests, not whether it was *verified*.
A test with no assertions, or an assertion copied from the mock's own return value,
can hit 100% coverage while catching zero real bugs. This skill exists to prevent
that outcome — coverage is the floor for CI enforcement, but every test written
under this standard must also carry real, checkable assertions.

Never write a test purely to move a coverage number. Every test case must answer:
"if this business logic were subtly wrong, would this test go red?"

## When writing or adding tests

1. **Always use table-driven tests.** This is Go's idiomatic pattern and the
   required structure under this standard — see `references/test-template.go`
   for the exact skeleton to start from.

2. **Cover the happy path AND edge/error cases for every branch.** For any
   function with `if`/`switch`/error returns, include at minimum:
   - one case per branch (not just the default path)
   - a zero/nil/empty-input case
   - a boundary case (exactly at a threshold, e.g. `price == 1000` when the
     logic branches on `price > 1000`)
   - an error case, if the function can return one

3. **Every test case must assert on a real, independently-derived expected
   value** — a value you compute by reading the business logic, not a value
   copied from what the code currently outputs. If you can't state in a code
   comment *why* the expected value is correct (e.g. `// 500 - (500*0.20)`),
   you haven't verified it yet.

4. **Never write these anti-patterns** (reject them in review, and never
   generate them yourself):
   - A test with no assertion at all — calling the function and discarding
     the result "just to get the line covered."
   - Asserting against a mock's own stubbed return value (circular — the
     mock says "return X", the test asserts "result == X"; this proves the
     mock works, not the code).
   - Table-driven cases that all assert the same trivial condition
     (e.g. every case just checks `err == nil`, never checking the value).
   - Deleting or loosening an assertion to make a failing test pass, instead
     of fixing the bug the assertion caught.

5. **Use subtests (`t.Run`) and `t.Parallel()`** per table entry for clear,
   isolated failure output — see the template.

Full anti-pattern list with examples: `references/anti-patterns.md`.

## When setting up or fixing coverage enforcement (SonarQube)

1. Generate coverage in Go's native format, excluding generated/mock code:
   ```bash
   go test $(go list ./... | grep -v /mocks/ | grep -v /gen/) \
     -coverprofile=coverage.out -covermode=atomic
   ```

2. Point SonarQube at it via `sonar-project.properties`
   (`assets/sonar-project.properties.template`). SonarQube's Go sensor reads
   `coverage.out` directly — no conversion step needed.

3. Set the Quality Gate condition on **"Coverage on New Code"**, not overall
   coverage, when rolling this out to existing repos — gating on overall
   coverage will permanently block every PR on a repo that starts below 80%.
   Track overall/legacy coverage as a separate, non-blocking dashboard metric.

4. Wire the reusable CI workflow (`assets/ci-workflow.yml.template`) into each
   repo rather than copy-pasting per-repo YAML, so new repos inherit the gate
   by default.

5. Optional fast pre-check before SonarQube: `assets/testcoverage.yml.template`
   works with `vladopajic/go-test-coverage` for a local/PR-time threshold
   check per file, without needing a SonarQube round-trip.

Full step-by-step: `references/sonarqube-setup.md`.

## Generating test files

**Single function:**
```bash
python3 scripts/scaffold_test.py path/to/file.go FunctionName
```

**Every untested exported function in one package:**
```bash
python3 scripts/scaffold_test.py path/to/package_dir --all
```

**Every untested exported function across an entire repo (all packages):**
```bash
python3 scripts/scaffold_test.py path/to/repo --all --recursive
```

Batch mode scans every `.go` file, skips unexported functions and
`main`/`init`, and skips any function that already has a `Test<Func>`
anywhere in its package — so it's safe to re-run repeatedly on a repo as
tests get filled in; it only scaffolds what's still missing. It prints a
one-line summary (found / scaffolded / already tested / skipped) so a whole
repo's test debt is visible in a single run.

In every mode, the tool produces empty test cases with `// TODO: verify
against business logic` markers — it deliberately does NOT guess or fill in
expected values, because that's the exact anti-pattern this standard exists
to prevent. A human (or Claude, reading the actual function body) must fill
in and justify each expected value before the test is complete.

## Multiple repos

When rolling this standard out across more than one repo, don't hand-copy
config or gate each repo the same way regardless of its current coverage —
see `references/multi-repo-rollout.md` for: templating the CI workflow and
Sonar config at the org level, aggregating visibility across repos via
SonarQube Portfolios, and sequencing rollout in waves so a legacy repo at
10% coverage doesn't block every PR on day one while a new repo still
correctly gates at 80%.

## Reviewing a PR against this standard

Check for, in order:
1. Are there table-driven tests for new/changed exported functions?
2. Does every branch have a covered case, including at least one edge case?
3. Does every assertion check a real value, not just "no error"?
4. Any of the anti-patterns in `references/anti-patterns.md` present?
5. Is `sonar-project.properties` present and pointing at the right
   coverage file for this repo?

If mutation testing (Gremlins) is enabled for this repo, also check the PR's
mutation report for `SURVIVED` mutants on changed lines — a survived mutant
on logic you just added means the new test isn't actually verifying it. See
`references/mutation-testing.md` for setup and how to read results (optional,
recommended for high-risk/critical-logic repos, not required repo-wide since
it adds CI time on large modules).
