# Evaluation rubric

## 목차

1. Expected requirement schema
2. Actual evidence lifecycle
3. Status rules
4. Evidence grade와 confidence
5. Overall verdict
6. 관측 한계와 금지된 추론

## 1. Expected requirement schema

각 요구사항을 다음 필드로 원자화한다.

| Field | Meaning |
|---|---|
| `id` | 문서와 재실행 사이에서 안정적인 ID |
| `source` | 사용자 기준 또는 SKILL.md section/line |
| `strength` | MUST / SHOULD / MAY |
| `condition` | 요구가 발동하는 관찰 가능한 조건 |
| `expected` | 한 가지 행동 또는 효과 |
| `observable` | 어떤 event/artifact가 충분한 증거인지 |

한 문장에 여러 동사가 있으면 독립적으로 실패할 수 있는 단위로 나눈다. 설명, 배경, 예시는 강제 요구가 아니다. `항상`, `반드시`, 명령형 절차는 조건과 함께 MUST 후보지만 문맥을 확인한다.

## 2. Actual evidence lifecycle

### Tool

1. `requested`: call event와 이름·call ID가 있다.
2. `returned`: 같은 call ID의 output event가 있다.
3. `transport_succeeded`: denial/error가 없고 exit/success 상태가 성공이다.
4. `effect_verified`: 별도 read/diff/test/artifact가 의도한 효과를 확인한다.
5. `integrated`: 후속 판단 또는 최종 산출물이 결과를 실제로 사용한다.

각 단계는 이전 단계를 대신하지 않는다. output이 있다는 이유만으로 의미적 성공을 주장하지 않는다.

### SubAgent

1. parent spawn call
2. child/thread identity 또는 started activity
3. child completion/final output
4. parent가 결과를 수신
5. 최종 산출물에 결과를 반영

parent function argument가 암호화되어 있거나 child에 원문 지시가 없으면 정확한 delegation prompt 준수는 관측 불가다.

### Hook

1. configuration evidence
2. trigger condition eligibility
3. invocation event
4. exit/result
5. intended effect evidence

configuration과 invocation을 혼동하지 않는다. 특정 hook event schema가 제품 trace에 없으면 hook absence는 실패 증거가 아니다.

### Skill

skill catalog/world state는 availability만 증명한다. `SKILL.md` read는 load proxy다. 실제 각 절차는 해당 tool/file/output event로 따로 검증한다.

### File/output

write/edit/patch request, 성공 result, changed path/artifact, 검증 read/test를 분리한다. 파일 내용 전체 대신 path, change kind, hash/status를 사용한다.

## 3. Status rules

| Status | Rule |
|---|---|
| `PASS` | condition이 성립했고 완전한 관련 trace에 expected event/effect의 직접 증거가 있다. |
| `PARTIAL` | 일부 단계만 충족됐거나 call은 성공했으나 effect/integration이 검증되지 않았다. |
| `FAIL` | 관련 trace가 충분히 완전하고 직접 모순·오류·필수 미실행 증거가 있다. |
| `UNVERIFIABLE` | telemetry가 없거나 trace가 불완전·암호화·중첩되어 판정할 수 없다. |
| `NOT_TRIGGERED` | 명시된 condition이 성립하지 않았다. |

absence of evidence를 FAIL로 사용하려면 expected event stream의 시작과 끝, 해당 condition, telemetry completeness가 모두 직접 확인되어야 한다.

## 4. Evidence grade와 confidence

### Evidence grade

- `E3 Direct`: 원시 call/result/exit event, 검증 가능한 diff/artifact/test처럼 stable pointer가 있는 직접 증거
- `E2 Corroborated`: 직접 event 하나와 독립 artifact, 또는 서로 독립적인 간접 신호 둘 이상
- `E1 Indirect`: 최종 답변의 자기보고, static source의 nested tool reference, 결과만 보고 한 추론
- `E0 None`: 관련 관찰 자료 없음

### Confidence

confidence는 다음 셋 중 가장 약한 요소를 따른다.

1. evidence strength
2. 관련 trace completeness
3. requirement-to-event matching ambiguity

- `High`: E3/E2이고 관련 trace가 완전하며 매칭이 고유하다.
- `Medium`: 직접 증거는 있으나 effect 또는 일부 stream이 빠졌거나 매칭 후보가 둘 이상이다.
- `Low`: E1 중심이거나 compaction/truncation/live trace 영향이 있다.
- E0에는 confidence를 붙이지 않고 `UNVERIFIABLE`로 둔다.

부정 판정도 같은 기준을 사용한다. 완전한 event stream에서 expected invocation이 없을 때만 high-confidence FAIL이 가능하다.

## 5. Overall verdict

단일 점수 대신 다음 matrix를 보고한다.

| Strength | PASS | PARTIAL | FAIL | UNVERIFIABLE | NOT_TRIGGERED |
|---|---:|---:|---:|---:|---:|
| MUST |  |  |  |  |  |
| SHOULD |  |  |  |  |  |

그다음 두 verdict를 분리한다.

- **행동 준수**: required workflow가 실제로 수행됐는가
- **결과 품질**: 사용자가 요구한 artifact/outcome이 검증됐는가

trace completeness와 confidence를 verdict 문장에 포함한다. MUST FAIL이 있으면 행동 준수 PASS를 주지 않는다. MUST UNVERIFIABLE이 있으면 `확인 불가`를 숨기지 않는다.

## 6. 관측 한계와 금지된 추론

- live session의 completion event 부재를 실패로 보지 않는다.
- code-mode outer exec source의 `tools.foo(...)` 문자열을 독립 tool call로 보지 않는다.
- encrypted reasoning이나 delegated prompt 내용을 복원·추정하지 않는다.
- child transcript의 forked ancestor event를 새 child 행동으로 중복 집계하지 않는다.
- hook summary만으로 특정 hook 이름·효과를 만들지 않는다.
- final response의 `완료했다`는 진술만으로 call/effect를 PASS로 만들지 않는다.
- compaction replacement history와 원 event를 두 번 세지 않는다.
- target trace가 evaluator 실행 중 바뀌면 부정 판정을 중단하고 partial snapshot으로 표시한다.
