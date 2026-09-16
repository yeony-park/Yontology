# Yontology

코드 학습, 논문 읽기, 프로젝트 기획과 작업 기록 분석에 사용할 수 있는 스킬 모음입니다. 스킬 지침과 필요한 스크립트·참조 문서·템플릿을 함께 제공합니다. 누구나 자신의 경로를 `.env`에 설정해서 사용할 수 있으며, 노트는 로컬 폴더나 OneDrive 등 원하는 위치에 보관할 수 있습니다.

## 스킬 목록

| 스킬 | 설명 | 사용 예시 |
| --- | --- | --- |
| [Code Review Tutor](skills/code-review-tutor/SKILL.md) | 특정 코드의 실행 흐름, 상태 변화, 의존성, 테스트 경계와 위험을 설명하고 코드 리뷰 학습 노트를 남깁니다. | “이 함수가 어떻게 동작하는지 설명해줘.” |
| [Concept Tutor](skills/concept-tutor/SKILL.md) | 공식 문서·원논문을 바탕으로 기술 개념의 원리와 장단점을 설명하고, 기존 개념 노트를 재사용하거나 갱신합니다. | “의존성 역전과 의존성 주입을 비교해줘.” |
| [Daily Learning Tutor](skills/daily-learning-tutor/SKILL.md) | 개념 노트를 읽은 뒤 문제를 풀고, 답변을 채점해 문제별 다음 복습일을 관리합니다. 객관식에서 서술형으로 발전합니다. | “오늘 복습 시작하자.” |
| [Define Project](skills/define-project/SKILL.md) | 질문과 검토로 모호한 아이디어를 구체화합니다. Ouroboros로 요구사항 명세인 Seed를 검증·버전 관리하고 승인된 PRD를 작성합니다. | “앱을 만들기 전에 요구사항부터 정리해줘.” |
| [Fill Document Template](skills/fill-document-template/SKILL.md) | 기능·유지보수·버그 이슈와 PR 본문을 정해진 한국어 Markdown 템플릿으로 작성합니다. | “이번 변경으로 PR 본문 작성해줘.” |
| [History Insight](skills/history-insight/SKILL.md) | 기간·프로젝트별 Claude Code 기록에서 반복 질문과 문제 해결 흐름을 찾아 재사용할 스킬·컨텍스트 후보를 제안합니다. | “지난달 기록에서 반복 작업을 찾아줘.” |
| [Project Decision Journal](skills/project-decision-journal/SKILL.md) | 중요한 결정과 이유를 프로젝트 ADR에 기록하고, 노트 보관함에 사본과 인덱스를 만들어 다른 컴퓨터에서도 읽을 수 있게 합니다. | “이 기술을 선택한 이유를 기록하고 ADR도 공유해줘.” |
| [Research Study](skills/research-study/SKILL.md) | 논문 PDF를 문단별로 읽으며 원문, 번역, 쉬운 설명과 용어를 정리하고 다음에 읽을 위치를 저장합니다. | “이 논문 초록부터 같이 읽자.” |
| [Seed Docs Suite](skills/seed-docs-suite/SKILL.md) | 확정된 요구사항으로 PRD·화면 흐름·기능 명세·와이어프레임·권한 정책·ERD·API·QA 문서 8종을 작성하고 서로 일치하는지 확인합니다. | “승인된 Seed로 개발 문서 세트를 만들어줘.” |
| [Session Analyzer](skills/session-analyzer/SKILL.md) | 선택한 스킬 지침과 Claude Code·Codex 실행 기록을 대조해 실제 도구 호출·파일 변경·결과 반영을 평가합니다. | “이 세션이 스킬 지침을 지켰는지 확인해줘.” |

## 다른 Mac에 설치

Git과 Python 3.10 이상이 필요합니다. 원하는 **지속 보관할 로컬 경로**에 `main` 브랜치를 복제합니다.

```bash
git clone --branch main https://github.com/yeony-park/Yontology.git
cd Yontology
cp .env.example .env
```

`.env`의 경로를 이 컴퓨터에 맞게 수정한 뒤 확인하고 설치합니다. 이미 `.env`가 있으면 복사로 덮어쓰지 말고 기존 파일을 수정하세요.

```bash
python3 scripts/yontology_paths.py
python3 scripts/install_skills.py
```

설치 도구는 스킬 10개를 `YONTOLOGY_SKILLS_DIR`에 심볼릭 링크로 연결합니다. 같은 저장소를 대상으로 다시 실행해도 안전하며, 충돌하는 기존 스킬이 하나라도 있으면 변경 전에 중단합니다. 기존 파일은 직접 백업·정리한 뒤 설치하세요. 저장소를 이동하면 링크를 다시 연결해야 합니다. 공통 설정 코드를 사용하므로 스킬 폴더만 따로 복사하지 말고 저장소 전체를 유지하세요. 업데이트는 이 저장소에서 `git pull --ff-only`로 받습니다.

