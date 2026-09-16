---
name: seed-docs-suite
description: Create or refresh a complete, internally traceable product-documentation suite from an approved Ouroboros Seed, PRD, or confirmed product requirements. Use when Codex is asked to turn a Seed into docs/prd.md plus English-named screen-flow, feature-specification, high-fidelity HTML wireframe, authorization-policy, ERD, API-specification, and QA-test-case documents; or when the user repeats a request for a coordinated product planning and delivery document pack.
---

# Seed Docs Suite

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

Create one coherent product documentation set whose downstream documents trace back to a single PRD.

## Workflow

1. Resolve the source of truth.
   - Prefer the latest user-approved, QA-passed Seed YAML.
   - Otherwise use an explicitly identified existing PRD or confirmed requirements supplied by the user.
   - Inspect the repository for relevant product, architecture, and design artifacts before drafting.
   - If sources conflict, preserve the newest explicit user decision and list unresolved conflicts; never resolve a product decision silently.
   - If no coherent source exists, ask for the Seed, PRD, or requirements summary before writing.

2. Inspect the destination.
   - Use `docs/` at the repository root unless the user names another directory.
   - Check every target file before editing.
   - Preserve unrelated content and user changes. If an existing target conflicts materially with the source of truth, explain the conflict before overwriting it.

3. Read [references/document-contract.md](references/document-contract.md) completely before authoring. Follow its filenames, required sections, identifiers, and traceability rules.

4. Build the suite in dependency order.
   - Write `docs/prd.md` first and treat it as the canonical product contract.
   - Stabilize requirement IDs, roles, terms, priorities, assumptions, and acceptance criteria.
   - Author the seven downstream documents from the PRD. Work on independent documents in parallel when safe, then reconcile them against the PRD.
   - Do not add features merely to fill a template. Mark genuine open decisions as `TBD` with an owner or decision point.

5. Keep the output names in English exactly as defined in the document contract, even when document content is Korean.

6. Validate the complete set.
   - Confirm all required files exist and contain no placeholder prose such as `TODO` except intentional, itemized `TBD` decisions.
   - Confirm Mermaid fences use the required diagram type and parse structurally.
   - Confirm the wireframe contains a complete standalone HTML document in a fenced `html` block. Do not create an extra `.html` file unless requested.
   - Confirm every P0 feature maps to at least one screen or non-UI rationale, authorization rule, entity or explicit stateless rationale, API or local-only rationale, and QA case.
   - Confirm role names, entity names, endpoint names, priorities, and requirement IDs are consistent across files.
   - Confirm all user-approved out-of-scope and post-MVP items remain excluded from P0 acceptance criteria.
   - Inspect the final diff and report unresolved decisions and validation limits.

## Editing Rules

- Use `apply_patch` for file edits.
- Keep diagrams and tables readable rather than exhaustive.
- Prefer observable outcomes in acceptance criteria; keep implementation steps in the feature plan or architecture sections.
- Do not invent legal, privacy, security, platform-version, scale, or performance commitments. Convert missing commitments into explicit decisions unless the source already fixes them.
- Keep API and ERD technology-neutral unless the approved source selects a stack.
- Treat authorization as server-enforced even when the client hides unavailable actions.
- Include destructive-action confirmations, ownership checks, and audit requirements where the product actually needs them.
- Preserve the product's approved visual direction in the high-fidelity wireframe; derive tokens rather than introducing a new aesthetic.

## Handoff

Summarize:

- source artifact used and its approval status;
- files created or updated;
- P0 critical path and parallel workstreams;
- unresolved `TBD` decisions;
- checks performed and any checks that could not be run.
