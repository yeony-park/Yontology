#!/usr/bin/env python3
"""Fill project issue and PR templates from CLI context."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".next",
    ".nuxt",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
    "venv",
}

KEYWORD_HINTS = {
    "로그인": ["login", "auth", "signin", "session"],
    "회원가입": ["signup", "register", "auth"],
    "온보딩": ["onboarding", "onboard", "welcome"],
    "메인": ["main", "home", "index", "page"],
    "랜딩": ["landing", "home", "page"],
    "이미지": ["image", "img", "photo", "media", "asset"],
    "API": ["api", "route", "endpoint"],
    "api": ["api", "route", "endpoint"],
    "Docker": ["docker", "compose", "container"],
    "docker": ["docker", "compose", "container"],
    "환경": ["env", "config", "setting"],
    "설정": ["config", "setting"],
    "검색": ["search"],
    "추천": ["recommend", "recommendation"],
    "지도": ["map", "location"],
    "주소": ["address", "location"],
    "리뷰": ["review"],
    "식당": ["restaurant", "store"],
    "예약": ["reservation", "booking"],
    "결제": ["payment", "billing"],
    "관리자": ["admin", "dashboard"],
    "채팅": ["chat", "message"],
    "테스트": ["test", "spec"],
}

STATUS_LABELS = {
    "A": "추가",
    "C": "복사",
    "D": "삭제",
    "M": "수정",
    "R": "이름 변경",
    "T": "타입 변경",
    "U": "충돌",
}

TEMPLATE_COMMANDS = {"feature", "chore", "bug", "pr"}
COMMAND_ALIASES = {
    "feat": "feature",
    "기능": "feature",
    "fix": "bug",
    "bugfix": "bug",
    "버그": "bug",
    "refactor": "chore",
    "refacor": "chore",
    "refactoring": "chore",
    "리팩토링": "chore",
    "maintenance": "chore",
    "maint": "chore",
}


@dataclass
class ProjectContext:
    root: Path
    name: str
    stack: list[str]
    files: list[str]


@dataclass
class ChangedFile:
    status: str
    path: str


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
        raise SystemExit(message)
    return proc.stdout.strip()


def resolve_repo(path: str) -> Path:
    repo = Path(path).expanduser().resolve()
    root = run_git(repo, ["rev-parse", "--show-toplevel"], check=False)
    return Path(root).resolve() if root else repo


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def collect_files(root: Path) -> list[str]:
    git_files = run_git(root, ["ls-files"], check=False)
    if git_files:
        return [line for line in git_files.splitlines() if line.strip()]

    files: list[str] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in names:
            path = Path(current, name)
            try:
                files.append(str(path.relative_to(root)))
            except ValueError:
                continue
    return sorted(files)


def direct_child_files(root: Path, filename: str) -> list[Path]:
    paths = [root / filename]
    try:
        children = list(root.iterdir())
    except OSError:
        return paths

    for child in children:
        if child.is_dir() and child.name not in SKIP_DIRS:
            paths.append(child / filename)
    return paths


def detect_stack(root: Path) -> tuple[str | None, list[str]]:
    stack: list[str] = []
    project_name: str | None = None

    for package_path in direct_child_files(root, "package.json"):
        package_json = read_json(package_path)
        if not package_json:
            continue
        if package_path.parent == root:
            project_name = package_json.get("name") or project_name
        deps = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {}),
        }
        if "next" in deps:
            stack.append("Next.js")
        if "react" in deps:
            stack.append("React")
        if "vite" in deps:
            stack.append("Vite")
        if "typescript" in deps:
            stack.append("TypeScript")
        if "tailwindcss" in deps:
            stack.append("Tailwind CSS")

    python_paths = direct_child_files(root, "pyproject.toml") + direct_child_files(root, "requirements.txt")
    if any(path.exists() for path in python_paths):
        stack.append("Python")
    for requirements_path in direct_child_files(root, "requirements.txt"):
        try:
            requirements = requirements_path.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        if "fastapi" in requirements:
            stack.append("FastAPI")

    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        stack.append("Docker")

    return project_name, list(dict.fromkeys(stack))


def load_project_context(repo: Path) -> ProjectContext:
    name, stack = detect_stack(repo)
    return ProjectContext(
        root=repo,
        name=name or repo.name,
        stack=stack,
        files=collect_files(repo),
    )


def normalize_text(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part.strip()).strip()


def short(text: str, limit: int = 90) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def tokens_from_text(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z0-9_./-]+|[가-힣]+", text.lower()))
    for source, hints in KEYWORD_HINTS.items():
        if source.lower() in text.lower():
            tokens.update(hint.lower() for hint in hints)
    return {token for token in tokens if len(token) > 1}


def relevant_files(text: str, files: list[str], limit: int = 6) -> list[str]:
    tokens = tokens_from_text(text)
    if not tokens:
        return []

    scored: list[tuple[int, str]] = []
    for file in files:
        lower = file.lower()
        basename = Path(file).name.lower()
        score = 0
        for token in tokens:
            if token in lower:
                score += 1
            if token in basename:
                score += 1
        if score:
            scored.append((score, file))

    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return [file for _, file in scored[:limit]]


def project_reference_lines(ctx: ProjectContext, files: list[str]) -> list[str]:
    lines = [f"- 프로젝트: {ctx.name}"]
    if ctx.stack:
        lines.append(f"- 기술 스택 후보: {', '.join(ctx.stack)}")
    if files:
        lines.append(f"- 관련 파일 후보: {', '.join(files[:4])}")
    else:
        lines.append("- 관련 자료 추가 예정")
    return lines


def render_feature(text: str, ctx: ProjectContext) -> str:
    focus = short(text or "작성 필요")
    files = relevant_files(text, ctx.files)
    scope = f"관련 파일 영향 범위 확인({', '.join(files[:3])})" if files else "현재 구현 흐름 및 영향 범위 확인"
    refs = "\n".join(project_reference_lines(ctx, files))
    return f"""## ✨ 기능 설명