이전에 `~/.codex/skills/` 또는 플러그인으로 설치한 동명 스킬이 있다면 중복 활성화되지 않도록 기존 설치를 확인하세요. 설치 도구가 이전 스킬이나 플러그인을 제거하지는 않습니다. Codex에서 목록이 갱신되지 않으면 재시작하세요. 설치 위치와 갱신 동작은 [공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)를 따릅니다.

일회성 설치 위치는 `python3 scripts/install_skills.py --dest <스킬-폴더>`로 지정할 수 있습니다. 기존 설치를 자동 이동하거나 제거하지는 않습니다.

## 스킬 사용 전 버전 확인

모든 스킬은 작업을 시작하기 전에 설치된 `SKILL.md`의 실제 저장소를 찾아 `origin/main`과 Git 커밋을 비교하도록 안내합니다. 한 사용자 요청 안에서 같은 저장소는 한 번만 확인합니다. 이는 **에이전트가 따르는 스킬 지침**이며 앱이 강제하는 실행 훅은 아닙니다.

수동으로도 확인할 수 있습니다.

```bash
python3 scripts/check_skill_updates.py --skill skills/concept-tutor/SKILL.md
```

- `up_to_date`: 원격 조회 시점의 최신 커밋과 일치합니다.
- `updated`: 수정 사항 없는 `main`이 원격보다 뒤처져 있어 fast-forward로 갱신했습니다. 에이전트는 바뀐 스킬과 이미 읽은 참조 문서를 다시 읽고 작업합니다.
- `skipped`: 로컬 수정·미추적 파일·작업 브랜치·로컬 전용 커밋·갈라진 이력 등이 있어 갱신하지 않았습니다. 사유를 알리고 현재 버전을 사용합니다.
- `unverified`: 네트워크·인증·권한 오류 등으로 확인하지 못했습니다. 최신이라고 표시하지 않고 현재 버전을 사용합니다. 사용자가 최신 버전을 필수로 요구했다면 해결 전까지 관련 작업을 진행하지 않습니다.

브랜치 전환, 강제 덮어쓰기, stash, 커밋·푸시는 자동으로 하지 않습니다. 무시된 로컬 파일인 `.env`와 충돌하는 갱신도 중단합니다. 설치된 링크는 갱신된 원본을 바로 가리키며, 새로 추가된 스킬 등록은 설치 도구를 다시 실행해야 합니다. 예전 설치에는 확인 절차가 없으므로 이번 기능을 처음 받는 다른 Mac에서는 `git pull --ff-only`를 한 번 실행하세요. [상세 절차](docs/skill-updates.md)

## 컴퓨터별 경로 설정

공유하는 [`.env.example`](.env.example)은 설정 양식입니다. 각 컴퓨터의 저장소 루트에 만든 `.env`는 Git에서 제외되며 커밋·푸시되지 않습니다. 다른 Mac에서는 그 Mac에 맞게 별도로 작성하세요. 설정 변경은 다음 도구 실행부터 적용되며 노트 파일을 자동 이동하지 않습니다.

| 변수 | 용도 | 예제 기본값 |
| --- | --- | --- |
| `YONTOLOGY_NOTES_DIR` | 개념·코드 리뷰·논문 노트, 학습 인덱스와 복습 상태를 보관하는 공통 폴더 | `~/Documents/Yontology/notes` |
| `YONTOLOGY_SKILLS_DIR` | 스킬 설치 도구가 링크를 만드는 위치 | `~/.agents/skills` |
| `YONTOLOGY_CLAUDE_DIR` | History Insight가 `projects/` 아래 세션을 읽는 Claude Code 설정 폴더 | `~/.claude` |
| `YONTOLOGY_CODEX_DIR` | Session Analyzer가 세션과 로컬 상태 DB를 찾는 Codex 데이터 폴더 | `~/.codex` |

OneDrive 사용자는 자신의 동기화 폴더를 지정하면 됩니다. OneDrive는 필수가 아닙니다.

```dotenv
YONTOLOGY_NOTES_DIR="~/OneDrive/Obsidian/Work/Documents"
```

`~/OneDrive`가 없으면 각 Mac의 실제 OneDrive 폴더 경로를 적어도 됩니다. 공백·한글이 있는 경로는 따옴표로 감싸세요. `~`, `$HOME`, `${HOME}` 및 정의된 환경변수를 확장하며, 상대 경로는 현재 작업 폴더가 아닌 Yontology 저장소 루트를 기준으로 해석합니다.

우선순위는 **명시한 CLI 경로 옵션 → 같은 이름의 `YONTOLOGY_*` 환경변수 → 저장소의 `.env` → 기본값**입니다. Claude·Codex 경로를 별도로 설정하지 않았을 때만 기존 `CLAUDE_CONFIG_DIR`, `CODEX_HOME` 환경변수를 기본값보다 먼저 사용합니다. 시스템 환경변수 자체를 변경하지 않습니다. `.env`가 없으면 위 기본값을 사용하며, 빈 경로나 잘못된 변수는 오류로 보고합니다.

