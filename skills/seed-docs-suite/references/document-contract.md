# Document Contract

Read this file before creating the documentation suite.

## Output Manifest

Create these files under `docs/`:

| File | Purpose | Required format |
| --- | --- | --- |
| `prd.md` | Canonical product requirements | Markdown |
| `screen-flow.md` | Screen inventory and navigation flow | Markdown + Mermaid `flowchart` |
| `feature-spec.md` | Prioritized, dependency-aware delivery specification | Markdown |
| `wireframe.md` | High-fidelity responsive wireframe | Markdown + one complete fenced `html` document |
| `authorization-policy.md` | Roles, ownership, and authorization rules | Markdown |
| `erd.md` | Logical data model | Markdown + Mermaid `erDiagram` |
| `api-spec.md` | API contracts and interaction sequences | Markdown + Mermaid `sequenceDiagram` |
| `qa-test-cases.md` | Traceable QA scenarios | Markdown |

Do not use Korean filenames. Do not create an additional `wireframe.html` unless the user requests it.

## Shared Identifiers

Use stable identifiers throughout the suite:

- `FR-###`: functional requirement
- `NFR-###`: non-functional requirement
- `AC-###`: acceptance criterion
- `SCR-###`: screen
- `ROLE-###`: authorization role
- `ENT-###`: entity
- `API-###`: API operation
- `TC-###`: QA test case
- `DEC-###`: unresolved decision

Never renumber existing identifiers merely for presentation. Link downstream records back to `FR-*`, `NFR-*`, and `AC-*`.

## `prd.md`

Include:

1. document status, source/provenance, version, and last-updated date;
2. product summary, problem, vision, and goals;
3. target users and key jobs-to-be-done;
4. assumptions and confirmed decisions;
5. MVP scope, post-MVP scope, and explicit non-goals;
6. user journeys;
7. functional requirements with IDs and priorities;
8. non-functional requirements with measurable predicates;
9. business rules and domain glossary;
10. acceptance criteria;
11. dependencies, risks, and mitigations;
12. unresolved decisions with IDs;
13. traceability index linking requirements to downstream documents.

Do not bury a confirmed product decision in an assumptions section. Keep desired future features out of MVP acceptance criteria.

## `screen-flow.md`

Include:

- screen inventory with `SCR-*`, purpose, entry conditions, and roles;
- one top-level Mermaid `flowchart TD` or `flowchart LR` covering onboarding, primary navigation, success paths, errors, empty states, permission denials, and re-entry/recovery;
- focused subflows when the top-level graph would become unreadable;
- transition table with source, action, destination, guard, and failure destination;
- deep-link, authentication, offline, and back-navigation behavior when relevant.

Every UI-dependent P0 requirement must appear in a flow. Avoid embedding paragraphs inside Mermaid nodes.

## `feature-spec.md`

For each feature include:

- `FR-*`, name, user value, P0/P1/P2 priority, and MVP status;
- dependencies and blockers;
- data/API/screen/authorization/QA links;
- observable acceptance criteria;
- failure and recovery behavior;
- explicit out-of-scope items.

Then include:

- a dependency graph;
- parallel workstreams such as foundation, account, personal records, team collaboration, design system, and quality/release when supported by the PRD;
- a critical path showing what must be sequential;
- milestones that name completed outcomes, not vague phases.

Use these priority meanings:

- P0: required for the approved MVP release;
- P1: valuable immediately after MVP or removable without breaking the core release;
- P2: later enhancement or strategic expansion.

Do not infer priority from enthusiasm; derive it from the approved source.

## `wireframe.md`

Start with a screen-to-requirement index. Then include exactly one fenced `html` block containing a complete standalone document from `<!doctype html>` through `</html>`.

The HTML must:

- render responsive mobile-first screens and a desktop overview when useful;
- implement the approved visual direction with CSS custom properties for color, type, spacing, radius, shadow, and motion;
- provide a visible theme switcher when multiple themes are required;
- show realistic states for the primary P0 journeys, including loading, empty, error, disabled, offline, and permission states;
- use semantic HTML, keyboard-visible focus, labeled controls, adequate contrast, and reduced-motion handling;
- avoid external network dependencies unless the user explicitly permits them;
- label frames with their `SCR-*` IDs and connect important interactions to `FR-*` IDs in comments or annotations;
- use representative placeholder content rather than copyrighted book text.