다음 기능을 추가하거나 개선합니다: {focus}

## 📌 작업 내용
- [ ] {scope}
- [ ] {focus} 구현 또는 개선
- [ ] 관련 화면/API 동작 확인 및 필요 시 테스트 보강

## 🎯 기대 효과
사용자가 {focus} 관련 흐름을 더 안정적이고 편리하게 이용할 수 있습니다.

## 📎 참고 자료
{refs}"""


def render_chore(text: str, ctx: ProjectContext) -> str:
    focus = short(text or "작성 필요")
    files = relevant_files(text, ctx.files)
    scope = f"관련 파일 정리 범위 확인({', '.join(files[:3])})" if files else "작업 범위와 영향도 확인"
    refs = "\n".join(project_reference_lines(ctx, files))
    return f"""## 🛠 작업 내용
- [ ] {scope}
- [ ] {focus} 작업 반영
- [ ] 변경 후 동작 및 설정 이상 여부 확인

## 📌 상세 설명
{focus} 작업이 필요합니다. 프로젝트 구조와 현재 구현을 확인한 뒤 필요한 범위만 수정합니다.

## 🔍 참고 사항
{refs}"""


def render_bug(text: str, ctx: ProjectContext) -> str:
    focus = short(text or "작성 필요")
    files = relevant_files(text, ctx.files)
    location = ", ".join(files[:4]) if files else "확인 필요"
    refs = "\n".join(project_reference_lines(ctx, files))
    return f"""## 🐛 버그 설명
{focus} 문제가 발생합니다.

## 📍 발생 위치
{location}

## 🔄 재현 방법
1. 프로젝트를 실행하고 관련 화면 또는 기능으로 이동합니다.
2. {focus} 상황을 재현합니다.
3. 실제 동작, 콘솔 로그, 네트워크 응답을 확인합니다.

## ✅ 기대 동작
문제가 발생하지 않고 의도한 동작이 정상적으로 수행되어야 합니다.

