# Learning-note discovery and roles

Use this convention for Concept Tutor and Code Review Tutor notes. Daily Learning
Tutor uses the same roles to avoid duplicate or non-concept reading assignments.
Resolve the notes root with `scripts/yontology_paths.py`; never persist this
machine's absolute vault path in a shared note or skill.

## Find before teaching

Search filenames, `title`, `aliases`, and then headings/body text with Korean,
English, and abbreviation variants. The index is a navigation aid, not an
exhaustive search boundary. Read matching notes and their scope before deciding
that a lesson already exists. Matching keywords alone do not establish equivalence.

For a simple definition request already answered by a suitable canonical note,
say that it is already documented and provide an absolute Markdown file link and
`obsidian://open?path=<percent-encoded-absolute-note-path>`. Point to the relevant
section and give at most a brief orientation. Reading that note is a sufficient
next step; do not recreate the lesson, force a quiz, or require acknowledgement.
Do not mark it as read or mastered merely because a link was offered or opened.
If asked to open it, use an available file-opening tool; a link alone is not proof
that an application opened the document.

For a follow-up, identify what is missing and answer that gap. Add the new
explanation to the representative note, preserving earlier correct content,
source links, and learning history. An explicit request for a fresh explanation,
comparison, different depth, or correction takes precedence over reuse-only
routing. Refresh volatile facts and stale sources when the question needs them.

## Metadata

Keep existing `title`, `aliases`, `tags`, dates, and history. Add:

- `type`: one role from the table below; this describes the document, not its topic.
- `summary`: a single-line description of what the reader can find here.
- `canonical`: only on a retained duplicate/supplement; the representative note's
  vault-relative path, including `.md`. Omit on the representative itself.

Use single-line text for these fields; quote strings containing YAML punctuation.
The index helper supports plain, single-quoted, or JSON-compatible double-quoted
scalars. It does not rewrite YAML or infer missing semantic metadata.
Use existing `tags` for topics rather than introducing a second mandatory topic
list. Put real synonyms, Korean terms, and common abbreviations in `aliases`.

| type | Purpose |
| --- | --- |
| `index` | Complete catalog for finding notes; not a lesson or prerequisite map |
| `concept` | Representative explanation of a distinct concept, including a short term note |
| `learning-map` | Reading order and relationships among separate concepts |
| `bilingual-reference` | Source paragraphs paired with translations |
| `supplement` | Retained same-concept material linked to a representative |
| `code-review` | Explanation anchored to concrete source code |

A learning map and a translation of the same source have different purposes and
are not duplicates. Link them as related reading; do not use `canonical` to imply
one supersedes the other. Preserve paragraph boundaries in bilingual references:
one original paragraph followed by its translation, with lists/code preserved.
Do not substitute links or summaries for supplied source text.

## Separate navigation, meaning, and provenance

- **Complete catalog:** `Code Learning Index.md` has `type: index`. Keep one
  primary entry per note in the owned section, including maps and supplements.
  The catalog answers “what exists?”; its links do not imply prerequisites.
- **Topic navigation:** topic tags describe subject matter (for example,
  `version-control` or `networking`). Reuse the library's existing vocabulary.
  A `type: learning-map` note in `concepts/` explains scope, useful reading paths,
  and how its linked notes differ. Reuse a suitable map before creating another;
  do not create a map for every isolated term. A note may belong to several topics.
- **Semantic relationships:** put a reason beside concept links, such as
  “compares with”, “uses”, or “specializes”. Add reciprocal links when useful,
  with a truthful relationship in each direction. Shared tags or shared authorship
  alone do not establish a conceptual dependency. Keep map backlinks under
  `## 탐색` separate from `## 연결된 개념`; navigation is not a parent concept.
- **Authoring provenance:** `concept-tutor` and `code-review-tutor` identify the
  workflow that produced material, not the subject or a conceptual parent.
  Preserve established provenance; do not add a new authoring tag merely because
  a maintenance pass touched a note. `terminology` is an optional note-style tag,
  not a topic or a new document role. New concept notes need a meaningful topic
  tag in addition to any workflow/style tags.

A topic map should link existing notes with short navigation annotations rather
than copy their definitions. Keep its contents compatible with the catalog:
list the map itself once in `## 개념`; do not repeat its member entries there.
New or substantially updated notes should link a suitable existing topic map,
with a return entry on that map. If none fits, a topic tag is enough.

For a requested library-wide reorganization, inventory filenames, roles, aliases,
and content first. Preserve stable filenames, source material, learning history,
quiz state, and unrelated sections. Review older index copies: retain unique
annotations as a `supplement` with a direct `canonical` link to the main index
and a visible reciprocal link. Do not silently delete them or treat them as a
second live catalog. Snapshot affected files before bulk writes, check for
concurrent edits, and verify catalog coverage, all added link targets, topic-map
return links, and preservation afterward. Keep personal vault contents and
machine paths out of public skill repositories.

## Concise terminology notes

A developer term or a standard's vocabulary is still a `concept`. Start with
**definition → scope/context → example → confusing neighbor or limitation →
primary source**. Record the defining tool, standard, or version when the meaning
is context-dependent. Do not pad a short note with empty mechanism, history,
diagram, or quiz sections. Grow the same canonical file when understanding deepens;
do not keep separate glossary and full-lesson copies of the same definition.
A comparison note is appropriate for a paired question; split only when each
meaning needs independent explanation or review. A glossary or topic map links
to these notes rather than maintaining another copy of their definitions.

## Resolve actual duplicates

Compare definitions, scope, unique explanations, source evidence, existing links,
and learning history. Prefer a stable, already-linked path for the representative
when appropriate; do not blindly choose the newest or longest note.

Mark a retained duplicate `type: supplement` with `canonical: concepts/<slug>.md`
and a visible link near its beginning. Add a reciprocal link in the representative
so unique examples and history remain discoverable. Add missing synonyms to the
representative's aliases. Do not delete or rename files, overwrite history, merge
homonyms, or treat an umbrella concept and its specialization as duplicates merely
because they share keywords. Never create canonical chains or cycles; verify the
target exists and is the actual representative.

Only merge unique material when its meaning and evidence are clear. A linked
supplement is an acceptable resolution without copying its whole body. A repeated
question does not itself prove that the user has read or forgotten a note.

## Index maintenance

The shared index has separate owned sections: `## 개념` and `## 코드 리뷰`.
Each note in the corresponding folder, including maps, translations, and retained
supplements, needs one primary entry. Show role and representative links where
relevant. Preserve curated descriptions and the other section verbatim.

Audit the filesystem against the index after note creation or renaming:

```bash
python3 scripts/sync_learning_index.py --section concepts
python3 scripts/sync_learning_index.py --section code-reviews
```

The default is read-only and exits 1 for missing or duplicate primary entries.
Use `--write` to append missing entries in the selected section. This is
idempotent, keeps existing entries and prose, and never changes note bodies.
It recognizes vault-relative and bare-filename wikilinks, aliases, headings,
`.md` extensions, and Unicode normalization. Use vault-relative links when
writing new entries. Duplicate entries are reported for manual review, not
silently removed. Semantic duplicates and stale/broken unrelated links still
require inspection; this helper does not decide which concepts are equivalent.

Routine Concept Tutor work selects `concepts`; Code Review Tutor selects
`code-reviews`. `--section all --write` is for an explicitly requested library
repair, not a reason to edit another skill's section during normal teaching.
`--notes-dir` overrides the configured root for isolated tests or an explicit
alternate library. Library maintenance may update metadata/indexes without
pretending a lesson or review happened.