Keep it high fidelity: demonstrate component hierarchy, spacing, visual tokens, navigation, forms, cards, progress, and feedback—not gray boxes alone.

## `authorization-policy.md`

Include:

- role definitions with `ROLE-*` IDs;
- authentication states and ownership boundaries;
- a subject-action-resource-condition matrix;
- team membership and leader-only rules;
- row/object-level access rules in plain language;
- invite, create, read, update, delete, leave, transfer, and archive behavior where relevant;
- enforcement points: server/API is authoritative; client checks are UX only;
- privacy defaults, least privilege, enumeration resistance, audit events, and sensitive-data handling;
- denial behavior and non-leaking error semantics;
- lifecycle edge cases such as expired invitation, removed member, deleted account, and archived reading round.

Do not introduce administrative roles or moderation powers unless needed by the approved requirements. Put undecided lifecycle policies under `DEC-*`.

## `erd.md`

Include:

- one Mermaid `erDiagram` with entities, primary keys, foreign keys, cardinalities, and important fields;
- entity catalog mapping each entity to `ENT-*` and the requirements it supports;
- invariants, uniqueness rules, ownership, archival/deletion policy, timestamps, and optimistic versioning where required by the product behavior;
- an explicit distinction between domain entities and transient client state;
- indexes or constraints that protect confirmed uniqueness, expiration, ordering, and idempotency behavior.

Model the smallest domain that preserves all approved behavior. Do not turn retry or view state into persistent entities without a clear requirement.

## `api-spec.md`

Include:

- conventions: base path, authentication, timestamps, identifiers, pagination, validation envelope, error envelope, and versioning;
- endpoint catalog with `API-*`, method, path, role, related requirement, request, success response, and relevant errors;
- write semantics for authorization, atomicity, idempotency, concurrency, and retries when required;
- realtime or refresh contract expressed as an observable outcome without forcing a transport not chosen in the PRD;
- at least one Mermaid `sequenceDiagram` for each critical multi-party journey;
- explicit behavior for expired credentials/invitations, duplicate requests, conflicts, offline attempts, and partial infrastructure failure;
- mapping from API operations to entities and QA cases.

Do not invent a vendor or framework. If a P0 feature is intentionally local-only, record that rationale instead of inventing an endpoint.

## `qa-test-cases.md`

Include:

- test strategy and environments;
- entry and exit criteria;
- a coverage matrix linking every P0 `FR-*`, `NFR-*`, and `AC-*` to one or more `TC-*` cases;
- test-case table with ID, type, priority, preconditions, data, steps, expected result, and automation candidate;
- positive, negative, boundary, authorization, concurrency, retry/idempotency, offline/reconnect, cross-device, accessibility, visual/theme, and platform-compatibility cases as required by the PRD;
- measurable performance protocol for every numeric SLO, including sample size, timing boundary, percentile calculation, and pass rule;
- regression smoke set and release sign-off checklist;
- defect severity definitions.

Expected results must state observable UI and persisted-state outcomes. Never use “works correctly” as an oracle.

## Cross-Document Reconciliation

Before finishing, produce an internal traceability matrix and resolve these checks:

1. Every P0 `FR-*` has an `AC-*` and at least one `TC-*`.
2. Every P0 UI behavior maps to a `SCR-*`; non-UI behavior states why no screen is needed.
3. Every protected action maps to a `ROLE-*` rule.
4. Every persisted concept maps to an `ENT-*`; transient concepts are marked transient.
5. Every client-server interaction maps to an `API-*`; local-only behavior has a rationale.
6. Every API error or concurrency rule has a negative or boundary test.
7. Every numeric NFR has a reproducible QA protocol.
8. Names, statuses, priorities, and lifecycle rules match across all files.
9. The wireframe does not imply functionality absent from the PRD.
10. Post-MVP items do not appear as P0 screens, endpoints, entities, or exit criteria.

If a mapping is intentionally absent, record a one-line rationale. Report unresolved `DEC-*` items in the final handoff.
