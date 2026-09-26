---
name: research-study
description: Study a user-provided academic or technical PDF paragraph by paragraph without modifying the source file, preserve and display each original English paragraph verbatim, translate it faithfully into Korean, add beginner-friendly background and theory, explain field-specific English terms, cite the paper by page and section, provide verified primary references, and maintain connected Obsidian study notes. Use when the user wants to read, translate, understand, or continue studying a PDF paper, especially a technical paper section such as Abstract, Background, Related Work, Method, or Discussion.
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
- Compute and record its SHA-256 before reading. Compute it again after the
  study turn and require the value to match.
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
4. Resume an existing paper by matching the PDF SHA-256 with its paper index.

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
  so they survive after temporary files are removed. Record the figure number,
  PDF page, source PDF hash, and extraction/rendering method beside the embed.
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
2. **Original (verbatim)**: Reproduce the English paragraph exactly as verified
   from the PDF. Do not correct grammar or rewrite it.
3. **한국어 번역**: Translate every sentence faithfully without adding claims
   that are absent from the paragraph.
4. **비전공자를 위한 부연설명**: Add two or three concise lines explaining
   why this background, problem, or technique emerged and how it connects to
   the field. For a concept such as GraphRAG, cover its motivation plus a
   relevant advantage and limitation when supported.
5. **핵심 영단어**: Explain field-specific terms in plain Korean, including
   the precise meaning they carry in this paper rather than only a dictionary
   definition.
6. **근거 자료**: Cite the paper page and section plus one to three verified
   primary sources for added theory.
7. **한 문장 정리**: State the paragraph's role in the paper.

Label provenance explicitly:

- `논문 원문`: the authors' exact words.
- `번역`: a faithful Korean rendering.
- `부연설명`: tutor-added context.

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
└── assets/                      # Create only when needed
    ├── original/                # Extracted or rendered source figures
    └── explanatory/             # Tutor-generated image assets
```

Use [assets/paper-index.md](assets/paper-index.md) for the paper index and
[assets/section-study.md](assets/section-study.md) for section notes. Omit its
optional figure and supplementary-visual blocks when not applicable.

- Keep the original PDF at its supplied path; do not copy it into the vault
  unless the user explicitly asks.
- Record source path, SHA-256, title, authors, DOI or arXiv ID when verified,
  current section, page, and next paragraph.
- For PDFs under the configured notes root, store the source path relative to that root and resolve it against `YONTOLOGY_NOTES_DIR` when opening it. For other PDFs, preserve the supplied path and verify availability when resuming on another Mac.
- Append each studied paragraph to its section file. Never overwrite prior
  original-text blocks.
- Link important theory terms to `[[concepts/<canonical-slug>]]` so paper study
  can connect to code-review concepts in the shared Obsidian graph.
- If the same hash already has an index, resume it. If the title matches but
  the hash differs, treat it as a different version and do not merge silently.
- Request the narrowest permission needed for the configured notes path. If denied,
  do not write elsewhere.

Report both the clickable Markdown path and a percent-encoded
`obsidian://open?path=...` URI.

## Completion Check

Before ending each turn, verify that:

- The source PDF hash is unchanged.
- The English paragraph matches the rendered page.
- Translation and added explanation are visibly separated.
- Added theory is two or three relevant lines unless the user asked for depth.
- Field terms are explained for a non-specialist.
- Page, section, and external references are verified.
- Relevant original figures are embedded when possible, visually checked, and
  cited by figure number and page; any extraction limitation is explicit.
- Supplementary visuals are clearly labeled, and saved assets or Mermaid blocks
  remain available in the note with working vault-relative links.
- The note contains the paragraph and exact resume point.
