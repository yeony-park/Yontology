---
name: fill-document-template
description: Fill Korean GitHub issue and pull request templates from the user's context. Use when the user asks to create or fill a feature issue, chore issue, bug report, or PR description using the configured templates.
---

# Fill Document Template

## Version check before use

Before this skill's workflow, resolve this `SKILL.md` through symlinks to its
Yontology checkout and follow [the shared update procedure](../../docs/skill-updates.md).
Once per user request per checkout, run
`python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>`.
After an update, re-read this skill and any already-loaded references before
continuing. Respect an explicit request to use the local version without updating.

Use this skill when the user wants one of these project document templates filled:

- Feature issue
- Chore issue
- Bug report issue
- Pull request description

## Behavior

- Write the final output in Korean unless the user requests another language.
- Return only one fenced `markdown` code block containing the filled template unless the user asks for explanation.
- Put no prose, labels, or commentary outside the fenced code block. The user should be able to use the code block copy button and paste directly into GitHub Markdown.
- Keep the template content raw inside the code block so headings such as `## ✨ 기능 설명` are not rendered in the chat response.
- Preserve the template section headings and order exactly.
- Fill missing details with concise, useful placeholders only when the user clearly wants a draft.
- If the document would be misleading without a key detail, ask one short clarifying question before filling it.
- Do not invent issue numbers, links, screenshots, logs, test results, or API names.
- When content is unknown, use natural placeholders such as `작성 필요`, `확인 필요`, or `관련 자료 추가 예정`.
- Keep checklist items actionable and specific.

## CLI Script

This skill includes a local CLI helper at `scripts/fill_template.py`.

Resolve `<skill-dir>` from the loaded SKILL.md (following symlinks), then use it from a project directory like this:

```bash
"<skill-dir>/scripts/dtf" feature 로그인 온보딩 개선
"<skill-dir>/scripts/dtf" chore ESLint 설정 정리
"<skill-dir>/scripts/dtf" bug 메인 페이지 이미지가 안 뜸
"<skill-dir>/scripts/dtf" pr --tested --issue 12
```

- `feature`, `chore`, and `bug` use the text after the command plus project file hints from the current repository.
- `pr` uses the current `HEAD` commit by default. Use `--commit <ref>` to target another commit.
- `pr` marks tests as incomplete unless `--tested` is supplied.
- Use `--repo <path>` with any subcommand when running outside the target project directory.
- The wrapper command calls `scripts/fill_template.py`; use the Python script directly if preferred.
- CLI output is raw Markdown for terminal copy/paste. Chat responses should still be wrapped in a fenced `markdown` code block.

## Template Selection

- Use the feature template for new functionality or improvements.
- Use the chore template for maintenance, configuration, dependency, cleanup, documentation, or non-feature work.
- Use the bug report template for broken behavior, regressions, errors, crashes, unexpected output, or reproduction steps.
- Use the PR template for pull request descriptions, merge requests, code review summaries, or when the user mentions changed files/commits.

If the requested template type is ambiguous, infer the most likely type from the user's words. Ask only when two or more templates fit equally well.

## Feature Issue Template

```markdown
## ✨ 기능 설명
추가하거나 개선할 기능 설명

## 📌 작업 내용
- [ ]
- [ ]
- [ ]

## 🎯 기대 효과
이 기능이 왜 필요한지 설명

## 📎 참고 자료
관련 링크, 디자인, API 문서 등
```

## Chore Issue Template

```markdown
## 🛠 작업 내용
- [ ]
- [ ]
- [ ]

## 📌 상세 설명
필요한 이유 및 작업 설명

## 🔍 참고 사항
기타 참고 내용
```

## Bug Report Template

```markdown
## 🐛 버그 설명
어떤 문제가 발생했는지 작성해주세요.

## 📍 발생 위치
예: 로그인 API, Docker 환경, 메인 페이지 등

## 🔄 재현 방법
1.
2.
3.

## ✅ 기대 동작
원래 기대했던 동작을 작성해주세요.

## 📸 참고 자료
스크린샷, 로그 등
```

## Pull Request Template

```markdown
## 🔥 작업 내용
-
-

## 📌 변경 사항
-
-

## 🚀 테스트 결과
- [x] 테스트 완료

## 📎 관련 이슈
close #
```

## Filling Rules

### Feature Issue

- `기능 설명`: Summarize the feature or improvement in one or two sentences.
- `작업 내용`: Write concrete implementation tasks as unchecked checklist items.
- `기대 효과`: Explain the user or project benefit.
- `참고 자료`: Add supplied links, designs, APIs, files, or `관련 자료 추가 예정`.

### Chore Issue

- `작업 내용`: Write concrete maintenance tasks as unchecked checklist items.
- `상세 설명`: Explain why the work is needed and what scope it covers.
- `참고 사항`: Add constraints, cautions, related files, or `특이사항 없음`.

### Bug Report

- `버그 설명`: Describe observed behavior and impact.
- `발생 위치`: Name the page, API, environment, component, file, or `확인 필요`.
- `재현 방법`: Use numbered steps. If unknown, write steps that start with `확인 필요`.
- `기대 동작`: Describe the correct behavior.
- `참고 자료`: Include supplied screenshots, logs, links, or `스크린샷/로그 추가 예정`.

### Pull Request

- `작업 내용`: Summarize the main work in bullets.
- `변경 사항`: List concrete changed behavior, files, or implementation points.
- `테스트 결과`: Preserve `- [x] 테스트 완료` only if the user says testing was done or you ran verification successfully. Otherwise use `- [ ] 테스트 필요`.
- `관련 이슈`: Use `close #<number>` only when an issue number is provided. Otherwise write `close #`.