## 📸 참고 자료
{refs}"""


def commit_message(repo: Path, commit: str) -> tuple[str, str]:
    raw = run_git(repo, ["log", "-1", "--pretty=%B", commit])
    lines = raw.splitlines()
    subject = lines[0].strip() if lines else commit
    body = "\n".join(lines[1:]).strip()
    return subject, body


def first_parent_diff_target(repo: Path, commit: str) -> tuple[str, bool]:
    parents = run_git(repo, ["rev-list", "--parents", "-n", "1", commit]).split()
    if len(parents) > 2:
        return f"{commit}^1", True
    return f"{commit}^", False


def changed_files_for_commit(repo: Path, commit: str) -> list[ChangedFile]:
    base, is_merge = first_parent_diff_target(repo, commit)
    args = ["diff", "--name-status", "--no-renames", base, commit] if is_merge else ["diff-tree", "--no-commit-id", "--name-status", "-r", commit]
    output = run_git(repo, args, check=False)
    changes: list[ChangedFile] = []
    seen: set[tuple[str, str]] = set()
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][0]
        path = parts[-1]
        key = (status, path)
        if key not in seen:
            changes.append(ChangedFile(status=status, path=path))
            seen.add(key)
    return changes


def derive_title(subject: str, body: str) -> str:
    if subject.lower().startswith("merge pull request"):
        for line in body.splitlines():
            clean = line.strip()
            if clean:
                return clean
    return subject


def changed_areas(changes: list[ChangedFile]) -> str:
    if not changes:
        return "변경 파일 확인 필요"
    roots = []
    for change in changes:
        parts = Path(change.path).parts
        if len(parts) >= 2 and parts[0] in {"app", "pages", "src"}:
            roots.append("/".join(parts[:2]))
        else:
            roots.append(parts[0])
    most_common = [area for area, _ in Counter(roots).most_common(3)]
    return ", ".join(most_common)


def format_change_bullets(changes: list[ChangedFile], limit: int = 8) -> list[str]:
    if not changes:
        return ["- 파일 변경 내역 확인 필요"]

    bullets = []
    for change in changes[:limit]:
        label = STATUS_LABELS.get(change.status, change.status)
        bullets.append(f"- {label}: {change.path}")
    if len(changes) > limit:
        bullets.append(f"- 외 {len(changes) - limit}개 파일 변경")
    return bullets


def issue_line(value: str | None) -> str:
    if not value:
        return "close #"
    match = re.search(r"\d+", value)
    return f"close #{match.group(0)}" if match else "close #"


def render_pr(repo: Path, commit: str, issue: str | None, tested: bool) -> str:
    subject, body = commit_message(repo, commit)
    changes = changed_files_for_commit(repo, commit)
    title = short(derive_title(subject, body))
    area = changed_areas(changes)
    test_line = "- [x] 테스트 완료" if tested else "- [ ] 테스트 필요"
    change_bullets = "\n".join(format_change_bullets(changes))

    return f"""## 🔥 작업 내용
- {title}
- {area} 중심 변경 사항 반영

## 📌 변경 사항
{change_bullets}

## 🚀 테스트 결과
{test_line}

## 📎 관련 이슈
{issue_line(issue)}"""


def add_repo_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo",
        default=".",
        help="프로젝트 경로입니다. 기본값은 현재 디렉터리입니다.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fill Korean issue and PR templates from CLI context.",
    )
    subparsers = parser.add_subparsers(dest="template", required=True)

    for name, help_text in [
        ("feature", "기능 이슈 템플릿을 채웁니다."),
        ("chore", "chore 이슈 템플릿을 채웁니다."),
        ("bug", "버그 리포트 템플릿을 채웁니다."),
    ]:
        sub = subparsers.add_parser(name, help=help_text)
        add_repo_argument(sub)
        sub.add_argument("text", nargs=argparse.REMAINDER, help="템플릿에 반영할 설명입니다.")

    pr = subparsers.add_parser("pr", help="현재 커밋 기준 PR 템플릿을 채웁니다.")
    add_repo_argument(pr)
    pr.add_argument("--commit", default="HEAD", help="분석할 커밋입니다. 기본값은 HEAD입니다.")
    pr.add_argument("--issue", help="관련 이슈 번호입니다. 예: 12 또는 #12")
    pr.add_argument("--tested", action="store_true", help="테스트 완료로 표시합니다.")

    return parser


def normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv

    first = argv[0]
    if first in {"-h", "--help"}:
        return argv
    if first in COMMAND_ALIASES:
        return [COMMAND_ALIASES[first], *argv[1:]]
    if first in TEMPLATE_COMMANDS:
        return argv
    if first.startswith("-"):
        return argv
    return ["feature", *argv]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(normalize_argv(argv or sys.argv[1:]))
    repo = resolve_repo(args.repo)

    if args.template == "pr":
        print(render_pr(repo, args.commit, args.issue, args.tested))
        return 0

    ctx = load_project_context(repo)
    text = normalize_text(args.text)
    if args.template == "feature":
        print(render_feature(text, ctx))
    elif args.template == "chore":
        print(render_chore(text, ctx))
    elif args.template == "bug":
        print(render_bug(text, ctx))
    else:
        raise SystemExit(f"unknown template: {args.template}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
