---
name: session-analyzer
description: 완료된 Claude Code 또는 Codex 세션 trace를 명시적으로 선택한 SKILL.md와 사용자 acceptance criteria에 대조해 실제 동작을 평가한다. 스킬이 의도대로 실행됐는지, Hook·SubAgent·Tool Calling·파일 변경이 실제 호출되고 성공하고 결과에 반영됐는지, Expected와 Actual이 왜 다른지, 세션에서 다음 workflow를 무엇으로 개선할지 묻는 요청에 사용한다. 요구사항별 Expected vs Actual 표, 원시 evidence pointer, trace coverage, confidence를 제공하며 관측되지 않는 동작은 실패로 추정하지 않고 UNVERIFIABLE로 표시한다.
---

# Session Analyzer

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

스킬 사양에서 검증 가능한 기대치를 추출하고, 선택된 세션 trace의 직접 증거와 대조하라. 행동 준수와 결과 품질을 분리하고 관측 한계를 숨기지 마라.

Resolve this SKILL.md through any symlinks to find the Yontology checkout (the parent of `skills/`). Before accessing notes or session data, run `python3 <checkout>/scripts/yontology_paths.py` and use the returned absolute paths. It reads that checkout’s `.env`, independently of the current working directory. `$YONTOLOGY_NOTES_DIR` below denotes the resolved value, not an automatically exported shell variable. Use the returned path for file access and chat links; keep links between notes vault-relative. Do not execute `.env` as shell code or fall back to a previous machine’s path.

## 범위 계약

- 대상 `SKILL.md`, acceptance criteria, session trace를 현재 작업에서 사용자가 첨부·선택·정확한 경로 또는 thread ID로 명시한 것만 사용하라. 사용자가 `현재 세션`을 말하면 이 스킬의 resolver로 정확한 current/root thread를 찾고 최신 mtime 파일을 추측하지 마라.
- 현재 Codex 창의 활성 파일은 최신 사용자 turn에서 첨부·명시된 파일과 해당 turn의 구조화된 tool trace가 실제로 읽거나 변경한 파일만 뜻한다. `cwd`, workspace root, 저장소 전체, 전역 UI 상태는 활성 파일 목록이 아니다.
- 원본 trace와 `SKILL.md`를 읽기 전용으로 유지하라. 분석 결과를 근거로 스킬·hook·프로젝트 파일을 자동 수정하지 마라. 사용자가 출력 경로를 명시하지 않으면 채팅으로만 보고하라.
- 실행별 임시 디렉터리 외에는 파일을 만들지 마라. 외부 웹, MCP, connector로 trace를 보내지 말고 secret, blob, thinking, 전체 patch/file content를 보고서에 복제하지 마라.
- live trace에 completion marker가 없거나 파일이 변하면 `in progress/partial`로 표시하라. 관련 telemetry가 불완전하면 이벤트 부재를 `FAIL` 근거로 사용하지 마라.

## 1. 입력과 우선순위를 고정하라

1. 대상 스킬의 `SKILL.md`를 처음부터 끝까지 읽어라. 참조 파일이 특정 조건에서 필수이면 그 조건이 실제로 성립할 때 해당 참조도 읽어라.
2. 기대치 우선순위를 `이번 요청의 acceptance criteria > 선택된 SKILL.md의 MUST/명령형 절차 > 명시적으로 선택된 hook/subagent 설정 > 일반 권고`로 적용하라. 충돌은 숨기지 말고 별도 row로 표시하라.
3. 대상 trace가 여러 개이면 thread/session ID, title, cwd, 시작 시각 후보를 보여 주고 하나를 임의 선택하지 마라.
4. evaluator 자신의 현재 실행을 대상 trace에 섞지 마라. 완료된 대상의 file size/mtime snapshot을 고정하고 evaluator run ID를 별도로 유지하라.

## 2. Expected matrix를 먼저 만들라

분석 전에 [evaluation-rubric.md](references/evaluation-rubric.md)를 전부 읽어라.

각 요구를 한 가지 관찰 가능한 행동 또는 효과로 원자화하고 다음을 기록하라.

- stable requirement ID
- source anchor: 사용자 기준 또는 `SKILL.md` section/line
- 강도: `MUST`, `SHOULD`, `MAY`
- trigger condition
- expected observable event/effect
- 충분한 증거의 형태

애매한 설명문을 강제 요구로 승격하지 마라. 조건이 성립하지 않은 요구는 `NOT_TRIGGERED`로 남겨라. 먼저 Expected matrix를 고정한 뒤 trace를 보며 기준을 바꾸지 마라.

## 3. trace를 스트리밍 정규화하라

이 스킬 폴더의 `scripts/normalize_trace.py`를 사용해 공통 evidence envelope를 만들어라.
아래 상대 경로는 로드한 이 `SKILL.md`가 있는 디렉터리를 작업 디렉터리로 삼아 해석하라.

현재 Codex task와 그 child subagent를 평가할 때:

```bash
python3 scripts/normalize_trace.py \
  --current-codex-thread \
  --include-children \
  --output "$RUN_DIR/trace.jsonl" \
  --summary "$RUN_DIR/trace-summary.json"
```

