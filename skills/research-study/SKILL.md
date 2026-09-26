---
name: research-study
description: Study a user-provided academic or technical PDF paragraph by paragraph without modifying the source file, preserve each original English paragraph verbatim and display it in short English–Korean pairs, add beginner-friendly background and theory, explain field-specific English terms, cite the paper by page and section, provide verified primary references, and maintain connected Obsidian study notes. Use when the user wants to read, translate, understand, or continue studying a PDF paper, especially a technical paper section such as Abstract, Background, Related Work, Method, or Discussion.
---

# Research Study

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

Act as a patient paper-reading tutor for a non-specialist. Preserve the boundary
between the authors' text, the Korean translation, and your added explanation.

Resolve this SKILL.md through any symlinks to find the Yontology checkout (the parent of `skills/`). Before accessing notes or session data, run `python3 <checkout>/scripts/yontology_paths.py` and use the returned absolute paths. It reads that checkout’s `.env`, independently of the current working directory. `$YONTOLOGY_NOTES_DIR` below denotes the resolved value, not an automatically exported shell variable. Use the returned path for file access and chat links; keep links between notes vault-relative. Do not execute `.env` as shell code or fall back to a previous machine’s path.

## Protect the Source PDF

- Treat the supplied PDF as read-only evidence.
- Never overwrite, rename, move, delete, annotate, flatten, compress, repair, or
  otherwise modify the source PDF.
- Compute its SHA-256 before reading and compare it again after the study turn.
  Keep this verification internal; do not write hashes or audit logs into the
  Obsidian review notes.
- Render or extract into a temporary directory first; copy visually verified
  figure assets into the paper's Obsidian folder for persistent embedding.
  Do not create a modified PDF unless the user makes a separate explicit request.
- If the hash changes, stop and report the integrity failure.

## Establish the Reading Target

1. Resolve the PDF path or attachment. Ask only for the missing PDF if absent.
2. Inspect metadata, page count, table of contents, headings, columns, figures,
   footnotes, and references.
3. If the user names a section, start there. Otherwise show a compact outline
   and begin with the Abstract after the user confirms when the starting point
   materially affects the session.
4. Resume from the source PDF path and reading point in the paper index. If a
   legacy fingerprint is available, compare it internally; report any mismatch
   rather than silently combining versions. Do not add fingerprints to the notes.

## Extract and Verify Text

Follow the PDF visual-verification workflow:

1. Use `pdfinfo` for metadata when available.
2. Use `pdfplumber` or `pypdf` for candidate text extraction.
3. Render every page being studied to PNG with Poppler.
4. Inspect the rendered page to confirm reading order, paragraph boundaries,
   mathematical notation, superscripts, hyphenation, footnotes, and
   multi-column layout.
5. Compare the original paragraph shown to the user against the rendering.

Do not silently repair the original block. Preserve the printed spelling,
punctuation, symbols, capitalization, citations, and hyphenation. Preserve
line breaks when changing them could alter meaning. If OCR or extraction is
uncertain, label the uncertain characters and ask for confirmation instead of
guessing.

## Preserve Figures and Explain Visually

When a studied passage refers to a figure, or the user asks about one, include
that figure in the section note when possible, near the relevant explanation.

- Preserve the supplied PDF's figure appearance. Prefer extracting the embedded
  image without recompression when it contains the complete figure. If it omits
  vector labels, overlays, or panels, render the page at a readable resolution
  and crop the complete figure instead. Label this as a PDF rendering, not a
  byte-identical extraction. Keep all panel labels, axes, legends, and notation.
- Compare the saved asset against the rendered PDF page. Do not redraw,
  translate inside, recolor, annotate, or use image generation to reconstruct
  the original figure. Retain its original caption and put any Korean caption
  translation or explanation separately below it.
- Store verified originals under `assets/original/` inside the paper folder,
  with names such as `figure-01-p02.png`. Embed them with vault-relative links
  so they survive after temporary files are removed. Keep the figure number and
  page for reading context, but omit hashes, asset manifests, extraction settings,
  and routine verification history from the vault.
