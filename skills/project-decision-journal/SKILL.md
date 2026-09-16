---
name: project-decision-journal
description: Persist material project decisions and their reasoning as repository ADRs, with optional cross-project indexing. Use implicitly after the user confirms a consequential product, architecture, data, security, API, vendor, or implementation choice following tradeoff discussion (including A/B selections), or explicitly asks to preserve why a choice was made. Ignore trivial, reversible, formatting, naming, and other mechanical choices.
---

# Project Decision Journal

Preserve the decision trail without interrupting the work that produced it.

Resolve this SKILL.md through any symlinks to find the Yontology checkout (the parent of `skills/`). Before accessing notes or session data, run `python3 <checkout>/scripts/yontology_paths.py` and use the returned absolute paths. It reads that checkout’s `.env`, independently of the current working directory. `$YONTOLOGY_NOTES_DIR` below denotes the resolved value, not an automatically exported shell variable. Use the returned path for file access and chat links; keep links between notes vault-relative. Do not execute `.env` as shell code or fall back to a previous machine’s path.

## Decide Whether to Record

Record a choice when reversing it later would materially affect scope, behavior, architecture, data, security, cost, operations, compatibility, or delivery. Treat an explicit selection such as `A` as confirmation only when the surrounding discussion identifies a material tradeoff.

Do not record routine commands, typo fixes, formatting, file naming, obvious implementation details, temporary debugging steps, or choices with no meaningful consequence. When uncertain, prefer not to create an ADR unless the user asks.

## Locate the Project Convention

1. Resolve the active repository or project root.
2. Search for an existing ADR convention, including decision directories, ADR files, templates, indexes, and documented naming or numbering rules.
3. Follow that convention exactly when found.
4. Otherwise use `docs/decisions/README.md` and `docs/decisions/ADR-NNNN-kebab-topic.md`, assigning the next unused four-digit number. Adapt [assets/adr-template.md](assets/adr-template.md) and [assets/index-template.md](assets/index-template.md).

Do not create or modify unrelated README files.

## Capture the Decision

Use the conversation and project artifacts as evidence. Separate:

- **User-confirmed facts:** the chosen option and reasons the user explicitly stated.
- **Inferences:** consequences or intent derived from context; label each as `Inferred` and state what supports it.

Never silently invent rationale. If an essential reason is missing and would change the record, ask one concise question. Otherwise write `Not stated` and continue.

Include:

- status and decision date;
- context and decision scope;
- confirmed decision and confidence source;
- considered alternatives and tradeoffs;
- explicit rationale;
- positive and negative consequences;
- implementation guardrails and measurable validation;
- revisit triggers;
- supersession links and status when applicable;
- links to relevant requirements, code, issues, research, or prior ADRs.

Use `Current conversation (no durable link)` when no durable source exists. Do not fabricate URLs or references.

## Maintain History

- Update a proposed ADR freely while the decision is still forming.
- For a clarification that does not change an accepted decision, add a dated amendment without rewriting history.
- For a changed accepted decision, create a new ADR, mark the old ADR `Superseded`, and link both directions.
- Keep the project decision index sorted by ADR number and update an existing row instead of duplicating it.

## Optionally Maintain the Cross-Project Index

If `$YONTOLOGY_NOTES_DIR` exists, offer to maintain `$YONTOLOGY_NOTES_DIR/Project Decision Index.md` for cross-project recall. Request the narrowest write permission before touching that path.

Keep each entry compact: project, date, status, one-sentence decision, and a link to the repository ADR. Never copy the full ADR. If permission is denied, leave the repository record complete and do not write an alternate global index.

## Verify and Report

Before finishing, verify that:

- the ADR ID and filename are unique;
- the chosen option is traceable to user confirmation;
- inferred claims are labeled;
- at least one downside or `None identified` is present;
- guardrails, validation, and revisit triggers are concrete;
- source and supersession links resolve when local;
- the project index matches the ADR status;
- no template placeholders remain.

Report the created or updated ADR and index with clickable absolute paths. Mention any unresolved rationale, deferred validation, or skipped cross-project index.