공통 코드는 `.env`를 데이터로 읽습니다. `source .env`로 실행하거나 셸 프로필에 등록할 필요가 없습니다. 노트 작성 스킬도 실행 전에 같은 코드를 통해 경로를 확인합니다. 복습 스케줄러는 `--state`를 생략하면 설정된 노트 폴더의 복습 상태를 사용합니다.

## 노트 폴더 구조와 동기화

`YONTOLOGY_NOTES_DIR` 아래에 다음 구조를 유지합니다.

```text
$YONTOLOGY_NOTES_DIR/
├── concepts/
├── code-reviews/
├── research-study/
├── decisions/
│   ├── <project>.md
│   └── <project>/
│       ├── README.md
│       └── ADR-*.md
├── learning-tutor/
│   ├── state.json
│   └── sessions/
├── Code Learning Index.md
└── Project Decision Index.md
```

기존 노트 폴더 **안의 내용**을 설정한 폴더 바로 아래로 옮깁니다. `notes/`를 한 단계 더 넣지 않습니다. Obsidian에서는 설정한 폴더를 보관함으로 열거나, 이를 포함하는 기존 보관함에서 노트 링크 기준을 확인합니다. 설치 도구는 노트를 이동하거나 클라우드 폴더를 생성하지 않습니다.

복습을 이어가려면 노트뿐 아니라 `learning-tutor/state.json`과 세션 기록도 함께 옮기세요. 학습을 시작하기 전에 동기화를 완료하고, 두 Mac에서 동시에 복습 상태를 수정하지 마세요. 새 문제 카드의 `source`와 노트 폴더 안의 PDF 경로는 노트 루트 기준 상대 경로로 기록하도록 안내합니다. 기존 노트의 절대 링크·Obsidian URI·저장된 원본 경로는 별도로 확인해야 하며, `.env` 변경만으로 과거 기록을 재작성하지 않습니다.

## 그 밖의 경로와 의존성

프로젝트 ADR은 원본을 저장소에 유지하고 `decisions/<project>/`에 공유용 사본을 둡니다. 기존 문서를 공유하거나 저장소에서 직접 수정한 내용을 반영하려면 다음 명령을 실행하세요. 스킬로 ADR을 작성·수정할 때도 같은 절차로 사본을 갱신합니다.

```bash
python3 skills/project-decision-journal/scripts/share_adrs.py \
  --source-dir /path/to/project/docs/decisions --project my-project
```

ADR과 프로젝트 결정 원장을 복사하고 내용 일치를 검증합니다. 프로젝트 전체 목록과 공통 인덱스는 스킬이 별도로 갱신합니다. 사본을 따로 수정했다면 덮어쓰지 않고 충돌을 알려줍니다. 원본에서 없어진 문서는 자동 삭제하지 않습니다. 프로젝트 전체 코드·PRD·이미지는 포함하지 않으며, 사본은 상시 자동 동기화가 아닌 실행 시점의 기록입니다. OneDrive 등의 서버 업로드 완료는 별도로 확인해야 합니다.

| 항목 | 경로 또는 준비 사항 |
| --- | --- |
| Claude Code 기록 | `YONTOLOGY_CLAUDE_DIR/projects`; 분석 대상은 이 Mac에 실제로 남아 있는 세션 |
| Codex 기록 | `YONTOLOGY_CODEX_DIR`; 현재 작업 분석에는 실제 Codex 실행 환경과 로컬 상태 DB 필요 |
| 프로젝트 PRD·Seed·ADR | 실행 대상으로 지정한 프로젝트의 `docs/`; 프로젝트 저장소를 별도로 복제 |
| 논문 원본 PDF | 사용자가 지정한 파일. 다른 Mac에서도 읽으려면 PDF도 공유하고 논문 인덱스의 경로 확인 |
| Define Project | 공식 Ouroboros 런타임/플러그인을 각 Mac에 별도 설치·활성화 |
| Research Study | PDF 추출용 `pdfplumber` 또는 `pypdf`, 페이지 렌더링용 Poppler (`pdftoppm`, `pdfinfo`) |
| 개념 조사·근거 확인 | 사용하는 에이전트의 웹 검색·페이지 열람 기능 |

포함된 Python 스크립트는 표준 라이브러리만 사용합니다. GitHub에는 개인 노트·원본 세션 로그·로그인 정보·가상환경을 넣지 않습니다. History Insight와 Session Analyzer는 각 Mac에 실제로 남아 있는 기록을 분석하므로, 스킬을 설치하는 것만으로 다른 Mac의 과거 세션까지 생기지는 않습니다.
