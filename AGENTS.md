# Yontology agent instructions

Use deep-inside on every user request as a lightweight quality preflight: expert gap, primary evidence, concrete methods/tools, independent validation. Think in English; answer in Korean unless requested otherwise. Scale depth to the task, not breadth. Never expand authorized scope or disclose hidden reasoning.

For multi-agent work, use skills/task-routing, skills/task-handoff and skills/knowledge-memory. Paseo CLI owns dispatch and communication; prefer native subagents for local subtasks. Do not create a second orchestrator. Use explicit task IDs, one active writer per task, incremental checkpoints and verified completion. Do not publish private notes or session traces to this public repository. Never change existing user notes without authorization.

Central deployment: use the authorized user's central storage roots; raw sources and Vault are separate. Execute task checkpoints on the storage server via remote_memory.py (or agent_memory.py on the server). Do not edit checkpoint files over SMB or create local copies on network failure. Reuse official Obsidian skills if available, without auto-installing them. Never include actual user paths, credentials, task state, or source materials in Git.
