---
title: "{{paper_title}}"
aliases:
  - "{{short_title}}"
tags:
  - research-study
  - paper
created: "{{created_at}}"
updated: "{{updated_at}}"
authors:
  - "{{author}}"
year: "{{publication_year}}"
doi: "{{verified_doi_or_empty}}"
arxiv: "{{verified_arxiv_id_or_empty}}"
source_pdf: "{{absolute_source_path}}"
source_sha256: "{{sha256}}"
status: reading
---

# {{paper_title}}

## 논문 정보

- 저자: {{authors}}
- 출처: {{venue_or_repository}}
- 원본 PDF: `{{absolute_source_path}}`
- SHA-256: `{{sha256}}`

## 읽기 순서

- [[{{section_note_name}}|{{section_title}}]]

## 현재 위치

- 섹션: {{current_section}}
- PDF 페이지: {{current_pdf_page}}
- 다음 문단: {{next_paragraph_id}}

## 핵심 개념

- [[concepts/{{concept_slug}}|{{concept_title}}]]

## 검증된 링크

- [논문 원문 또는 공식 랜딩 페이지]({{verified_paper_url}})
