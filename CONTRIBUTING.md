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

## Branches and Commits

Use short kebab-case branch descriptions, such as `docs/update-skill-index` or `feat/add-review-skill`. Codex-created branches use the `codex/` prefix, such as `codex/setup-skill-collection`.

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
