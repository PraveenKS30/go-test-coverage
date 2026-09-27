# SonarQube setup, step by step

1. **Generate coverage** with `go test -coverprofile=coverage.out -covermode=atomic`,
   excluding mocks/generated code from the package list.

2. **Drop `sonar-project.properties`** (from `assets/`) into the repo root,
   set `sonar.projectKey`.

3. **Create/edit the Quality Gate**: add condition "Coverage on New Code" <
   80% → fails. Set this as the org-wide default gate so new repos inherit it.

   Gate on **new code**, not overall code, for any repo that isn't starting
   from zero — gating on overall coverage on a repo currently at 30% blocks
   every single PR indefinitely. Track legacy/overall coverage as a separate
   non-blocking dashboard metric, and set a longer-term plan to raise it.

4. **Wire into CI** using `assets/ci-workflow.yml.template`. Make the
   SonarQube check a **required status check** in branch protection — an
   unenforced gate is just a dashboard.

5. **Template, don't repeat.** Turn the CI workflow into an org-level reusable
   workflow and the `sonar-project.properties` into a copy-paste-and-fill
   template, so every new Go repo — including ones created by new team
   members — inherits the gate by default instead of someone remembering to
   wire it in.

6. **Pilot on one repo first.** Get the full loop (test → coverage → Sonar →
   gate → required check) working end-to-end on one repo before rolling out
   org-wide. Baseline current coverage on the rest before turning on
   enforcement elsewhere.