사용자가 선택한 Claude Code parent transcript를 평가할 때:

```bash
python3 scripts/normalize_trace.py \
  --input /absolute/path/to/session.jsonl \
  --include-children \
  --output "$RUN_DIR/trace.jsonl" \
  --summary "$RUN_DIR/trace-summary.json"
```

- current Codex thread는 `CODEX_THREAD_ID`와 설정된 `YONTOLOGY_CODEX_DIR`의 read-only state database의 `threads.rollout_path`로 해결하라. child에서 호출했다면 spawn edge를 따라 root로 올라가라.
- Codex child trace의 fork된 ancestor history와 response/event 복제를 stable event/call/turn key로 dedupe하라. Claude main/subagent stream은 서로 다른 stream으로 유지하되 UUID/tool ID 중복을 집계에서 제거하라.
- call과 output을 `call_id`로 결합하라. 수백 MB trace를 전체 메모리에 올리는 `json.load`, `jq -s`, 전체 문자열 read를 사용하지 마라.
- 불완전 마지막 JSONL line은 content hash만 남기고 제외하라. snapshot이 바뀌거나 malformed/unknown event가 있으면 coverage gap으로 유지하라.
- code-mode의 outer `exec` source 안에 보이는 `tools.foo(...)`는 `nested_tool_reference`라는 간접 증거일 뿐이다. 독립 call/output event가 없으면 실제 호출·성공으로 승격하지 마라.

## 4. Actual lifecycle을 재구성하라

각 Expected row에 가장 구체적인 직접 증거를 연결하라.

- **Tool**: requested → returned/denied/error → transport success → 결과가 후속 판단이나 산출물에 사용됨을 분리하라.
- **SubAgent**: spawn requested → child/thread started → completed/error/interrupted → 결과가 최종 응답에 통합됨을 분리하라. 정확한 delegated prompt가 trace에서 암호화되거나 빠졌으면 지시 준수는 별도 기준 없이는 판정하지 마라.
- **Hook**: configured → condition eligible → invoked → exit/success → intended effect verified를 분리하라. 설정 존재나 stop summary만으로 특정 hook 실행을 주장하지 마라.
- **Skill**: catalog에 존재하거나 `SKILL.md`가 읽혔다는 사실과 실제 절차 수행을 분리하라.
- **File/output**: patch/write call뿐 아니라 success result, 실제 path/diff/artifact, 후속 검증을 확인하라. patch content 원문은 기본 제외하라.
- **Sequence**: phase 순서가 요구사항이면 timestamp보다 원래 trace line order와 turn/call relation을 우선하라.

## 5. Expected vs Actual을 판정하라

다음 열을 가진 표를 출력하라.

`ID | Source / condition | Expected | Actual | Status | Evidence | Confidence | Gap / next action`

상태는 `PASS`, `PARTIAL`, `FAIL`, `UNVERIFIABLE`, `NOT_TRIGGERED`만 사용하라. confidence와 증거 grade는 rubric대로 계산하라.

- 완전한 관련 trace에 직접 충족 증거가 있을 때만 `PASS`로 판정하라.
- 일부 lifecycle만 관찰되거나 호출 성공은 보이나 효과·통합이 검증되지 않으면 `PARTIAL`로 판정하라.
- 관련 event stream이 완전한데 직접 모순, 오류, 또는 필수 미실행이 확인될 때만 `FAIL`로 판정하라.
- telemetry가 없거나 nested 실행·hook 내부·암호화된 prompt처럼 관측할 수 없으면 `UNVERIFIABLE`로 판정하라.
- trigger condition이 성립하지 않으면 `NOT_TRIGGERED`로 판정하라.

Overall verdict는 단일 근거 없는 백분율로 만들지 마라. 다음을 분리해 요약하라.

- MUST/SHOULD별 Pass/Partial/Fail/Unverifiable/Not triggered 수
- 행동 준수 verdict
- 결과 품질 verdict
- trace coverage와 판정 신뢰도

## 6. 다음 workflow를 추출하라

반복된 workaround, 수동 검증, 실패 후 복구, telemetry 공백을 다음 workflow·스킬 개선 후보로 제안하라. 각 제안은 어느 gap에서 나왔는지 연결하고 기대 효과와 추가 telemetry를 명시하라. 분석 중 원본 스킬을 고치지 말고, 수정은 별도 요청에서만 수행하라.

## 결과 형식

1. **Verdict** — 행동 준수, 결과 품질, trace completeness를 한 문단으로 요약
2. **Scope & evidence coverage** — 대상 session/skill snapshot, 포함 child, event/call/output/hook/file 수, malformed·compaction·live gap
3. **Expected vs Actual** — 요구사항별 표
4. **Lifecycle findings** — Tool, SubAgent, Hook, Skill, File/output별 중요한 실제 흐름
5. **다음 workflow 후보** — gap에 연결된 최소 개선안
6. **관측 한계** — FAIL이 아닌 UNVERIFIABLE로 남긴 이유

evidence pointer는 `source path + line + timestamp + call/turn/event ID`로 제시하고, excerpt는 짧게 마스킹하라.
