# Epic grouping and story skeletons

Binding rules for Procedure steps 5 and 9. The epic rule is the one that changed:
epics are grouped by **business dependency**, not by system area.

## Why the rule changed

The previous breakdown produced epics named after services — AUTH, CHECKOUT,
ORDER, INVENTORY. Three of those are not epics. A business audience gets nothing
from "authentication" shipping alone; it gets something from "a customer can buy
something" shipping. Service-shaped epics leak the future architecture into the
BA layer, they make every epic depend on every other epic, and they produce
success criteria that are really one epic's metric copied four times.

## The three tests

A candidate is an epic only if **all three** hold. Record the answers in the
epic's `decoupling` block — the tests are auditable, not vibes.

### Test 1 — Independently valuable

A business audience gets value from this candidate shipping **alone**, with no
sibling candidate shipped.

Judged against the epic's `business_value` sentence. If that sentence only makes
sense by naming another candidate ("lets customers log in *so they can later*
check out"), test 1 fails.

### Test 2 — Own success metric

At least one `success_criteria` row that is **not** another candidate's metric.

"Checkout conversion" cannot be the success metric of both a login candidate and
a checkout candidate. Whichever candidate does not own it fails test 2.

### Test 3 — No mandatory business dependency on a sibling

If candidate A cannot deliver its value without candidate B shipping first **for
business reasons**, A and B are **one epic**.

The qualifier is load-bearing. Distinguish:

| Kind of dependency | Example | Verdict |
|---|---|---|
| **Business** — the value proposition itself needs both | A customer cannot "buy" without both an account and reserved stock | **Merge** |
| **Technical sequencing** — one is easier to build first | The order service wants the catalogue schema first | **Do not merge** — that is the Tech Lead's ordering problem, recorded in `depends_on` at story level |
| **Temporal preference** — the squad wants to demo one first | Show the storefront at the sprint review | **Do not merge** — that is release sequencing |

Only a business dependency merges. Technical and temporal dependencies live in
story `dependencies.depends_on`.

`decoupling.sibling_dependencies` is schema-capped at **zero entries**: if the
analysis produces a non-empty list, the merge has not been done yet.

## Enablers are never epics

Authentication, inventory reservation, notification, audit logging, session
management, file storage. Each exists to enable a business capability and
delivers no standalone business value. They become **stories inside the epic they
enable**, and the rule they enforce becomes a row in `RULES.json`.

If an enabler serves two epics, it belongs to the epic whose value it is
**necessary** for, and the second epic's story references the same rule ids. Do
not duplicate the story.

## Merging: what to record

When candidates merge, the surviving epic records every folded candidate in
`decoupling.merged_from` with the reason. Never drop a candidate silently — the
three-amigos session needs to see that "customer authentication" was considered
and folded, otherwise it re-litigates the same question.

```json
"decoupling": {
  "independently_valuable": true,
  "own_success_metric": true,
  "sibling_dependencies": [],
  "rationale": "A customer buying something is one indivisible business outcome: an account with nothing to buy, a cart that cannot reserve stock, and a checkout with no payment step each deliver zero business value on their own.",
  "merged_from": [
    "candidate: customer authentication - enabler, no standalone business value (test 1)",
    "candidate: stock reservation - checkout cannot promise an item without it (test 3)"
  ]
}
```

## Story cap and splitting a merged epic

A merged epic can get large. Cap: **12 stories**. Above the cap, split on a
**value axis** and record it in `decoupling.split_axis`:

| Axis | Use when |
|---|---|
| `workflow-step` | The epic contains a state machine with two or more named states |
| `business-rule-variation` | Rules diverge by customer tier, data class or risk class |
| `data-variation` | Personal versus non-personal data; the handling genuinely differs |
| `role-boundary` | Customer-facing versus back-office actor |
| `happy-vs-alternate` | Distinct error, retry or escalation flows |
| `crud` | Create / read / update / delete carry different authority |
| `optimize-later` | Defer a performance or scale concern to a follow-on story |
| `spike` | Pure investigation, no acceptance-criteria commitment |

**Never split on a technical layer** (frontend / backend / API / database).
AP-7.1 in `references/anti-patterns.md` still binds, and a layer split fails
INVEST-Independent and INVEST-Valuable by construction. If the only axis that
presents itself is a technical layer, leave the epic unsplit and raise an open
question for the three-amigos session — that is exactly what the session is for.

## Story skeletons

A skeleton answers *what and why*, never *how it will be verified*. Acceptance
criteria are deliberately absent: writing them before dev and tester have agreed
the breakdown is the rework this stage exists to prevent.

Per story emit: `id`, `epic_id`, `title`, `format`, `card`, `intent`,
`rule_refs`, `flow_refs`, `entity_refs`, `priority`, `sizing`, `dependencies`.

Rules for each:

- **`id`** — `STORY-{epic.story_prefix}-NN`, dense from 01 in emission order
  within the epic. `story_prefix` keeps ids short when a merged epic id is long.
- **`format`** — classic user story by default; `references/job-story-decision-tree.md`
  when the choice is ambiguous; `spike` for pure investigation.
- **`card.so_that`** — a concrete outcome (complete / verify / track / comply /
  resolve / receive / recover). "So I can use the system" fails INVEST-V.
- **`intent`** — one line, 300 characters maximum, describing what changes in the
  business when this ships. The cap is deliberate: the whole skeleton set must be
  readable in one sitting.
- **`rule_refs`** — non-empty for every non-spike story, schema-enforced. A story
  that honours no business rule means either the rule catalogue is incomplete or
  the story is not a story. Both are findings; neither is silently acceptable.
- **`sizing`** — 13 points forces `split_required: true`. Points above 13 are not
  in the enum; use `TBD_by_TL` with `split_required: true`.
- **`dependencies.depends_on`** — technical and temporal sequencing lives HERE,
  which is what keeps it out of the epic-grouping decision.

## MoSCoW

Priority per story. More than 70% `Must` across the breakdown triggers a P2 open
question addressed to the PM — an all-Must backlog has not been prioritised, it
has been transcribed.

## Cross-references

- `references/anti-patterns.md` — AP-1.3 (tier from label), AP-7.1 (layer split),
  AP-7.3 (unsplit density)
- `references/job-story-decision-tree.md` — story format choice
- `references/rules-domain-flows.md` — the catalogues the skeletons reference
