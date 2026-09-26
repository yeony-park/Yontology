---
title: "{{paper_short_title}} — {{section_title}}"
tags:
  - research-study
  - paper-section
created: "{{created_at}}"
updated: "{{updated_at}}"
paper: "[[00-paper-index]]"
section: "{{section_title}}"
---

# {{section_title}}

## {{paragraph_id}} · PDF p.{{pdf_page}}

### 논문 원문

> {{verbatim_english_paragraph}}

<!-- Optional: omit when no figure is relevant. Repeat for multiple figures. -->
### 논문 원본 Figure {{figure_number}} · PDF p.{{figure_pdf_page}}

![[research-study/{{paper_slug}}/assets/original/{{figure_filename}}]]

- 원본 출처: PDF p.{{figure_pdf_page}}, Figure {{figure_number}}
- 원본 PDF SHA-256: `{{source_sha256}}`
- 보존 방식: {{embedded_image_extraction_or_pdf_render_crop}}

**원문 캡션**

> {{verbatim_figure_caption}}

**캡션 번역**

{{faithful_korean_caption_translation}}

### 번역

{{faithful_korean_translation}}

### 비전공자를 위한 부연설명

{{two_or_three_line_context}}

<!-- Optional: omit unless a supplementary visual helps understanding. -->
### 부연설명용 시각 자료 — 논문 원본 아님

{{mermaid_code_block_or_explanatory_image_embed}}

- 설명 목적: {{specific_point_illustrated}}
- 단순화·가정: {{simplifications_or_hypothetical_details}}

### 핵심 영단어

| 영단어 | 한국어 표현 | 이 논문에서의 뜻 |
|---|---|---|
| {{term}} | {{korean_term}} | {{field_specific_explanation}} |

### 근거 자료

- 이 논문: {{section_title}}, PDF p.{{pdf_page}}
- [{{reference_title}}]({{verified_url}}) — {{why_relevant}}

### 한 문장 정리

{{paragraph_role_in_paper}}

### 연결 개념

- [[concepts/{{concept_slug}}|{{concept_title}}]]

---

다음 위치: {{next_paragraph_id}}
