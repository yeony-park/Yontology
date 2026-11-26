# Yontology agent instructions

Use deep-inside on every user request as a lightweight quality preflight: expert gap, primary evidence, concrete methods/tools, independent validation. Think in English; answer in Korean unless requested otherwise. Scale depth to the task, not breadth. Never expand authorized scope or disclose hidden reasoning.

For multi-agent work, use skills/task-routing, skills/task-handoff and skills/knowledge-memory. Paseo CLI owns dispatch and communication; prefer native subagents for local subtasks. Do not create a second orchestrator. Use explicit task IDs, one active writer per task, incremental checkpoints and verified completion. Do not publish private notes or session traces to this public repository. Never change existing user notes without authorization.
