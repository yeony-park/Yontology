---
name: history-insight
description: 명시된 기간 또는 프로젝트의 로컬 Claude Code 세션 기록을 전수 분석해 반복 질문 유형, 트러블슈팅 흐름, 워크플로우 패턴, 재사용 가능한 스킬·컨텍스트 후보를 찾는다. 어제·지난주·이번 달 전체 세션, 특정 프로젝트의 모든 세션, 수백 개의 크거나 bulky한 JSONL transcript를 빠짐없이 분석해 달라는 요청에 사용한다. 안정 snapshot, 병렬 map/reduce, 고정 taxonomy, coverage accounting으로 누락과 불확실성을 드러낸다. 단일 스킬 실행을 SKILL.md와 대조 평가하는 요청에는 session-analyzer를 사용한다.
---

# History Insight

현재 로컬에 보존된 Claude Code 세션을 스트리밍으로 인벤토리화한 뒤, 서로 겹치지 않는 배치로 분석하고 증거 기반 인사이트를 합성하라.

## 범위 계약

- Claude Code 세션 분석 요청은 `${CLAUDE_CONFIG_DIR:-~/.claude}/projects`의 transcript JSONL을 읽기 전용으로 조사할 권한으로 해석하라. 사용자가 다른 소스 경로를 명시하면 그 경로만 추가하거나 대신 사용하라. `history.jsonl`, 파일 mtime, 인코딩된 프로젝트 디렉터리명은 권위 인덱스로 사용하지 마라.
- 세션 외 프로젝트 자료는 현재 Codex 작업에서 사용자가 첨부·선택·정확한 경로로 명시한 파일만 활성 파일로 인정하라. `cwd`, workspace root, 저장소 전체, 다른 창의 UI 상태를 활성 파일 목록으로 간주하지 마라.
- 활성 파일은 프로젝트 식별과 보조 컨텍스트에만 사용하라. 입력 파일이라는 이유만으로 수정 권한이 생기지 않는다. 사용자가 출력 경로를 명시하지 않으면 결과를 채팅으로 반환하고 영구 파일을 만들지 마라.
- 원본 로그와 활성 파일을 수정하지 마라. 임시 산출물만 권한 `0700`의 실행별 시스템 임시 디렉터리에 두고 파일은 `0600`으로 유지한 뒤 종료 시 제거하라. 재개 가능한 checkpoint는 사용자가 경로를 명시했을 때만 보존하라.
- symlink를 따라 승인된 루트 밖으로 나가지 마라. 외부 웹, MCP, connector로 로그를 보내지 마라. 원문 대신 짧고 마스킹된 근거를 사용하라.
- 수집·정규화 스크립트는 로컬에서 실행되지만 의미 분석은 Codex 모델과 서브에이전트 컨텍스트를 사용한다. 사용자가 완전한 offline/local-LLM 처리를 요구하면 이 차이를 먼저 밝히고 진행하지 마라.

## 1. 분석 범위를 고정하라

1. 상대 기간을 현재 작업의 날짜와 IANA timezone으로 절대 반개구간 `[start, end)`로 바꾸고 보고서에 표시하라. 파일 mtime이 아니라 이벤트 timestamp로 필터링하라.
2. 트러블슈팅·워크플로우 요청에서는 기간 안에 사람의 prompt가 하나라도 있는 parent session을 선택하고 main/subagent hierarchy 전체를 문맥으로 분석하라. 범위 밖 이벤트는 `context_only`로 표시하라.
3. 질문 빈도 요청에서는 같은 session context를 사용할 수 있지만 집계에는 기간 안의 사람이 직접 작성한 turn만 포함하라. tool result, task notification, meta/system 주입을 질문으로 세지 마라.
4. 프로젝트는 사용자가 명시한 canonical 경로 또는 활성 파일의 canonical 경로와 transcript의 실제 `cwd`를 비교해 식별하라. 손실 인코딩된 디렉터리명을 경로로 역변환하지 마라. 후보가 여러 개면 목록을 보여 주고 사용자 선택 전에는 합치지 마라.
5. `전체`는 승인된 소스와 현재 보존된 안정 snapshot 안에서만 의미한다. retention으로 이미 삭제된 기록, orphan metadata, timestamp 없는 선택 불가능 이벤트를 coverage gap으로 밝혀라.

## 2. 인벤토리와 안정 snapshot을 만들라

이 스킬 폴더의 `scripts/session_corpus.py`를 사용하라. 먼저 시스템 임시 디렉터리를 만들고 다음 형태로 실행하라.
아래 상대 경로는 로드한 이 `SKILL.md`가 있는 디렉터리를 작업 디렉터리로 삼아 해석하라.

```bash
python3 scripts/session_corpus.py inventory \
  --start 2026-08-12T00:00:00 \
  --end 2026-08-13T00:00:00 \
  --timezone Asia/Seoul \
  --manifest "$RUN_DIR/manifest.jsonl" \
  --summary "$RUN_DIR/inventory.json"
```

