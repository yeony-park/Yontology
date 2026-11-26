---
name: task-routing
description: Route tasks across Paseo providers using difficulty, account availability and native subagents, avoiding redundant context and delegation.
---

# Task routing

Read config/model-routing.json relative to the resolved Yontology checkout. Check the installed host's `paseo --help`, `paseo run --help`, profile notes and provider model catalog before launching; model labels here are preferences, not validated IDs. Use `paseo usage ls --json` once at a routing boundary (not in a polling loop). Inspect report status and account mapping; unknown/missing quota is not zero. Never equate quota with per-task token use.

Classify by complexity and risk: L0 deterministic bookkeeping (no LLM); L1 bounded lookup or simple edit; L2 implementation/test; L3 complex architecture/debugging. Prefer the current session or native subagents when sufficient. Batch related work. Cross-provider delegation is for real capability differences, independent review or quota exhaustion. When Codex is low, prefer the configured Claude profile for the task level; respect user overrides. If an effort is unsupported, report it and use only a user-approved compatible profile; never silently escalate. Do not retry ambiguous launches (first reconcile agent IDs).

Use `paseo run --provider <verified-provider/model> --no-wait --quiet "<brief>"` plus only locally verified mode/effort flags; `paseo send <id> --no-wait "<brief>"` for a compatible existing worker. Record returned agent ID. Use worktree isolation for independent writers; never let two agents edit the same worktree concurrently. Use completion notifications, or one bounded `paseo wait <id> --timeout 60` when needed; don't read full logs by default. Output artifact references, tests, blockers and next action.

For cross-provider continuation use task-handoff; preserve current checkpoint before launch. No automatic stop/merge/push. Never send credentials or private content across an unauthorized provider/host.
