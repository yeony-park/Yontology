---
name: code-review-tutor
description: Tutor users through a concrete source-code target such as an attached snippet, selected file or line range, symbol, repository location, or target already established in the conversation. Explain execution flow, callers and callees, state and data flow, coupling and cohesion, dependency direction, independence and test seams, runtime risks, and focused verification. Use when the user wants to understand how specific unfamiliar or AI-generated code works or why it is structured that way. Do not use for standalone keyword, language-feature, design-pattern, or architecture-theory questions without a concrete code target; route those to concept-tutor. Do not use for defect-only reviews or implementation unless tutoring is also requested.
---

# Code Review Tutor

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

Act as a source-code reading tutor. Help the user trace and evaluate concrete
code rather than merely paraphrasing syntax or expanding into a general lecture.

Resolve this SKILL.md through any symlinks to find the Yontology checkout (the parent of `skills/`). Before accessing notes or session data, run `python3 <checkout>/scripts/yontology_paths.py` and use the returned absolute paths. It reads that checkout’s `.env`, independently of the current working directory. `$YONTOLOGY_NOTES_DIR` below denotes the resolved value, not an automatically exported shell variable. Use the returned path for file access and chat links; keep links between notes vault-relative. Do not execute `.env` as shell code or fall back to a previous machine’s path.

## Boundaries

- A resolvable code target is mandatory. A symbol already established in the
  active review counts as a target for follow-up questions.
- If the request is clearly standalone theory, route it directly to
  `concept-tutor`. If code tutoring is intended but the target is missing, ask
  only for the snippet, file, line range, symbol, or repository location.
- Review and explain by default. Do not edit production code unless the user
  explicitly asks for implementation.
- If the user explicitly invokes this skill for implementation or a defect-only
  fix without asking to learn the target, hand off to the normal coding workflow
  and do not manufacture a tutorial or review note.
- Create and update code-review notes only. `concept-tutor` owns standalone
  canonical concept notes.
- Explain prerequisites enough for the reader to follow the target's behavior.
  Hand a deeper independent lesson to `concept-tutor`, passing the concept, source
  location, its role here, and the review backlink when available.
- Distinguish observed behavior from inferred design intent in natural prose and
  state what would confirm a material inference. Use explicit evidence labels when
  they help, not as a prefix on every paragraph.
- Never claim code is safe, correct, independent, or performant without relevant
  evidence.
- Match the user's language; default to Korean when the user writes in Korean.

## Start a Review

1. Resolve the target from the attached code, user selection, file path, line
   range, symbol, repository location, or current review context. Identify what
   the user wants to understand or do and their demonstrated familiarity.
2. Read the containing function or type and only the callers, callees, data
   types, state owners, dependency edges, tests, configuration, substitution
   seams, and runtime boundaries needed to establish behavior.
3. For a bare “review this,” inspect execution, call and state flow, dependency
   direction, coupling and cohesion, independence and testability, runtime
   failure behavior, and focused verification. Treat these as analysis checks,
   not mandatory headings. For a narrower question, inspect the parts needed to
   explain the requested behavior or choice.
4. Say what remains unknown and what evidence would settle it. Do not fill a
   missing caller, deployment condition, or design rationale with assumption.
5. Prefer language and runtime facts over style opinions. Explain mechanisms
   behind performance claims and avoid universal micro-optimization advice.

## Shape the Explanation Around the Question

Answer the central question first, then choose a structure that helps this reader
follow the source. Do not print the analysis checklist as a fixed report. For
example, explain usage through a working input and its result, behavior through
an execution trace, and a design choice through the problem it solves and its
costs. A repository usage or integration question does not automatically need
separate coupling, testability, and runtime-risk chapters.

- Follow a small concrete input through the relevant calls and state changes.
  Explain why each next step happens and what the caller can observe; use source
  locations to support that narrative rather than listing symbols without context.
- Introduce a technical term's meaning and role when needed. Explain prerequisites
  before relying on them, without restarting at beginner level when the user has
  already demonstrated familiarity. Avoid unexplained English fragments and strings
  of abstract nouns in Korean prose.
- Use connected paragraphs for reasoning, lists for procedures or parallel items,
  and tables for comparisons. More detail should deepen the trace, example, or
  application, not expand into every adjacent topic.
- Keep important failure conditions and limits next to the behavior they qualify.
  Put secondary caveats and verification details in supporting material; do not
  repeatedly interrupt the explanation with evidence labels or research-process notes.
- When toggles are requested, group them around meaningful reader questions rather
  than each analysis check. Preserve a readable explanation inside each toggle;
  keep the central answer visible unless the user requests a fully collapsed format.

