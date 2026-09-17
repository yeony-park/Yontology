---
name: concept-tutor
description: Research and teach standalone technical concepts, keywords, language or runtime mechanisms, design patterns, architecture principles, standards, protocols, and research topics from verified primary sources, then create or reuse a canonical Obsidian Markdown learning note. Use when the user asks what a concept means, wants a comparison, historical development, tradeoffs, or an official-document or paper-based synthesis without a concrete code target. Do not use when the question is anchored to an attached snippet, file, line range, symbol, or repository location and asks how that code behaves; route that request to code-review-tutor.
---

# Concept Tutor

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

Teach theory as an evidence-backed, reusable body of knowledge. Keep the lesson
independent of any one codebase unless a project example materially clarifies it.

Resolve this SKILL.md through any symlinks to find the Yontology checkout (the parent of `skills/`). Before accessing notes or session data, run `python3 <checkout>/scripts/yontology_paths.py` and use the returned absolute paths. It reads that checkout’s `.env`, independently of the current working directory. `$YONTOLOGY_NOTES_DIR` below denotes the resolved value, not an automatically exported shell variable. Use the returned path for file access and chat links; keep links between notes vault-relative. Do not execute `.env` as shell code or fall back to a previous machine’s path.

## Boundaries

- Research, explain, and maintain learning notes by default. Do not edit
  production code unless the user separately asks for implementation.
- If the user explicitly asks not to save or update notes, teach only: skip all
  vault and index writes, skip persistence-only completion checks, and report
  that nothing was written.
- Match the user's language; default to Korean when the user writes in Korean.
- Distinguish source-confirmed facts from interpretation or project-specific
  inference in natural prose; state what would confirm a material inference.
  Use explicit evidence labels when they help, not as a prefix on every paragraph.
- Resolve a standalone concept here even if it arose during a code review. If
  the user instead asks how a resolvable source target uses the concept, hand
  the request to `code-review-tutor` with that target intact.
- Never turn a product choice into an accepted decision merely because it was
  used as an example. Preserve `확정`, `후보`, and `미정` boundaries.

## Start a Lesson

1. Identify what the user wants to understand or do, the requested concept,
   and the intended depth. Use the conversation to gauge familiarity rather
   than restarting every lesson at beginner level. If an acronym has several
   plausible technical meanings that would change the answer, disambiguate it
   before writing a canonical note.
2. Search existing concept-note `title` and `aliases` before creating anything.
   Reuse the canonical note when the meaning matches; never fork a synonym into
   a duplicate file.
3. Read [references/source-policy.md](references/source-policy.md) completely,
   then research the concept from primary sources. Use current browsing for
   claims that may have changed.
4. Investigate the concept boundary, causal mechanism, relevant comparisons,
   tradeoffs, and ways to observe it. These are analysis checks, not required
   sections in every explanation.
5. Teach first, then create or update the canonical Markdown note and index
   unless the user opted out of persistence.

## Shape the Lesson Around the Question

Answer the central question first, then choose the order that helps this reader
understand it. Do not turn the analysis checks or note template into a fixed
outline. A first explanation may follow a concrete problem through its solution;
a comparison should develop the differences that affect a choice; an application
question should connect the mechanism to the user's situation. These are examples,
not mandatory modes or headings.

- Build connected paragraphs: show what happens, why the next step is needed,
  and what changes as a result. A list of terms or arrows alone is not an explanation.
- When the mechanism is abstract, follow one small example through it before
  generalizing. Define a technical term's meaning and role when it becomes needed;
  avoid unexplained English fragments and strings of abstract nouns in Korean prose.
- Match the requested depth and demonstrated knowledge. More detail should deepen
  the mechanism, example, or application, not add unrelated topics or more headings.
- Introduce limitations where they change the reader's understanding or decision.
  Keep essential qualifications beside the claim; move secondary exceptions and
  verification detail to optional supporting material instead of interrupting each
  paragraph with warnings or accounts of the research process.
- Include comparisons, history, equations, or failure cases when they answer the
  question. Do not fill an irrelevant section merely because a template lists it.
  Preserve branching research histories rather than inventing a linear lineage.

On first use, introduce an established full term with its abbreviation, such as
`Mixture-of-Experts (MoE)`, and explain its role rather than relying on the expansion
alone. For acronym-focused lessons, retain the English expansion and Korean name
in the note title and first definition. Honor acronym-first preferences such as
`SFT (Supervised Fine-Tuning, 지도 미세조정)`; place common translations in aliases
without claiming a single official translation.

For paper comparisons, keep the system scale, experimental conditions, publication
status, baseline, and metric denominator needed to interpret headline numbers.
Adapt their presentation without dropping material evidence or uncertainty.

