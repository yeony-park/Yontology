# Primary-source and evidence policy

Read this file before researching or refreshing a concept note.

## Source order

Prefer evidence in this order:

1. Official language, runtime, framework, database, vendor, or standards-body
   documentation.
2. Numbered standards and design documents such as RFCs, W3C specifications,
   PEPs, JEPs, or authoritative implementation documentation.
3. Original research papers from the publisher, conference archive, DOI,
   arXiv, OpenReview, or an author-maintained page.
4. Official source code or tests when documentation does not settle runtime
   behavior.
5. High-quality secondary sources only for discovery or when no primary source
   exists. Label that limitation.

For a technical web search, base factual claims on primary sources. A social
post, newsletter, or blog summary can supply the question but is not evidence
for the answer when an original source exists.

## Verification

- Open every cited URL and verify the title, owner or authors, relevant section,
  version, and date before citing it.
- Link the exact section or paper page when possible.
- Never invent a URL, DOI, author, venue, standard status, metric, or quote.
- Distinguish a preprint, withdrawn submission, accepted paper, and later
  archival version. A withdrawal from one venue does not erase a later accepted
  version.
- Distinguish a standard-track document from informational, experimental, best
  current practice, draft, or vendor guidance.
- Quote sparingly. Prefer an accurate paraphrase with a nearby citation.

## Scope discipline

- Report the conditions behind performance numbers: hardware, scale, batch or
  workload, baseline, measurement, and comparison denominator.
- Do not generalize a result outside the tested setting without labeling it an
  inference.
- Do not present a successful architecture example as an ablation proving that
  one hyperparameter is optimal.
- For a research lineage, allow branches and independent design axes. Do not
  force papers into a chronological replacement chain when their goals differ.
- When sources disagree, describe the disagreement and prefer the newest
  authoritative version without silently erasing the older context.

## Evidence states in notes

- `확인됨`: directly supported by a cited primary source.
- `추정`: a reasoned implication not directly claimed by the source; include
  what evidence would confirm it.
- `근거 확인 보류`: primary evidence could not be accessed; include a specific
  follow-up TODO and do not fabricate a citation.