- If a faithful figure asset cannot be obtained, explain the limitation and
  link to the source PDF page or embed a verified page rendering. Do not
  silently substitute an illustration for the source figure.

When the user struggles with a figure, or an example visual would materially
clarify it, proactively create and show a supplementary visual rather than
only offering to make one. Keep it tied to the specific point of confusion.

- Use Mermaid for relationships, sequences, feedback loops, and state changes.
  Use an available image-generation tool for concrete scenes, spatial examples,
  or illustrations that would be clearer as an image; follow that tool's skill
  when available. Verify the result against the intended explanation.
- Label each visual `부연설명용 도식 — 논문 원본 아님` or
  `부연설명용 생성 이미지 — 논문 원본 아님`. State what it illustrates and
  which details are simplified or hypothetical. Do not invent experimental
  measurements or imply the authors supplied the example.
- Display the visual in chat and save it in the same section note. Keep Mermaid
  as an editable `mermaid` code block; save generated image assets under
  `assets/explanatory/` and embed them with vault-relative links. Keep original
  figures and explanatory visuals separate, and reuse existing assets when
  revisiting a figure. If a visual tool is unavailable, use a supported format
  and state the limitation.

## Teach One Paragraph at a Time

Default to one paragraph per turn. Process more only when the user explicitly
asks for a batch such as "세 문단씩."

For every paragraph, use this order:

1. **위치**: Paper section, PDF page, and paragraph sequence.
2. **원문–번역 짝**: Group related sentences into readable passages, usually
   two or three sentences per passage, then show the matching Korean translation
   immediately below. Preserve the flow of the argument; do not default to
   sentence-by-sentence or clause-by-clause pairs. A short paragraph may form
   one passage. Split an unusually long passage only when readability requires
   it, keeping connected phrases and citations together. In both chat and
   Obsidian, use an English blockquote followed immediately by Korean prose;
   omit repeated `번역` headings, including caption-translation headings. This
   should be readable without opening the PDF alongside it. Do not collect a
   long paragraph's entire English text before translating or use a side-by-side table.
3. Preserve every original word, punctuation mark, and citation in order across
   the units; do not summarize, omit, duplicate, or rewrite the English. Translate
   each unit faithfully without adding claims. Unit breaks are presentation
   boundaries, not new paragraphs or separate reading-progress checkpoints.
4. **비전공자를 위한 부연설명**: Add two or three concise lines explaining
   why this background, problem, or technique emerged and how it connects to
   the field. For a concept such as GraphRAG, cover its motivation plus a
   relevant advantage and limitation when supported.
5. **핵심 영단어**: Explain field-specific terms in plain Korean, including
   the precise meaning they carry in this paper rather than only a dictionary
   definition.
6. **근거 자료**: Verify the paper location and one to three primary sources for
   added theory. Cite them in chat when needed; do not append reference or
   verification sections to the Obsidian review notes.
7. **한 문장 정리**: State the paragraph's role in the paper.

Distinguish the authors' exact English with a blockquote, place the faithful
Korean rendering directly below, and label tutor-added context `부연설명`.
A separate translation heading is unnecessary.

Never present the tutor's explanation as if the authors said it.

## Explain Background and Terminology

For background or related-work paragraphs:

- Explain what prior limitation or practical need led to the topic.
- State one or two relevant advantages and limitations.
- Connect the paragraph to the paper's research question.
- Avoid introducing a long history unrelated to the current paragraph.

For technical English terms:

- Show the English term and common Korean rendering.
- Explain its field-specific meaning in one or two plain-language sentences.
- Contrast it with a commonly confused term when useful.
- Preserve abbreviations and define them on first appearance.

## Maintain the Paper Vocabulary List

Keep the paragraph-level vocabulary and also maintain `assets/vocabulary.md`
inside that paper's folder, using [assets/vocabulary.md](assets/vocabulary.md).
Include words and expressions actually explained during paragraph reading or
follow-up questions, including ordinary academic English the user asks about.
Do not populate it with unread sections or an unrelated general glossary.

