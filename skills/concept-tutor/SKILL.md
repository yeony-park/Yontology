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
- Separate source-confirmed facts from interpretation or project-specific
  inference. Label the latter `추정` and state what would confirm it.
- Resolve a standalone concept here even if it arose during a code review. If
  the user instead asks how a resolvable source target uses the concept, hand
  the request to `code-review-tutor` with that target intact.
- Never turn a product choice into an accepted decision merely because it was
  used as an example. Preserve `확정`, `후보`, and `미정` boundaries.

## Start a Lesson

1. Identify the requested concept and intended depth. If an acronym has several
   plausible technical meanings that would change the answer, disambiguate it
   before writing a canonical note.
2. Follow [note discovery and roles](../../docs/note-library.md): search filenames,
   titles, aliases, and relevant body text, then read the matching notes. Do not
   rely on the index alone. Resolve a supplement to its canonical target.
   For a simple concept question already answered there, say it is documented,
   link the note and relevant section, and stop the full-lesson workflow. Reading
   the note is sufficient; do not force a quiz or mark reading as completed.
   Honor requests to explain again. For follow-ups, teach and persist only the
   missing explanation rather than repeating or duplicating the whole lesson.
3. Read [references/source-policy.md](references/source-policy.md) completely,
   then research the concept from primary sources. Use current browsing for
   claims that may have changed.
4. Determine the concept boundary, causal mechanism, nearest confusing concept,
   tradeoffs, failure modes, and a way to verify or observe it.
5. Teach first, then create or update the canonical Markdown note and index
   unless the user opted out of persistence.

## Choose the note depth

For a word, developer term, or standards term, use a concise canonical concept
note: definition, context, example, confusion/limit, and verified primary source.
Use [assets/term-note.md](assets/term-note.md). Keep `type: concept`; `terminology`
is only an optional style tag. Expand the same file for a deeper follow-up rather
than creating a separate glossary copy. The full lesson sequence below applies
when mechanism or depth warrants it; short terms do not need every heading.

## Teach in This Order

1. **한 줄 정의**: Give the shortest accurate explanation.
   On first use in every answer and note, write an established full term before
   its abbreviation, for example `Mixture-of-Experts (MoE)` and
   `Feed-Forward Network (FFN)`; use the abbreviation alone afterward.
   For an acronym-focused lesson, include the English expansion and Korean name
   in each note's title and first definition. When the user prefers acronym-first
   notation, use `SFT (Supervised Fine-Tuning, 지도 미세조정)` instead. Put common
   Korean translations in aliases without claiming a single official translation.
2. **적용 범위와 한계**: State what the concept includes and does not solve.
3. **작동 원리**: Explain the causal sequence, not only terminology.
4. **헷갈리는 개념과 비교**: Contrast the closest alternative or homonym.
5. **발전 과정**: Include only when history, standards, or a paper lineage
   matters; avoid inventing a single linear lineage for branching research.
6. **장단점과 실패 양상**: State costs, assumptions, limits, and where a claim
   stops generalizing.
7. **적용과 검증**: Give a small example or an observable test without turning
   an unchosen project design into a decision.
8. **근거 자료**: Cite the exact official section, standard, or original paper.

Use equations, tables, or a tiny example only when they make the mechanism more
precise. For paper comparisons, report model or system scale, experimental
conditions, publication status, and the metric denominator needed to interpret
headline numbers.

### Structured Explanations

- Use descriptive subsections, numbered causal steps, and comparison tables so
  the reader can distinguish inputs, outputs, assumptions, and tradeoffs.
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

Apply the metadata and duplicate-resolution rules in
[the note-library convention](../../docs/note-library.md). Record `type` and a
one-line `summary`; use aliases and tags for names/topics. A learning map,
bilingual reference, and concept explanation have different roles. Retain actual
duplicates as linked supplements when they contain distinct examples or history;
use a verified vault-relative `canonical` target and a reciprocal visible link.

Use [assets/concept-note.md](assets/concept-note.md) and one canonical file per
meaningful concept.

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
- Give each new note a meaningful subject tag; retain workflow tags as provenance.
- Explain the relationship beside semantic links; add reciprocal links when useful.
  A shared authoring tool is not a conceptual relationship.
- Reuse suitable topic maps (`type: learning-map`) in `concepts/`, with navigation
  backlinks under `## 탐색` and a return entry on the map. Use
  [assets/topic-map.md](assets/topic-map.md) only when a new map adds useful
  navigation. Topic maps link explanations rather than duplicate them.
- Use vault-relative wikilinks for links stored between shared notes. Expand home-relative paths only for file access and chat links, so another Mac does not inherit this Mac's username.
- A code source, project example, and code-review backlink are optional. When a
  code-review handoff supplies them, add them under `프로젝트·코드 연결` and
  link the concept note back to the review.
- Record verified source URLs and relevant sections. Write `근거 확인 보류` plus
  a concrete TODO when primary evidence cannot be reached.

### Maintain the Shared Index

Keep the shared index a complete catalog (`type: index`), separate from topic
maps and provenance tags. Follow the role separation and bulk-reorganization
rules in [the shared convention](../../docs/note-library.md). Routine lessons
update their own notes and relevant maps; do not reorganize the whole vault unless
requested. Use [assets/index.md](assets/index.md) if absent. Add or update one
entry in `## 개념` and preserve `## 코드 리뷰` verbatim. Never duplicate an
entry when a note is refreshed. After writing, audit with
`python3 <checkout>/scripts/sync_learning_index.py --section concepts` and append
missing entries with `--write` when writes are authorized. Cover every note role
in `concepts/`; do not silently omit translations, maps, or supplements. Keep the
index maintenance scope within this section unless library-wide repair is requested.

### Report Note Links

After finding an existing note or writing one, report clickable absolute Markdown
paths and an Obsidian URI:

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

- For an existing-note lookup, the matched scope was read and the user received
  working note links; no redundant full lesson or invented read/mastery event was
  required. The remaining teaching checks apply when actually teaching.
- A full lesson covers definition, boundary, mechanism, and tradeoff; a concise
  term note covers definition, context, example, confusion/limit, and source.
- Claims are backed by verified primary sources at the right scope.
- Facts, inference, and unchosen project options are distinguishable.
- The canonical note was reused when appropriate, its document role is explicit,
  and its primary index entry exists. Retained duplicates point directly to it.
  Read-only lookups and persistence opt-outs do not require library repairs.
- Routine lessons change only `concepts/` and the index's `## 개념` section.
  A requested library reorganization may also update catalog metadata/navigation
  and retained index supplements; preserve unrelated sections. Persistence
  opt-outs produce no file changes.
- Subject tags, topic navigation, semantic links, and workflow provenance have
  distinct roles. Added map links resolve and have return entries; semantic links
  state their relationship without manufacturing dependencies.
- Acronym expansions and Korean names are present for acronym-focused lessons;
  useful diagrams, reading guidance, and follow-up question examples are included.
