---
name: define-project
description: Convert vague project or feature ideas into approved, versioned product specifications through a Socratic interview and an Ouroboros-backed Interview → Seed → Execute → Evaluate → Evolve loop. Use when the user wants to plan or define a new product, service, application, major feature, MVP, requirements document, or PRD before coding; asks to clarify ambiguous requirements; requests an interview-first or specification-first workflow; or says 프로젝트 기획, 요구사항 정리, 명세 작성, PRD 작성, 만들기 전에 질문해줘, or 모호한 아이디어를 구체화해줘. Do not use for a small, already well-specified implementation or defect-only task unless the user asks to revisit product intent.
---

# Define Project

Turn a brief into an explicitly approved `docs/PRD.md`. Prefer the official
Ouroboros runtime for persistent interviews, immutable Seeds, evaluation, and
evolution. Add the project-definition gates in this skill around that runtime.

## Non-negotiable contract

- Define what to build before deciding how to code it.
- Do not create production code, scaffolding, migrations, or implementation
  tasks while this skill is active.
- Ask one primary Socratic question per turn. Group only tightly coupled choices.
- Inspect repository facts directly; ask the user only for human judgment.
- Treat assumptions, deferred decisions, and confirmed requirements differently.
- Require explicit user approval before freezing a Seed and before finalizing the
  PRD.
- Preserve every accepted Seed. Never edit a frozen Seed in place.
- Increment the Seed version only when its content changes.
- Finish only at `docs/PRD.md`; do not substitute another final path.

## Prepare the workflow

1. Determine the project root from the active workspace. If multiple roots are
   plausible, ask which one owns the PRD.
2. Inspect relevant existing product docs and repository structure without
   changing them. Record facts separately from inferred requirements.
3. Discover the official Ouroboros PM/interview tools or active `ooo` skills.
   Prefer `ooo pm` for product discovery, then the standard interview/Seed tools
   for the runnable Seed handoff.
4. If the tools are inactive in Codex, inspect `codex plugin list`. Distinguish:
   - `ouroboros@ouroboros` is installed and enabled: explain that the current
     session predates the plugin activation, ask the user to restart Codex, and
     stop without reinstalling anything;
   - the plugin is absent: stop before promising persistent or replayable
     behavior, explain the missing dependency, and ask permission to install the
     official plugin/runtime.
   In other hosts, use their equivalent plugin/runtime status check. Never
   silently imitate Ouroboros persistence, ambiguity scores, or convergence.
5. Read [references/prd-and-review.md](references/prd-and-review.md) before the
   first closure review or before drafting the PRD.

## Run the evolutionary specification loop

### 1. Interview

Start from the user's brief. Maintain a compact visible ledger containing:

- confirmed decisions;
- assumptions awaiting confirmation;
- decide-later items with an owner and decision deadline;
- development-deferred technical choices;
- blocking unknowns;
- current ambiguity score when Ouroboros provides one.

Route each question before asking it:

1. Answer repository-local facts by inspection.
2. Research current external facts only when they materially affect the choice.
3. Ask the user about goals, users, scope, tradeoffs, business rules, risk
   tolerance, or success criteria.
4. Offer two or three concrete interpretations when a vague term could be read
   multiple ways. State a recommendation and its tradeoff.
5. Allow `decide later`, `defer to development`, and `record as assumption` only
   when the item is not blocking.

Cover, without mechanically dumping a questionnaire: problem and motivation;
target users and excluded users; primary outcome; scope and non-goals; core
entities; journeys and screens or service touchpoints; permissions and data;
failure and recovery states; operational ownership; constraints; rollout; and
measurable success.

### 2. Seed

Ask for explicit approval to crystallize the current answers. Generate the Seed
through Ouroboros. Accept a Seed only when:

- the official ambiguity gate passes, normally `<= 0.20`;
- every acceptance criterion is observable and falsifiable;
- blocking unknowns are empty;
- non-goals and hard constraints are explicit;
- each open item has a safe deferral rule.

Freeze every accepted Seed with:

```bash
python3 <skill-dir>/scripts/version_seed.py <seed-path> --project-root <project-root> --reason "<concise reason>"
```

Use the returned `vNNNN` as the canonical project Seed version. If the content
hash is unchanged, keep the current version. Store versions under
`docs/seeds/`; never modify a versioned file.

### 3. Execute the specification

Do not implement the product. Execute the Seed as a specification simulation:

- walk the primary journey from entry to successful outcome;
- walk at least one permission failure, empty state, invalid-input state, partial
  failure, and recovery path when applicable;
- map each step to a screen, service touchpoint, or system response;
- test acceptance criteria against concrete examples;
- simulate rollout, monitoring, support, rollback, and data lifecycle;
- identify decisions that would force materially different product shapes.

Use repository inspection, small calculations, or throwaway analysis only when
they reduce requirement uncertainty. Do not create production artifacts.

### 4. Evaluate from three independent perspectives

Spawn independent subagents when the runtime supports them. Give each reviewer
the current Seed and factual project context, not prior conclusions. Assign:

1. **Product and UX reviewer** — verify user value, core screens or touchpoints,
   journey continuity, states, accessibility, and scope coherence.
2. **Engineering and operations reviewer** — verify data, permissions, security,
   integrations, ownership, observability, support, rollout, rollback, and
   lifecycle constraints.
3. **QA and evidence reviewer** — verify measurable success, falsifiable
   acceptance criteria, negative cases, test data, evaluation method, and exit
   conditions.

Require every finding to include severity, evidence, affected Seed section, and
a concrete question or amendment. Reviewers advise; they do not change the Seed.
If subagents are unavailable, perform the same reviews sequentially and disclose
the limitation.

### 5. Evolve

Merge duplicate findings and distinguish genuine gaps from implementation detail.
For each material gap:

1. Ask the smallest user question that resolves it.
2. Generate a new Seed from the previous Seed plus accepted answers and evidence.
3. Freeze it as the next version with `version_seed.py`.
4. Repeat specification execution and the affected review lanes.

Stop evolving only when blocking/high-severity findings are zero, ontology and
scope are stable, and the closure rubric in the reference passes. Respect
Ouroboros convergence and stagnation signals; never claim convergence from
intuition alone.

## Run the final confirmation gate

When the closure review passes, present exactly one concise confirmation sentence
in the user's language using this structure:

> 최종 목표: [target user]가 [core problem]을 [core experience]로 해결하고,
> [hard constraints]를 지키며, 성공 여부를 [measurable evidence]로 판단할 수
> 있는 [product]을 만든다.

Adapt the sentence naturally but keep user, problem, experience, constraints,
evidence, and product type. Ask the user to approve or correct it. Do not write
the final PRD until the user explicitly approves this sentence.

## Write and verify the PRD

After approval:

1. Draft `docs/PRD.md` using the exact section contract in
   [references/prd-and-review.md](references/prd-and-review.md).
2. Mark it approved and cite the latest Seed version and path.
3. Preserve decide-later and development-deferred items; do not rewrite them as
   confirmed requirements.
4. Include requirement-to-acceptance-criterion traceability.
5. Validate it:

```bash
python3 <skill-dir>/scripts/validate_prd.py <project-root>/docs/PRD.md
```

6. Fix validation failures without inventing decisions. Reopen the interview if
   a missing section requires human judgment.
7. Report the PRD path, latest Seed version, remaining non-blocking open items,
   and the approved final-goal sentence. End the planning workflow. Do not begin
   implementation unless the user makes a new explicit request.