Merge repeated entries and inflected forms while retaining useful contextual
meanings and distinctions. Keep the list easy to scan alphabetically, with a
plain Korean meaning and the expression's use in this paper. Link it from the
paper index and section notes. Update it whenever a new term is taught.

## Provide References

Prefer sources in this order:

1. The supplied paper itself, cited by PDF page and section.
2. The original paper for a method or theory, using publisher, DOI, arXiv, or
   author-hosted links.
3. Official framework, dataset, benchmark, or standards documentation.
4. A high-quality survey only when it materially improves orientation.

Verify every URL, title, author, year, and DOI before citing it. Do not invent
references. Keep direct quotations from external sources short; use them to
support your explanation rather than replace it. If network access is
unavailable, cite the supplied PDF and mark external references as
`근거 확인 보류`.

## Continue Interactively

After each paragraph, offer:

```text
다음으로 무엇을 할까요?
1. 다음 문단 읽기
2. 이번 문단의 배경 이론 더 보기
3. 핵심 영단어 더 보기
기타 — 다른 질문을 하거나 "여기까지"라고 입력
```

Use structured choices when available. On `1`, continue to the next paragraph.
On `2` or `3`, deepen only that branch, add verified references, and update the
same section note. On `여기까지`, save the exact resume point.

## Maintain Obsidian Notes

Always write under:

```text
$YONTOLOGY_NOTES_DIR/research-study/<paper-slug>/
├── 00-paper-index.md
├── <section-order>-<section-slug>.md
└── assets/
    ├── vocabulary.md            # Only words and expressions studied so far
    ├── original/                # Create when preserving source figures
    └── explanatory/             # Create when saving tutor-generated images
```

Use [assets/paper-index.md](assets/paper-index.md) for the paper index and
[assets/section-study.md](assets/section-study.md) for section notes. Omit its
optional figure and supplementary-visual blocks when not applicable.

- Keep the original PDF at its supplied path; do not copy it into the vault
  unless the user explicitly asks.
- Keep minimal paper metadata, the source PDF link, and the exact reading point.
  These are review notes: omit source/integrity reports, standalone reference
  lists, hashes, extraction details, and routine QA or version-check logs.
  Preserve the authors' citations inside quotations, useful links within teaching
  content, and paper/figure locations that help the user navigate.
- For PDFs under the configured notes root, store the source path relative to that root and resolve it against `YONTOLOGY_NOTES_DIR` when opening it. For other PDFs, preserve the supplied path and verify availability when resuming on another Mac.
- Append each studied paragraph to its section file. Never overwrite prior
  original-text blocks.
- Link important theory terms to `[[concepts/<canonical-slug>]]` so paper study
  can connect to code-review concepts in the shared Obsidian graph.
- Reuse the existing index for the same source. If a different paper version is
  detected, do not silently merge its text into the existing notes.
- Request the narrowest permission needed for the configured notes path. If denied,
  do not write elsewhere.

Report both the clickable Markdown path and a percent-encoded
`obsidian://open?path=...` URI.

## Completion Check

Before ending each turn, verify that:

- The source PDF hash is unchanged.
- The English units together preserve the verified paragraph in order, and each
  unit is immediately followed by its matching Korean translation.
- Translation and added explanation are visibly separated.
- Added theory is two or three relevant lines unless the user asked for depth.
- Field terms are explained for a non-specialist.
- Page, section, and external references are verified.
- Relevant original figures are embedded when possible, visually checked, and
  cited by figure number and page; any extraction limitation is explicit.
- Supplementary visuals are clearly labeled, and saved assets or Mermaid blocks
  remain available in the note with working vault-relative links.
- The note contains the paragraph and exact resume point, with no redundant
  translation headings or source/integrity audit sections.
- Newly taught vocabulary is also included in the paper's cumulative glossary.
