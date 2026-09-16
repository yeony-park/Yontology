---
name: project-decision-journal
description: Persist material project decisions and their reasoning as repository ADRs, with portable copies and a cross-project index in the configured notes vault. Use after the user confirms a consequential product, architecture, data, security, API, vendor, or implementation choice following tradeoff discussion, asks to preserve its reasoning, or wants to share existing ADRs across computers. Ignore trivial, reversible, formatting, naming, and mechanical choices.
---

# Project Decision Journal

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

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

## Share ADRs in the Configured Notes Vault

Unless the user opts out of note sharing, publish a portable copy after creating or updating repository ADRs. For an explicit request to share existing ADRs, skip decision creation and locate the requested project's existing ADR directory. Keep repository documents authoritative and unchanged during sharing.

1. Resolve `YONTOLOGY_NOTES_DIR` and reuse the project's existing stable folder name under `decisions/`; otherwise derive a lowercase kebab-case project identifier. Resolve collisions before combining different projects.
2. Use the helper for conventional `ADR-*.md` documents and their `README.md`:

   ```bash
   python3 <skill-dir>/scripts/share_adrs.py --source-dir <project-adr-directory> --project <project-slug>
   ```

   It copies complete documents to `$YONTOLOGY_NOTES_DIR/decisions/<project-slug>/`, verifies their contents, and records hashes in `.adr-share.json`. Subsequent runs refresh unchanged copies from their sources; independently edited copies cause a conflict instead of being overwritten. Documents missing from the source are retained for review, never automatically deleted. For a different naming convention, preserve the repository convention and copy the explicitly selected ADRs with the same comparison checks rather than silently skipping them.
3. Keep relative links among ADRs and the copied project README working. Report references to code, PRDs, images, or other files outside the ADR directory as requiring the project repository; do not silently copy the entire project.
4. Maintain a project overview at `$YONTOLOGY_NOTES_DIR/decisions/<project-slug>.md` linking all shared ADRs. Record that these are snapshots of authoritative repository documents, when they were refreshed, and the repository-relative source directory. Do not put a machine-specific absolute source path in the shared overview.
5. Update `$YONTOLOGY_NOTES_DIR/Project Decision Index.md` to link to this overview and shared ADRs using vault-relative Markdown links or wikilinks. Keep existing confirmed summaries and history; do not infer new decisions during sharing. Avoid obsolete absolute links to another computer's checkout.

If the notes root is absent or write permission is unavailable, leave repository ADRs complete and report the sharing limitation. A copy operation verifies local content, not cloud upload completion. This helper is not a background watcher: rerun it after direct repository edits, and refresh copies during subsequent journal work. Respect the user's instruction not to save notes when given.

## Verify and Report

Before finishing, verify that:

- the ADR ID and filename are unique;
- the chosen option is traceable to user confirmation;
- inferred claims are labeled;
- at least one downside or `None identified` is present;
- guardrails, validation, and revisit triggers are concrete;
- source and supersession links resolve when local;
- the project index matches the ADR status;
- shared copies match their source documents and cross-project links resolve inside the vault, or the sharing limitation is explicit;
- no template placeholders remain.

Report the created or updated ADR, shared overview, and index with clickable absolute paths. Mention any unresolved rationale, deferred validation, copy conflict, external project references, or skipped sharing. Never claim another computer has synced based only on successful local copying.