- `--root`를 생략하면 Claude의 canonical projects 디렉터리를 사용한다. 명시 소스가 있으면 `--root`를 반복하라.
- 특정 프로젝트이면 canonical 디렉터리를 `--project-path`로 전달하라. 이름 문자열로 추측하지 마라.
- 스크립트가 정렬된 file/chunk manifest, content hash, line/byte 경계, session hierarchy, 관찰된 cwd, 기간 일치 여부, deterministic batch ID를 만든다.
- `volatile`, malformed line, root 밖 symlink, unknown timestamp, duplicate content, orphan 상태를 조용히 버리지 말고 summary에 유지하라.
- 크기가 큰 파일을 통째로 메모리에 읽는 `jq -s`, `json.load`, 전체 문자열 read를 사용하지 마라.

manifest가 비어 있거나 프로젝트가 모호하거나 snapshot이 변했으면 의미 분석 전에 범위를 바로잡아라. 분석 도중 계속 쓰인 세션은 재인벤토리하거나 `partial`로 판정하라.

## 3. 서로 겹치지 않는 배치를 map하라

분석 전에 [map-contract.md](references/map-contract.md)를 전부 읽고 모든 mapper에 동일한 계약을 적용하라.

1. `batch_id`별로 다음처럼 redacted normalized event shard를 만들라.

```bash
python3 scripts/session_corpus.py extract \
  --manifest "$RUN_DIR/manifest.jsonl" \
  --batch-id batch-00001 \
  --output "$RUN_DIR/shards/batch-00001.jsonl"
```

2. 가용 서브에이전트 슬롯 이하의 bounded pool로 여러 batch를 병렬 처리하라. 각 worker에는 서로 겹치지 않는 batch ID와 동일한 분석 질문·schema만 주어라. 슬롯이나 서브에이전트 도구가 없으면 같은 계약으로 순차 처리하라.
3. 한 worker가 너무 많은 작은 batch를 맡을 수는 있지만, 한 chunk를 둘 이상의 worker에 주지 마라. worker별 결과 파일을 분리하고 공유 파일에 동시 기록하지 마라.
4. 실패 batch는 원인을 기록하고 한 번만 재시도하라. 이후에도 실패하면 `failed`로 남기고 완전 분석을 주장하지 마라.
5. 원문 전체를 reducer에 넘기지 마라. mapper는 chunk별 상태, 집계 기여분, 짧은 redacted evidence pointer, 관찰·불확실성만 반환해야 한다.

## 4. 빈도 질문은 고정 taxonomy로 2회 처리하라

`가장 많이 한 질문 종류`처럼 정확한 빈도를 요구하면 다음을 지켜라.

1. 첫 pass의 대표적이되 전체 범위를 덮는 관찰에서 mutually exclusive taxonomy와 분류 규칙을 확정하라.
2. 확정된 taxonomy를 모든 eligible human turn에 동일하게 적용하는 두 번째 map을 실행하라. mapper가 임의로 새 범주를 만들지 못하게 하고 애매한 항목은 `other/uncertain`으로 남겨라.
3. user-authored turn 수, distinct session 수, distinct project 수를 분리해 보고하라. 같은 질문의 tool echo나 child transcript 복제를 중복 집계하지 마라.

## 5. 계층 reduce와 coverage를 대조하라

- batch가 많으면 chunk → session → project/date → global 순으로 합성하라. 빈도가 낮아도 friction이 큰 패턴을 평균 속에 지우지 마라.
- mapper 결과를 `map-results/`에 JSONL로 저장한 뒤 다음처럼 coverage를 검증하라.

```bash
python3 scripts/session_corpus.py verify \
  --manifest "$RUN_DIR/manifest.jsonl" \
  --results-dir "$RUN_DIR/map-results" \
  --summary "$RUN_DIR/coverage.json"
```

- 모든 selected chunk가 정확히 한 번 `processed`, `failed`, `skipped` 중 하나로 나타나야 한다. missing, duplicate, unknown chunk ID가 하나라도 있으면 reconcile한 뒤에만 최종 합성하라.
- `processed == eligible`, failed/skipped/missing/duplicate 0, snapshot 변경 0일 때만 `현재 보존된 승인 범위 내 완전 분석`이라고 표현하라. 그 밖에는 `partial`로 표시하라.
- 스킬 후보는 서로 다른 session에서의 recurrence, retry/error/time friction, solution stability, cross-project breadth, automation potential, evidence confidence로 순위화하라. 반복 설명·선호·환경 정보는 스킬보다 context 후보로 분리하라.
- 인사이트를 근거로 스킬이나 프로젝트 파일을 자동 생성·수정하지 마라. 별도 요청을 받아라.

## 결과 형식

다음 순서로 간결하게 보고하라.

1. **Scope & coverage** — timezone과 `[start,end)`, 승인 source/project, 발견·eligible·처리·실패·건너뜀 file/session/chunk/event/byte 수, snapshot/retention gap, completeness 판정
2. **핵심 인사이트** — 질문 유형 또는 반복 workflow를 turn/session/project 수와 함께 제시
3. **트러블슈팅 패턴** — 문제 → 시도 → 실패 신호 → 해결 → 검증 흐름과 짧은 evidence pointer
4. **스킬 후보 / context 후보** — 후보별 점수 근거, 추천 trigger, 자동화 경계
5. **불확실성** — malformed/volatile/unknown schema, 분류 애매성, 다음 검증

개인정보·비밀값·긴 원문을 인용하지 말고, `session_id + 상대 경로 + line + timestamp`로 재현 가능한 최소 근거만 남겨라.
