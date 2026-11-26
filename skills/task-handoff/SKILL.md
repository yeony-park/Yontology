---
name: task-handoff
description: Persist incremental task state and transfer a bounded briefing to another Paseo agent; resume after interruption or quota exhaustion.
---

# Handoff

Use the existing notes path resolver. Run `python3 <checkout>/scripts/agent_memory.py init` once and `... show PROJECT TASK` to read the current checkpoint. New tasks use a stable project/task slug and `... checkpoint PROJECT TASK --input <json-file> --expected 0`. On update read the current revision and pass it as --expected. Keep previous decisions and unresolved issues; don't overwrite a newer revision. Schema: templates/task.json. Write a new checkpoint after meaningful task milestones, before voluntary handoff or compaction; don't wait for exhaustion.

For a handoff, prefer Sol 6.2 Medium; secondary Terra 6.1 High; when Codex is unavailable use the configured Claude handoff profile. Check model IDs/effort on the host. If no compression model is available, resume from the last valid checkpoint and inspect git status/diff and explicit knowledge references. Never invent completion. Do not launch a second model for routine checkpoint writes. Compress only changed facts; use existing PRD/ADR/wiki links rather than copying source text. Suggested initial briefing budget: 2,000–4,000 tokens, not a guaranteed measured limit. Keep constraints, acceptance criteria, known failures, repo/worktree/commit, next action and evidence. Do not copy transcripts, secrets or whole tool logs.

Send the receiving agent a task ID, checkpoint reference as project/task ID (not a host-specific absolute path), objective and next action via Paseo CLI. Verify the destination can access the repo and notes before dispatch; when moving to another machine verify the same central root, account authorization and explicit ownership transfer. A new provider starts a new context; no KV-cache or hidden reasoning transfer. The previous writer must relinquish ownership before the next writer edits. Resume by reading the checkpoint, verifying git state and referenced knowledge, then proceeding only with remaining actions. Mark completed only with acceptance evidence. Promote durable validated knowledge via knowledge-memory.

## Central task state

In central-storage deployments, all client checkpoint operations must execute on the storage server under the task owner's authorized account. Use `python3 <checkout>/scripts/remote_memory.py --host <trusted-ssh-alias> --checkout <absolute-server-checkout> show PROJECT TASK` and the corresponding checkpoint command with --input and --expected. The server may use agent_memory.py directly. Never write task files from SMB clients or switch silently to local memory when the server is unavailable. Reconcile the remote revision after an uncertain result before retrying. Do not share SSH credentials or a personal Vault across users. A task may use the shared Vault only with explicit shared-project authorization. See docs/storage.md.
