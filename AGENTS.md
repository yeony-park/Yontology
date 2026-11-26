# Yontology agent instructions

Use deep-inside on every user request as a lightweight quality preflight: expert gap, primary evidence, concrete methods/tools, independent validation. Think in English; answer in Korean unless requested otherwise. Scale depth to the task, not breadth. Never expand authorized scope or disclose hidden reasoning.

For multi-agent work, use skills/task-routing, skills/task-handoff and skills/knowledge-memory. Paseo CLI owns dispatch and communication; prefer native subagents for local subtasks. Do not create a second orchestrator. Use explicit task IDs, one active writer per task, incremental checkpoints and verified completion. Do not publish private notes or session traces to this public repository. Never change existing user notes without authorization.

Central deployment: use the authorized user's central storage roots; raw sources and Vault are separate. Execute task checkpoints on the storage server via remote_memory.py (or agent_memory.py on the server). Do not edit checkpoint files over SMB or create local copies on network failure. Reuse official Obsidian skills if available, without auto-installing them. Never include actual user paths, credentials, task state, or source materials in Git.

Repository changes must follow CONTRIBUTING.md: track an issue first, use a topic branch from develop, open an issue-linked PR, and close completed issues only after merge. Never push implementation commits directly to develop or main. Release to main via a separate authorized PR. Preserve actual verification status.

When working outside Yontology, use the explicit user's instructions and the target project's applicable local instructions, contribution conventions, CI, lint, templates and branch rules first. Yontology conventions are defaults only when the target has no applicable rule; do not overwrite project conventions or bypass permissions. Review confirmed findings, fix them on the topic branch, and verify CI before merging. Only delete merged topic branches after checking no unmerged changes remain; preserve long-lived branches and follow the target repository policy.
