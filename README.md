# Yontology

다른 Mac에서도 설치해서 사용할 수 있는 개인 스킬 모음집입니다. 스킬 지침과 실행에 필요한 스크립트·참조 문서·템플릿을 함께 관리합니다. 학습 노트는 OneDrive로 동기화합니다.

## 스킬 목록

| 스킬 | 용도 |
| --- | --- |
| [Code Review Tutor](skills/code-review-tutor/SKILL.md) | 구체적인 코드의 실행·의존성·테스트 경계를 학습 |
| [Concept Tutor](skills/concept-tutor/SKILL.md) | 기술 개념을 조사하고 정규 개념 노트 작성 |
| [Daily Learning Tutor](skills/daily-learning-tutor/SKILL.md) | 개념 노트 기반 퀴즈와 문제별 간격 복습 |
| [Define Project](skills/define-project/SKILL.md) | Ouroboros 인터뷰·Seed 검증을 거쳐 PRD 확정 |
| [Fill Document Template](skills/fill-document-template/SKILL.md) | 한국어 GitHub 이슈·PR 템플릿 작성 |
| [History Insight](skills/history-insight/SKILL.md) | Claude Code 세션의 반복 질문·작업 패턴 분석 |
| [Project Decision Journal](skills/project-decision-journal/SKILL.md) | 중요한 결정과 이유를 프로젝트 ADR로 기록 |
| [Research Study](skills/research-study/SKILL.md) | 논문 PDF 문단별 번역·학습과 재개 위치 기록 |
| [Seed Docs Suite](skills/seed-docs-suite/SKILL.md) | 확정 요구사항에서 일관된 제품 문서 8종 생성 |
| [Session Analyzer](skills/session-analyzer/SKILL.md) | 스킬 지침과 실제 세션 실행 기록 대조 |

## 다른 Mac에 설치

Git과 Python 3.10 이상이 필요합니다. 원하는 **지속 보관할 로컬 경로**에 복제합니다. 현재 스킬 모음은 `chore/setup-skill-collection` 브랜치에 있습니다.

```bash
git clone --branch chore/setup-skill-collection https://github.com/yeony-park/Yontology.git
cd Yontology
python3 scripts/install_skills.py
```

설치 도구는 스킬 10개를 `~/.agents/skills/`에 심볼릭 링크로 연결합니다. 같은 저장소를 대상으로 다시 실행해도 안전하며, 충돌하는 기존 스킬이 하나라도 있으면 변경 전에 중단합니다. 기존 파일은 직접 백업·정리한 뒤 설치하세요. 저장소를 이동하면 링크를 다시 연결해야 합니다. 업데이트는 이 저장소에서 `git pull --ff-only`로 받습니다.

이전에 `~/.codex/skills/` 또는 플러그인으로 설치한 동명 스킬이 있다면 중복 활성화되지 않도록 기존 설치를 확인하세요. 설치 도구가 이전 스킬이나 플러그인을 제거하지는 않습니다. Codex에서 목록이 갱신되지 않으면 재시작하세요. 설치 위치와 갱신 동작은 [공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)를 따릅니다.

다른 설치 위치가 필요할 때만 `python3 scripts/install_skills.py --dest <스킬-폴더>`를 사용하세요. 이 경우 CLI 예제의 설치 경로도 그 위치로 바꿉니다.

## OneDrive 노트 위치

모든 Mac에서 다음 경로를 사용합니다. `Opsidian`은 지정한 실제 폴더명입니다.

```text
~/OneDrive/Opsidian/Work/Documents/
├── concepts/
├── code-reviews/
├── research-study/
├── learning-tutor/
│   ├── state.json
│   └── sessions/
├── Code Learning Index.md
└── Project Decision Index.md
```

기존 보관함의 **`notes/` 안에 있는 내용**을 위 `Documents/` 바로 아래로 옮깁니다. `Documents/notes/`로 한 단계 더 넣지 않습니다. Obsidian에서는 `Documents/`를 보관함으로 열거나 이를 포함하는 기존 보관함에서 노트 링크 기준을 확인합니다. 설치 도구는 노트를 옮기거나 빈 OneDrive 폴더를 만들지 않습니다. 먼저 각 Mac에서 OneDrive가 동기화한 실제 폴더를 이 경로로 접근할 수 있게 설정하세요.

`~`는 현재 사용자의 홈이므로 사용자명이 달라도 사용할 수 있습니다. 셸에서는 `"$HOME/OneDrive/Opsidian/Work/Documents"`, Python에서는 `Path.home() / "OneDrive/Opsidian/Work/Documents"`로 해석합니다. 따옴표 안의 `"~/..."`는 셸에서 홈으로 확장되지 않습니다.

복습을 이어가려면 노트뿐 아니라 `learning-tutor/state.json`과 세션 기록도 함께 옮기세요. 학습을 시작하기 전에 동기화를 완료하고, 두 Mac에서 동시에 복습 상태를 수정하지 마세요. 기존 노트의 절대 파일 링크·Obsidian URI, 문제 카드의 `source`, 논문 인덱스의 PDF 경로는 이동 시 새 위치로 갱신해야 합니다. 설치 도구는 기존 노트 내용을 수정하지 않습니다.

## 그 밖의 경로와 의존성

| 항목 | 경로 또는 준비 사항 |
| --- | --- |
| Claude Code 기록 | 각 Mac의 `~/.claude/projects`; `CLAUDE_CONFIG_DIR` 설정 시 그 아래 `projects` 사용 |
| Codex 기록 | 각 Mac의 `~/.codex`; `CODEX_HOME` 설정 시 해당 경로 사용. 현재 작업 분석에는 실제 Codex 실행 환경과 로컬 상태 DB 필요 |
| 프로젝트 PRD·Seed·ADR | 실행 대상으로 지정한 프로젝트의 `docs/`; 프로젝트 저장소를 별도로 복제 |
| 논문 원본 PDF | 사용자가 지정한 파일. 다른 Mac에서도 읽으려면 PDF도 공유하고 논문 인덱스의 경로 확인 |
| Define Project | 공식 Ouroboros 런타임/플러그인을 각 Mac에 별도 설치·활성화 |
| Research Study | PDF 추출용 `pdfplumber` 또는 `pypdf`, 페이지 렌더링용 Poppler (`pdftoppm`, `pdfinfo`) |
| 개념 조사·근거 확인 | 사용하는 에이전트의 웹 검색·페이지 열람 기능 |

포함된 Python 스크립트는 표준 라이브러리만 사용합니다. GitHub에는 개인 노트·원본 세션 로그·로그인 정보·가상환경을 넣지 않습니다. History Insight와 Session Analyzer는 각 Mac에 실제로 남아 있는 기록을 분석하므로, 스킬을 설치하는 것만으로 다른 Mac의 과거 세션까지 생기지는 않습니다.
