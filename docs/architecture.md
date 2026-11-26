# Paseo-first agent harness

Yontology adds policy and persistent memory; Paseo owns agent creation, routing transport, lifecycle and workspace placement. The existing skills and overview-project remain at their original paths. No separate scheduler, daemon, vector store or Notion integration.

1. Apply Deep Inside at each user input (constant lightweight hook, explicit skill for detailed use).
2. Classify task and check account availability only at dispatch boundaries. Prefer local/native subagents; use Paseo CLI across providers.
3. Use a stable task ID and one owner; checkpoint meaningful progress into Obsidian. Context stays provider-native while work is active. Handoff transmits a compact briefing plus references, not a transcript.
4. The receiving agent verifies repository state, task revision and accessible notes. Independent work uses a separate worktree; no silent merge.
5. Record acceptance evidence and promote only verified durable knowledge to the wiki.

The routing configuration records requested labels/effort, not real provider IDs. Discover on the specific daemon and create matching profiles in Settings → host → Agents. Use usage report status and account mapping; no quota guessing. The account quota is not token accounting. Configure approved fallback profiles before enabling delegation.

Task markdown holds a JSON block for deterministic reads. Writes are atomic with optimistic revision checks and a local advisory lock; this is NOT a distributed lock. Cross-host transfer requires a shared/synced authorized vault and explicit owner handover. Preserve existing note layout. Never commit actual notes, checkpoint contents, credentials or session logs to the public repo.

Hooks are opt-in fragments, not auto-installed. UserPromptSubmit injects only a short constant instruction. SessionStart adds a reminder. Semantic checkpointing is a skill operation, not an inferred summary from a transcript. True automatic pre-compaction/stop checkpoints and quota-based dispatch automation need host integration tests; they are not claimed implemented. No remote process is started by installation.

## Local validation

Run `python3 -m unittest discover -s tests`. Run `python3 scripts/agent_memory.py init` after verifying .env. Inspect `paseo usage ls --json`, `paseo run --help`, and actual profile names/effort. Use a synthetic repo/task to test Codex→Claude and Claude→Codex, including a simulated exhausted quota and stale revision. Measure input/output/cache usage from provider telemetry, not quota percentages; compare completion accuracy and repeated work. Do not test on production or confidential project data by default.