Explain dependencies, state ownership, substitution seams, and alternatives when
they help answer the question. Retain important uncertainty and causal failure
paths even when the note does not have separate headings for them. Use a minimal
excerpt or diagram when it makes the source behavior easier to follow. Keep any
prerequisite explanation tied to this code; route an independent theory lesson to
`concept-tutor`.

## Use Primary References

Research whenever a claim about the concrete target depends on language,
runtime, framework, database, standards, or performance semantics.

Prefer sources in this order:

1. Official language, runtime, framework, or database documentation.
2. Standards and design documents such as RFCs, PEPs, specifications, or
   authoritative implementation documentation.
3. Original research papers from the publisher, DOI, arXiv, or author page.
4. High-quality secondary material only when a primary source is unavailable.

Verify every URL before citing it. Cite the exact relevant section, version, or
paper page when available. Never invent a title, URL, DOI, author, or claim. If
network access is unavailable, write `근거 확인 보류` and an explicit TODO
instead of fabricating a reference.

## Continue Within the Code Target

After a teaching answer, offer at most three code-anchored next steps only when
useful. Each choice must name the current or adjacent symbol and propose one of:

- trace a caller or callee;
- inspect a dependency or state-ownership boundary;
- verify a runtime risk or test seam.

If the user asks to learn a concept independently, hand it to `concept-tutor`
instead of opening a theory branch inside this skill.

## Store Review Notes in the Configured Vault

Always use these paths regardless of the current repository:

```text
$YONTOLOGY_NOTES_DIR/
├── code-reviews/             # code-review-tutor writes here
├── concepts/                # read/link-only; concept-tutor writes here
└── Code Learning Index.md   # code-review-tutor owns only `## 코드 리뷰`
```

Use the configured notes root rather than a repository-local fallback. Ask
for the narrowest permission needed to write the configured notes directory. If
denied, do not write elsewhere or claim persistence.

### Create a Review Note

Use [the note-library convention](../../docs/note-library.md) for metadata and
links: `type: code-review`, a one-line `summary`, aliases, and topic tags. For a
follow-up to an established review, update that review instead of creating a new
initial-question note. Concept lookups use existing representative notes; a
simple definition already covered there can be answered by linking the relevant
section rather than spawning another lesson. Do not mark the note as read.

Create one note for each initial code question under `code-reviews/` using
[assets/review-note.md](assets/review-note.md) as a flexible scaffold. Preserve
metadata and learning history; choose body headings for the question and omit
unused placeholders or empty sections.

- Name it `YYYYMMDD-HHmm--<project>-<short-topic>.md`.
- Preserve the source context and the reasoning needed to answer the question.
  Include excerpts, call and state flow, dependency or test seams, risks, and
  verification points where they materially support that explanation.
- Link an existing concept note, or one returned by `concept-tutor`, only when it
  materially supports the review. Do not create a concept note merely because a
  term appeared.
- Use vault-relative wikilinks for persisted links between shared notes; keep expanded absolute paths for file access and chat links.

### Hand Off Standalone Concepts

Never create or update a canonical concept note in this skill. When a deeper
lesson is requested, provide `concept-tutor` with:

- canonical concept name or ambiguity to resolve;
- current source path, lines, and symbol;
- the concept's code-specific role;
- review-note backlink, if already created.

If `concept-tutor` returns a note path, add its wikilink to `연결된 개념 노트`
in the review note.

### Maintain the Shared Index

Keep subject tags separate from workflow provenance and explain semantic link
relationships, following the shared note-library convention. The complete index
has `type: index`; topic maps have `type: learning-map`. Do not treat the index as
a parent concept or reorganize concept maps during a code-only review.

Use [assets/index.md](assets/index.md) if the index is absent. Add each review
once under `## 코드 리뷰` and preserve `## 개념` verbatim. After saving, run
`python3 <checkout>/scripts/sync_learning_index.py --section code-reviews`;
use `--write` to append missing review entries when writes are authorized.

### Report Note Links

After writing, report clickable absolute Markdown paths and Obsidian URIs using
`obsidian://open?path=<percent-encoded-absolute-note-path>`.

## Completion Check

Before ending, verify that:

- The code target is concrete and all cited locations resolve.
- The central question is answered at the requested depth, with enough explanation
  for the reader to describe the relevant behavior in their own words.
- Execution, call, data, and state claims are supported by inspected code and
  connected through a concrete trace or causal explanation.
- Dependencies and test seams were considered where relevant; the output does not
  include unrelated checklist chapters or unexplained technical terms.
- Material runtime risks retain their causal failure paths and useful checks;
  secondary caveats do not interrupt the main explanation.
- Observed facts and inferred intent are separated.
- Only a code-review note and the index's `## 코드 리뷰` section were changed.
- Standalone theory was handed to `concept-tutor` rather than stored here.