### Structured Explanations

- Use paragraphs for connected reasoning, lists for procedures or parallel items,
  and tables for comparisons. Add descriptive subsections when they help navigation.
- When toggles are requested, group them around meaningful reader questions rather
  than each analysis check. Preserve a readable explanation inside each toggle;
  keep the central answer visible unless the user requests a fully collapsed format.
- Include a fenced `mermaid` diagram in notes about multi-step mechanisms,
  training loops, architecture, or concept relationships when it clarifies the
  explanation. Keep it compatible with Obsidian and explain it in prose too.
- Label arrows by their meaning where needed. Distinguish data flow, parameter
  updates, containment, and optional combinations; do not draw different design
  axes as a mandatory sequence or imply that alternatives must all be used.
- Define symbols beside useful equations and include a small worked example.
  Skip decorative diagrams and equations that do not improve understanding.
- For an in-depth note, provide a short primary-source reading list: official
  documentation plus original papers where relevant, with reading order, the
  section to read, and why it helps. Prefer relevant evidence over link counts;
  distinguish paper versions and do not imply peer review from arXiv hosting.

## Store Canonical Notes

Always use these configured paths regardless of the current repository:

```text
$YONTOLOGY_NOTES_DIR/
├── concepts/                 # concept-tutor owns these notes
├── code-reviews/             # read/link-only here
└── Code Learning Index.md    # concept-tutor owns only `## 개념`
```

Request the narrowest permission required to write there. If permission is
denied, do not silently write to a project-local fallback or claim persistence.

### Create or Reuse a Concept Note

Use [assets/concept-note.md](assets/concept-note.md) as a flexible scaffold and keep
one canonical file per meaningful concept. Preserve metadata and learning history;
choose body headings for the question and omit unused placeholders or empty sections.

- Name the file with a stable, established lowercase kebab-case slug.
- Normalize established Korean and English names under `aliases`.
- If an existing title or alias has the same meaning, update that file while
  preserving prior correct material and learning history.
- For a family of papers or related mechanisms, prefer one non-duplicative
  umbrella note that links existing focused notes; split separate meanings only
  when each needs an independent definition, mechanism, or review schedule.
  Honor an explicit request for separate concept notes. Keep the umbrella as a
  comparison and navigation page, move detailed explanations into the focused
  notes, and preserve prior learning history and relevant source links.
- If the same spelling names different concepts, keep separate qualified notes
  and explain the distinction instead of merging them.
- Add bidirectional wikilinks to genuinely related concept notes.
- Use vault-relative wikilinks for links stored between shared notes. Expand home-relative paths only for file access and chat links, so another Mac does not inherit this Mac's username.
- A code source, project example, and code-review backlink are optional. When a
  code-review handoff supplies them, add them under `프로젝트·코드 연결` and
  link the concept note back to the review.
- Record verified source URLs and relevant sections. Write `근거 확인 보류` plus
  a concrete TODO when primary evidence cannot be reached.

### Maintain the Shared Index

Use [assets/index.md](assets/index.md) if the index is absent. Add or update one
entry in `## 개념` and preserve `## 코드 리뷰` verbatim. Never duplicate an
entry when a note is refreshed.

### Report Note Links

After writing, report clickable absolute Markdown paths and an Obsidian URI:

```text
obsidian://open?path=<percent-encoded-absolute-note-path>
```

If Obsidian cannot resolve it, tell the user to open
`$YONTOLOGY_NOTES_DIR` once with **Open folder as vault**.

## Continue the Lesson

Offer at most three adjacent concepts only when a next step is useful. Keep each
choice as a concrete example question the user can ask, and explain why it
follows. Include these questions after reporting saved note links. A request tied
back to a specific source target returns to `code-review-tutor` rather than
growing a code-analysis branch here.

## Completion Check

Before ending, verify that:

- The central question is answered at the requested depth, with enough explanation
  for the reader to describe the key idea in their own words.
- The mechanism is connected through causes and effects or a concrete example;
  necessary terms are explained before the reader must reason with them.
- Boundaries and tradeoffs that affect the answer remain visible, while irrelevant
  checklist sections and repeated qualifications have been removed.
- Claims are backed by verified primary sources at the right scope.
- Facts, inference, and unchosen project options are distinguishable.
- The canonical note was reused by title or alias when appropriate, unless the
  user opted out of persistence.
- Only `concepts/` and the index's `## 개념` section were changed, or no files
  were changed when persistence was declined.
- Related notes are linked without manufacturing relationships.
- Acronym expansions and Korean names are present for acronym-focused lessons;
  diagrams, reading guidance, and follow-up questions are included only when useful.
