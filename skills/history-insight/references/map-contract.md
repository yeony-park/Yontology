# Map contract

## 목차

1. 입력 이벤트
2. chunk별 출력
3. 관찰 분류
4. 빈도 taxonomy pass
5. 증거와 개인정보
6. reducer 불변조건

## 1. 입력 이벤트

`session_corpus.py extract`의 각 JSON 객체를 독립적인 normalized event로 취급한다.

- `chunk_id`, `file_id`, `session_id`, `stream_kind`, `relative_path`, `line`, `timestamp`는 provenance다.
- `in_window=true`인 human prompt만 기간 질문 빈도에 기여한다.
- `in_window=false`인 이벤트는 선택된 session의 문맥일 뿐 기간 집계에 기여하지 않는다.
- `in_window=null`인 timestamp 없는 metadata는 session 문맥으로만 사용할 수 있다.
- `event=human_prompt`만 사용자의 질문으로 센다. `tool_result`, `system`, `task_notification`을 질문으로 세지 않는다.
- `event=tool_call`, `tool_result`, `hook`, `assistant_text`는 workflow와 troubleshooting 근거로 사용한다.
- `event=metadata_record`는 line coverage만 증명하며 의미 집계에서 제외한다. `event=unhandled_record`가 있으면 unknown schema gap으로 보고하고 완전 분석을 주장하지 않는다.
- `truncated=true`이면 내용이 일부만 제공되었다. 누락 부분을 추정하지 않는다.

## 2. chunk별 출력

각 selected `chunk_id`에 대해 정확히 한 JSON object를 mapper 결과 JSONL에 기록한다.

```json
{
  "chunk_id": "chunk-...",
  "status": "processed",
  "question_contributions": [
    {"turn_key": "...", "provisional_label": "debugging", "confidence": "medium"}
  ],
  "workflow_observations": [
    {
      "pattern": "test -> inspect error -> patch -> rerun",
      "phase": "problem|attempt|failure|resolution|verification",
      "evidence": ["session:relative.jsonl:L42@timestamp"],
      "confidence": "high"
    }
  ],
  "skill_signals": [
    {"candidate": "...", "recurrence": 1, "friction": 2, "stability": 1, "automation": 2}
  ],
  "context_signals": [],
  "unknowns": [],
  "errors": []
}
```

`status`는 `processed`, `failed`, `skipped` 중 하나다. 실패하거나 건너뛴 chunk에도 동일한 `chunk_id`와 이유를 기록한다. 한 chunk를 여러 줄로 나누지 않는다.

## 3. 관찰 분류

- **질문 유형**: 사용자가 달성하려던 목적을 분류한다. 사용된 tool이나 파일 확장자만으로 분류하지 않는다.
- **workflow**: 관찰 순서가 있는 재사용 가능한 행동 묶음이다. 최소 두 개의 직접 event가 있어야 한다.
- **troubleshooting**: 문제 신호, 하나 이상의 시도, 결과 또는 검증을 구분한다. 단순 tool error 하나를 해결 패턴으로 승격하지 않는다.
- **skill 후보**: 반복 실행 가능한 절차·판단·도구 조합이다. 서로 다른 session에서 반복됐는지 확인한다.
- **context 후보**: 반복 설명되는 선호, 환경, 도메인 사실, convention이다. 실행 절차가 없으면 skill로 제안하지 않는다.

chunk 안의 관찰은 전역 recurrence를 증명하지 않는다. reducer가 distinct session/project를 기준으로 합친 뒤에만 `반복`이라고 표현한다.

## 4. 빈도 taxonomy pass

첫 pass 결과로 다음 속성을 가진 taxonomy를 한 번 고정한다.

- label과 한 문장 정의
- 포함 기준과 제외 기준
- 가까운 다른 label과의 tie-breaker
- `other/uncertain` 처리 규칙

두 번째 pass에서는 각 `in_window=true` human prompt의 stable `turn_key`를 정확히 하나의 label에 배정한다. 같은 `turn_key`가 parent와 child transcript에 반복되면 한 번만 센다. 집계 단위를 다음처럼 분리한다.

- user-authored turn count
- distinct parent session count
- distinct canonical project count

## 5. 증거와 개인정보

- evidence pointer 형식은 `session_id:relative_path:Lline@timestamp`로 통일한다.
- 짧은 paraphrase를 우선하고, 직접 인용은 필요한 몇 단어로 제한한다.
- secret, token, authorization header, cookie, private key, 환경변수 값, URL query, email/전화번호 등은 다시 마스킹한다.
- thinking, base64/blob, 전체 파일 snapshot, 긴 tool stdout은 분석하거나 복원하지 않는다.
- `truncated` content를 바탕으로 부정적인 결론을 내리지 않는다.

## 6. reducer 불변조건

- manifest의 selected chunk 집합과 mapper 결과의 chunk 집합을 일치시킨다.
- chunk ID당 결과는 정확히 하나여야 한다.
- 중복 content/session alias는 삭제하지 말고 집계에서만 dedupe하며 수를 보고한다.
- 질문 빈도는 turn key, workflow recurrence는 parent session, cross-project breadth는 canonical cwd 기준으로 dedupe한다.
- 높은 빈도와 높은 friction을 별도로 표시한다.
- 직접 근거가 없는 원인·해결·효과를 사실처럼 합성하지 않는다.
