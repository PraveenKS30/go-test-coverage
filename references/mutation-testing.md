# Mutation testing (optional, recommended for critical-logic repos)

Coverage % tells you a line executed. It cannot tell you whether the test
that executed it would fail if the logic were wrong — the discount-calculator
demo in this skill's origin conversation proved this directly: a stub test
hit 84.6% coverage and stayed green after a real discount-rate bug was
introduced, while a real table-driven test (92.3% coverage) failed
immediately on the same bug.

Mutation testing automates that check at scale: it deliberately mutates your
code (flips `>` to `<`, `+` to `-`, deletes a return, etc.) and reruns your
tests. If tests still pass, that mutant "survived" — a sign your tests aren't
actually verifying that logic.

## Tool: Gremlins

```bash
go install github.com/go-gremlins/gremlins/cmd/gremlins@latest
gremlins unleash ./...
```

Reports each mutation as `RUNNABLE`, `NOT COVERED`, `KILLED`, or `SURVIVED`.
A `SURVIVED` mutant on code you just changed means: write a case that would
fail if that logic broke.

## Where this fits in the rollout

- **Not required repo-wide on day one.** Gremlins is built for small/medium
  Go modules (microservices) — on very large modules a run can take hours,
  so don't mandate it as a blocking CI step everywhere immediately.
- **Start with**: run it as a sampled/manual check on PRs touching
  high-risk logic (billing, ARR variance calculations, anything financial or
  customer-facing), not as a blocking gate on every PR.
- **Incremental mode** exists specifically for testing only the mutants
  introduced by a PR's diff, which keeps run time bounded even on larger
  repos — use this before considering a full-repo run.
- **Metric to watch**: mutation/efficacy score (% mutants killed) trending
  over time on critical packages, reported alongside — not instead of —
  the SonarQube coverage %.
