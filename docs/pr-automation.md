# Pull request automation

## Deterministic CI

.github/workflows/ci.yml runs on PR creation, reopening, synchronization and ready-for-review for main/develop, and pushes to those branches. Python 3.10/3.12 run syntax checks, repository unit tests and daily-learning tests; Overview Project uses Node 22 and the frozen pnpm lock. Jobs have read-only repository permissions, bounded runtimes, and no model credentials. Fork PRs run CI without secrets. These checks do not prove live Paseo, storage, provider or backup integration.

## Selected reviewer: ClawSweeper

[ClawSweeper v0.3.5](https://github.com/openclaw/clawsweeper/releases/tag/v0.3.5), pinned to [22265ff](https://github.com/openclaw/clawsweeper/commit/22265ff14ea73421cfaba18a17cca92a3c13d8e9), is selected for advisory review. The workflow builds the upstream local-range reviewer, not a fork or copied implementation. [Local branch review](https://github.com/openclaw/clawsweeper/blob/v0.3.5/docs/commit-sweeper.md) supports arbitrary repositories and uses their own AGENTS.md and project rules. The hosted OpenClaw dispatcher requires an eligible installation, external service and configured repository admission; do not assume Yontology is eligible. No hosted dispatcher is installed.

The optional workflow is disabled until explicitly configured. Before enabling, review the upstream source and security model, use a dedicated API project with spending limits, and verify the GitHub-hosted runner's sandbox and scanner prerequisites. Then create the protected GitHub Actions environment `clawsweeper-review` (restrict trusted deployment branches and reviewers as appropriate), add environment secret `CLAWSWEEPER_OPENAI_API_KEY`, choose an API-accessible model in repository variable `CLAWSWEEPER_MODEL`, and set repository variable `CLAWSWEEPER_ENABLED=true`. Do not store a key or personal Codex login in the repository. This consumes separate API usage, not a local ChatGPT/Codex subscription. To disable, unset the enable variable. The automatic trigger runs only on non-draft, same-repository PRs; fork PRs are deliberately excluded from credentialed review.

The pull_request_target workflow uses the trusted base-branch workflow definition. Never run scripts, package install, tests, hooks or actions from the PR tree in this job. It obtains the exact head/base Git objects and hands a clean checkout to the pinned read-only review engine; no GitHub write token, OpenClaw service credentials or storage access is granted. The model credential is scoped to a dedicated isolated Codex home. The authentication step alone receives the API key; a model login still creates credential material, so protect the environment and treat this as a defense-in-depth boundary, not an absolute guarantee. Review code and prompts as untrusted input. Do not enable on a self-hosted runner with personal files or other credentials. Keep one bounded review per PR head. The report is advisory in the Actions step summary; no auto-fix or auto-merge is enabled. Do not interpret a successful process exit as a clean review. Inspect findings and CI status explicitly.

For an already-authenticated trusted local host, follow the upstream local-range documentation and choose a clean target checkout:

```bash
# from a built ClawSweeper v0.3.5 source checkout
pnpm local-review -- --target-dir /path/to/project --target-repo owner/repo --base origin/develop
```

Use the actual PR base ref instead of origin/develop in repositories with another convention. Upstream scanner setup and model auth are prerequisites. No model review has been run by adding this file.

## Convention and review loop

Explicit user instructions and the actual target project's AGENTS.md, CLAUDE.md, CONTRIBUTING.md, existing workflows, lint rules and branch policies take precedence over Yontology defaults. Respect higher-level security constraints and actual permissions. Never impose Yontology branch names or labels on unrelated projects that already have rules. Review changes against the PR scope and evidence; fix only confirmed actionable findings in the topic branch, re-run CI/review after the head changes, and do not merge with unresolved blocking findings or required checks. Preserve main/develop. After a successful merge verify topic branch ancestry (or squash-equivalent content and no newer commits) before deleting it. Keep open or unmerged branches. GitHub's automatic head-branch deletion setting can be enabled separately by the repository administrator; the connector does not support branch deletion or repository settings writes. Do not automatically delete develop after a release PR. Follow target repository cleanup policy if it differs.

ClawSweeper hosted automation or OpenClaw integration is a future option, not an active deployment. The review workflow is opt-in; CI alone does not establish branch protection or required checks. Configure these separately if desired.
