---
title: "{{title}}"
aliases:
  - "{{short_alias}}"
tags:
  - code-review
  - code-review-tutor
created: "{{created_at}}"
updated: "{{updated_at}}"
project: "{{project}}"
language: "{{language}}"
source: "{{source_path}}"
lines: "{{line_range}}"
---

# {{title}}

> {{one_sentence_summary}}

## 질문

{{user_question}}

## 코드 맥락

```{{language}}
{{minimal_code_excerpt}}
```

- 위치: `{{source_path}}:{{line_range}}`
- 주변 흐름: {{surrounding_context}}

## 실행 흐름

{{execution_flow}}

## 호출·데이터·상태 관계

- 호출자: {{callers}}
- 피호출자: {{callees}}
- 데이터 소유권과 상태 변화: {{data_and_state_flow}}
- 외부 효과: {{side_effects}}

## 결합도·응집도·의존성 방향

{{coupling_cohesion_and_dependency_direction}}

## 독립성·테스트 경계

{{independence_substitution_and_test_seams}}

## 왜 이 방식인가

- 확인됨: {{verified_rationale}}
- 추정: {{inferred_rationale}}
- 대안과 트레이드오프: {{alternatives_and_tradeoffs}}

## 런타임 위험

{{runtime_risks_and_failure_paths}}

## 검증 포인트

{{verification_points}}

## 연결된 개념 노트

{{optional_concept_links}}

## 근거 자료

- [{{reference_title}}]({{verified_url}}) — {{relevant_section}}

## 학습 진행

- {{updated_at}} · 최초 코드 질문
