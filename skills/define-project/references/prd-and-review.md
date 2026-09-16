# PRD and closure contract

Use this reference only for closure review and final PRD authoring.

## Closure rubric

All conditions must pass before asking for final-goal approval.

### Product and UX

- Name the target user, triggering situation, current pain, and desired outcome.
- Define the primary journey from entry through success.
- Map every primary step to a screen, service touchpoint, or system response.
- Cover loading or waiting, empty, invalid, permission-denied, partial-failure,
  recovery, and completion states when applicable.
- State accessibility and platform constraints that affect the experience.
- Make goals, non-goals, MVP boundary, and later opportunities distinguishable.

### Engineering and operations

- Define core entities, authoritative data sources, retention, deletion, and
  migration expectations.
- Define roles, permissions, sensitive-data handling, and abuse boundaries.
- Identify integrations, dependencies, rate or capacity constraints, and
  degradation behavior.
- Name the operational owner, monitoring signals, alerts, support path, rollout,
  rollback, and incident expectations.
- Make legal, policy, localization, compatibility, performance, reliability, and
  budget constraints explicit or deliberately not applicable.

### QA and evidence

- Express every acceptance criterion as observable behavior with a pass/fail
  boundary.
- Include happy path, negative cases, boundary cases, recovery, and permissions.
- Define test data or evaluation fixtures without relying on production secrets.
- Tie success metrics to a baseline, target, measurement window, and owner where
  relevant.
- Define launch gates, stop conditions, and evidence needed to call the project
  complete.

### Exit conditions

- Ouroboros ambiguity is at or below its configured gate.
- No blocking or high-severity review finding remains.
- Every non-blocking open item has an owner and decision deadline or trigger.
- Consecutive Seeds do not change the product ontology or scope materially.
- The user explicitly approves the final-goal sentence.

## Required PRD structure

Write the document in the user's language. Keep the parenthesized English labels
exactly as shown so deterministic validation works.

```markdown
# PRD

## 1. 문서 상태 (Document status)

- Status: Approved
- Seed version: vNNNN
- Seed path: docs/seeds/seed-vNNNN.yaml
- Final goal approved: yes

## 2. 최종 목표 (Final goal)

## 3. 문제와 배경 (Problem and context)

## 4. 대상 사용자 (Target users)

## 5. 목표와 제외 범위 (Goals and non-goals)

## 6. 사용자 여정과 핵심 흐름 (User journeys and core flows)

## 7. 화면 및 서비스 접점 (Screens and service map)

## 8. 기능 요구사항 (Functional requirements)

## 9. 데이터와 권한 (Data and permissions)

## 10. 비기능 및 운영 요구사항 (Non-functional and operational requirements)

## 11. 성공 지표와 검증 계획 (Success metrics and validation plan)

## 12. 출시와 롤아웃 (Release and rollout)

## 13. 위험, 가정, 미결정 사항 (Risks assumptions and open questions)

## 14. 인수 조건 (Acceptance criteria)

## 15. 추적성과 결정 기록 (Traceability and decision log)
```

## Content rules

- Give requirements stable IDs such as `FR-001`, operational requirements IDs
  such as `OR-001`, and acceptance criteria IDs such as `AC-001`.
- Map every must-have requirement to at least one acceptance criterion in the
  traceability section.
- Label open items as `assumption`, `decide-later`, or `dev-deferred`; give each
  an owner and decision trigger.
- Never leave a blocking item in an approved PRD.
- Prefer testable prose over implementation prescriptions. Include a technical
  constraint only when it is a confirmed product or operational constraint.
