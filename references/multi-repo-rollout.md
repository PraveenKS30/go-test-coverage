# Multi-repo rollout

Scaling this standard from one repo to many introduces three problems that
don't exist in a single-repo setup: inconsistent config drift, no org-wide
visibility, and repos with wildly different starting coverage baselines.
Here's how each is handled.

## 1. Config drift — templates, not copy-paste

Every repo needs the same three files. Don't hand-edit them per repo:

- `sonar-project.properties` — only `sonar.projectKey` changes per repo.
  Use a consistent key naming convention: `your-org_<repo-name>` — this is
  what lets SonarQube group repos into a Portfolio (below).
- The CI workflow — convert `assets/ci-workflow.yml.template` into an
  **org-level reusable GitHub Actions workflow** once, and have every repo's
  `.github/workflows/test-and-scan.yml` just be a thin `uses:` reference to
  it. A threshold change (e.g. raising 80% → 85% org-wide later) becomes a
  one-line edit in one place instead of N PRs across N repos.
- `.testcoverage.yml` — same templating approach; only the `threshold`
  block should ever need to differ per repo (see baseline handling below).

## 2. Org-wide visibility — SonarQube Portfolios

Individual repos each get their own Quality Gate pass/fail, but you also
want one view across all of them. SonarQube's **Portfolios** feature
aggregates multiple projects (repos) into a single dashboard — coverage
trend, gate pass rate, and open issues, rolled up across every repo whose
`projectKey` you add to the portfolio. This is why the naming convention in
step 1 matters: a consistent `your-org_` prefix makes it trivial to add new
repos to the portfolio as they're created, either manually or via a tag-based
rule so it happens automatically.

## 3. Different starting baselines — wave rollout, not a big bang

Repos in a real org are never at the same coverage level on day one. Forcing
an 80% overall gate everywhere at once either blocks a legacy repo's every
PR indefinitely, or forces the team to quietly lower the bar org-wide to
accommodate the worst repo. Instead:

1. **Inventory first.** Run the batch scaffold scan (`scaffold_test.py <repo>
   --all --recursive`) against every repo to get a same-day picture of how
   many exported functions currently have zero tests, per repo. This is a
   text-based accounting: you don't need real coverage numbers yet to know
   which repos have the most test debt.
2. **Gate on "Coverage on New Code" everywhere, immediately.** This is safe
   to turn on org-wide from day one regardless of legacy debt, since it only
   evaluates the diff in each PR — it does not block on the whole repo's
   history. This is the single biggest lever for stopping new test debt from
   accumulating while legacy debt is paid down separately.
3. **Track legacy/overall coverage as a dashboard metric, not a gate**, per
   repo, until each repo crosses whatever overall threshold your team
   decides (doesn't have to be 80% — could be a lower interim target).
4. **Roll out in waves**, not all repos at once:
   - Wave 1: pilot repo — get the full loop (test → coverage →
     SonarQube → required check) working end-to-end.
   - Wave 2: repos already near 80% overall — quick wins, gate on new code
     AND set a near-term overall target.
   - Wave 3: repos furthest from 80% — new-code gate only, with a longer
     runway and no overall gate until debt is paid down.

## Rollout tracker template

Keep this as a living doc/sheet, one row per repo, updated as each repo
moves through the waves:

| Repo | Wave | New-code gate live? | Overall coverage (baseline) | Overall coverage (current) | SonarQube project key | Owner |
|---|---|---|---|---|---|---|
| dbt-code-promotion | 1 (pilot) | Yes | 12% | — | your-org_dbt-code-promotion | Praveen |
| cdk-customer-foundation | 2 | — | 61% | — | your-org_cdk-customer-foundation | Yamini |
| story-work-cycle-svc | 3 | — | 4% | — | your-org_story-work-cycle-svc | Navdeep |

This is the same information a SonarQube Portfolio gives you visually, but
useful earlier — before every repo is even wired up to Sonar yet — as a
plain rollout-status tracker.
