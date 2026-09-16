# Quiz and scheduling policy

## Reading gate

Present the exact notes and headings first. Require the reply `읽었음`. Acknowledgement unlocks the quiz but is not evidence of mastery; only recall answers are scored. Keep a pending session durable so an automation run and a later reply resume the same cards.

## Question modes

Every card starts in `mcq` mode. Ask four plausible, mutually exclusive choices and require both a choice and a one-sentence reason.

- Correct choice: 60 points; rationale supplies 0–40 more.
- Incorrect choice: 0 for the choice and at most 30 total if the rationale contains independently correct, relevant knowledge.
- Score `>=70`: promote this card to `written` for its next eligible appearance.
- Score `<70`: keep this card in `mcq`, but change distractors on the next appearance.
- Once promoted, keep the card in `written`; do not regress it to multiple choice to inflate the score.

Written-answer rubric, 100 points total:

| Criterion | Points |
| --- | ---: |
| Correct definition or conclusion | 40 |
| Causal mechanism or execution flow | 25 |
| Constraints, tradeoffs, or failure behavior | 20 |
| Precise example, project application, or verification | 15 |

When the prompt legitimately excludes one category, state the redistributed rubric before grading.

## Strict grading caps

- Wrong core conclusion: maximum 39.
- Correct conclusion without the required causal mechanism: maximum 69.
- Keyword list with no coherent explanation: maximum 49.
- An unresolved contradiction with the source: subtract at least 20 and cap at 59.
- Invented source behavior: subtract 10 per material invention; a safety- or architecture-critical invention also caps the score at 59.
- Minor terminology differences are acceptable only when the meaning and boundary are exact.

Do not round a score upward across a cooldown threshold. Explain every deduction.

## Per-card cooldown

The scheduler uses the score from that exact card:

| Score | Next eligible date |
| ---: | --- |
| 100 | three calendar months later |
| 90–99 | one calendar month later |
| 80–89 | 14 days later |
| 70–79 | 7 days later |
| 60–69 | 4 days later |
| 40–59 | 3 days later |
| 0–39 | 2 days later |

The 2/3/4-day low-score bands are an initial, non-personalized spacing heuristic. They intentionally avoid same-day and consecutive-day rote repetition. Keep full history so later evidence can support personalization; do not describe this table as a measured personal forgetting curve.

Never violate a cooldown to fill a daily quota. A concept can still appear through a different eligible card.

## Daily selection

- Default maximum: 10 cards.
- Prefer lower-scoring due cards, then older due dates.
- Prefer concepts absent from the most recent earlier completed session. Pass
  those prior concepts to the scheduler as `--avoid-concept`. If any alternate
  due concept exists, select only from that pool and allow a shorter session;
  fall back only when every due card belongs to the avoided range.
- Topic rotation never makes a card eligible early and never changes a score,
  mode, attempt, or cooldown.
- No card more than once per session.
- No adjacent cards from the same concept.
- Maximum two cards from one concept per session.
- If diversity constraints leave fewer than ten, ask fewer than ten.

## Session log

Record date, assigned readings, card IDs, avoided prior concepts, question modes, exact user answers, grading breakdown, score, next eligible date, next mode, and final daily mean. Never store a score for an unanswered or aborted card. If the user rejects an awaiting-reading topic set before answering, mark that session aborted with the reason and select a replacement without touching card attempts.

For a same-day replacement, preserve the rejected assignment under
`## Aborted attempts` and use the file frontmatter for the active replacement.
Rejected concepts are hard exclusions for that replacement; if nothing else is
due, report that no alternate topic is available.
