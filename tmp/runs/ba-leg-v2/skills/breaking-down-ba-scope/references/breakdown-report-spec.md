# breakdown.md — the three-amigos report

Binding contract for Procedure step 11. This is the **only** human-facing document
this stage emits. It replaces a multi-thousand-line offline HTML viewer and a
generated markdown tree; the run-level delivery-review console renders the pack
for anyone who wants to browse it afterwards.

## Constraints

- **Two pages.** Hard target: 120 lines. A reviewer who has to scroll for ten
  minutes before a meeting reads none of it.
- **Markdown, offline, no images, no HTML.** It is read in a terminal, an editor,
  a pull request and a chat window.
- **Derived, never authoritative.** Every fact comes from the JSON pack. On any
  conflict the JSON wins. Regenerating it from the same pack produces byte-identical
  output — no timestamps, no random ordering, no run-dependent values.
- **It is an agenda, not a summary.** Every section exists to provoke a decision
  from the developer or the tester in the room. Anything that provokes no
  decision belongs in the JSON only.

## Section order

### 1. Header

Epic count, story count, rule count, entity count, flow count, tier, and the
gate state — all from `count_check` and `state`. One table, no prose.

### 2. Blockers (only when there are any)

Every `governance_gaps[]` entry with `blocks: true`, with its owner. When the
list is empty, write one line saying so. When it is not, this section is first
after the header and says plainly that elaboration cannot start until a named
human clears it.

### 3. Epics and why they are epics

One block per epic: id, title, `business_value`, and — this is the part reviewers
actually argue with — the `decoupling.rationale` and the `merged_from` list.
Showing what was folded in prevents the session re-litigating a merge the
analysis already made deliberately.

### 4. Business flows

One compact ASCII path per flow: trigger, the numbered steps, decision points
with their rule ids, and the outcomes. This is the section a developer reads
first, because it is the only place the whole path appears.

```
FLOW-CUSTOMER-PURCHASE  (actor: registered customer)
  trigger: customer opens a product page with intent to buy
  1 customer  adds item to cart              [ENTITY-CART]
  2 customer  applies a coupon               [RULE-CHECKOUT-02]
  ? step 3 -- is stock still available?      [RULE-STOCK-01]
      available     -> 4
      last item won -> outcome: out of stock
  4 customer  confirms the order             [RULE-CHECKOUT-01, RULE-CHECKOUT-03]
  outcomes: order placed (paid) | payment declined (awaiting-payment) | out of stock (abandoned)
```

### 5. Business rules

One table: id, statement, type, and whether it is open. Open rules are listed
first — an open rule is a decision the session can close in thirty seconds that
would otherwise become a week of rework.

### 6. Domain entities and state machines

Per entity with a lifecycle, the states and the legal transitions as a compact
list. Fields appear only where `pii_class` is not `none` — the reviewer needs to
see the personal data, not the whole schema.

### 7. Story skeletons

One line per story: id, title, priority, points, and its rule ids. Grouped by
epic. No cards, no intent prose — those are in the JSON. The reviewer is checking
the *shape* of the backlog here, not reading each story.

### 8. Questions for this session

`open_questions[]` grouped by `for`, with the `dev` and `tester` groups first and
labelled as such. These are the reason the meeting exists. Each line: id,
severity, question, and the stories or rules it affects.

### 9. What happens next

Three lines: the verdict vocabulary (`agreed`, `split-stories`, `descope`,
`needs-rework`), that `agreed` releases elaboration, and that anything else
returns here with the findings attached.

## What must not appear

- Acceptance criteria or Gherkin — they do not exist yet, by design.
- Banking-grade concern rows — elaboration writes those.
- Any restatement of a rule in prose. Cite the id; the rule table is right there.
- Processing metadata, model names, token counts, durations, or any per-run
  timing. None of it survives a determinism check and none of it helps a reviewer.
- Real personal data, in any example. Redacted classes only.
