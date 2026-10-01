# Contributing to Yontology

Yontology is a personal collection of skills. Keep each change focused on one skill or one documentation improvement.

These conventions follow [gitropolis-ai](https://github.com/yeony-park/gitropolis-ai/blob/main/CONTRIBUTING.md), adapted for a skill collection.

## Scope and Language

These conventions apply to everyone contributing to this repository, including the repository owner and AI coding agents.

Write issue titles and bodies, pull request titles and bodies, and commit messages in English. The README remains in Korean.

## Issues

Check existing issues and pull requests before opening a new one.

- Use `[Bug]: <short description>` for incorrect skill instructions or unexpected behavior. Include the affected file, steps to reproduce, actual behavior, and expected behavior.
- Use `[Feature]: <short description>` for a new skill or an improvement. Include the proposed work, the problem it solves, and the expected impact.
- Small typo fixes and documentation changes may go directly to a pull request. Open an issue first for larger changes.

Use the provided issue forms and write all descriptions in English.

## Issue and Pull Request Labels

Apply labels when creating or triaging an issue or pull request. This applies to
maintainers and AI coding agents, including items created with the GitHub CLI or
API. Before handing work back, verify that the labels match its final scope.

Choose exactly one primary label:

| Label | Meaning | Typical PR type |
| --- | --- | --- |
| `bug` | Correct incorrect instructions or unexpected behavior | `fix` |
| `enhancement` | Add or improve a skill or capability | `feat` |
| `documentation` | Explain existing behavior without changing it | `docs` |
| `maintenance` | Repository upkeep, refactoring, tests, or formatting without a feature or bug fix | `chore`, `refactor`, `test`, `style` |

Classify the effect of a change, not its file extension. A `SKILL.md` change that
fixes tutor behavior is a `bug`; new skill behavior is an `enhancement`. Do not
add `documentation` merely because the implementation is written in Markdown.

Add all directly affected scope labels:

| Label | Scope |
| --- | --- |
| `skill:code-review-tutor` | Code Review Tutor instructions, prompts, and templates |
| `skill:concept-tutor` | Concept Tutor instructions, prompts, and templates |
| `skill:daily-learning-tutor` | Daily Learning Tutor instructions and supporting tools |
| `skill:research-study` | Research Study instructions and assets |
| `area:note-library` | Shared note conventions, catalogs, topic maps, and index tooling |
| `area:repository` | Contribution rules, GitHub templates, installation, and repository tooling |

Reuse existing labels. Create another `skill:<skill-name>` or `area:<area-name>`
only when an actual issue or PR needs that scope; give it an English description.
Use the same scope labels on a linked issue and PR when they address the same
work. Do not label unrelated skills just because they consume a shared format.

Bug and feature issue forms supply their primary label. Add the scope labels
after submission. Issues created through the CLI or API and all PRs need explicit
labels; the PR template is a checklist, not automatic labeling.

Keep labels on closed issues and merged PRs so completed work remains searchable.
When scope changes, replace obsolete classification labels while preserving
unrelated labels. Optional labels such as `duplicate`, `question`, `help wanted`,
`good first issue`, `invalid`, and `wontfix` require a concrete reason. Use GitHub's
open/closed/merged state instead of adding status labels, and do not infer priority.

## Branches and Commits

Use `<type>/<short-kebab-case-description>` for branch names. Choose the type from `feat`, `fix`, `docs`, `style`, `refactor`, `test`, or `chore`, matching the commit types below.

Examples: `docs/update-skill-index`, `feat/add-review-skill`, `chore/setup-skill-collection`.

This convention applies to all contributors, including AI coding agents.

Write commit messages and pull request titles in English using:

```text
<type>: <short description>
```

| Type | Use |
| --- | --- |
| `feat` | Add a skill or new behavior |
| `fix` | Correct instructions or behavior |
| `docs` | Update documentation only |
| `style` | Change formatting without changing behavior |
| `refactor` | Reorganize without changing behavior |
| `test` | Add or update validation |
| `chore` | Update repository configuration or tooling |

Examples: `feat: add code review skill`, `fix: clarify review prerequisites`, `docs: describe the skill collection`.

## Pull Requests

Use the pull request template and include:

- What changed and why it was needed.
- How the change was verified and the results. For documentation-only changes, describe the checks performed; mark runtime tests as not applicable.
- Related issues: use `Closes #123` when the PR resolves an issue, or `Related to #123` for partial work. Write `None` if there is no related issue.

Write the entire pull request title and body in English, keeping the template headings intact.

Before submitting, review changed instructions and links, update relevant documentation, and ensure no secrets, personal data, or unrelated generated files are included.
