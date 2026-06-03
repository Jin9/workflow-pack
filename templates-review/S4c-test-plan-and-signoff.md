<!-- TEMPLATE · stage S4c QA Test Design · owner: qa-squad lead · produced-by: planning-banking-tests ^1.0.0 · audit_id: <audit_id:UUID> -->
# S4c QA Test Design — Test Plan & Sign-off Criteria

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/qa-plan.json`](../schemas/qa-plan.json) — required fields `test_roster`, `signoff_criteria`, `audit_id`.
> 2. **This human-review document** — the **sync on conditional-go (L3)** gate (owner: qa-squad lead).
>
> Maps business logic → a test roster across levels. *Design only* — execution is S5 (deferred, GAP-05). No real PII.

## Test roster (per story → cases, by level)
| `story_id` / AC | Level | Case (one sentence) | Expected (concrete) | Mechanism / skill |
|---|---|---|---|---|
| `STORY_<SLUG>/AC-N` | `<unit / integration / contract / e2e / security / performance / a11y / smoke>` | `<…>` | `<HTTP/code/value>` | `<executing-* / contract-testing-pact / running-* skill>` |

## Coverage rubric
- **Levels required for this change:** `<…>`  ·  **Coverage target:** `<e.g. 0.80>`  ·  **Out-of-scope levels (why):** `<…>`

## Execution DAG (how S5 will run it)
- Fan out off `be.artifacts` / `fe.artifacts` / `qa.plan`: `<unit ∥ integration → contract → e2e → security → perf → a11y>`

## Sign-off criteria (`signoff_criteria`)
- **Go conditions:** `<all high ACs pass · coverage ≥ target · no open P1>`
- **Conditional-go conditions:** `<documented caveats → KNOWN_ISSUES>`

## Sign-off (qa-squad lead — sync L3 on conditional-go)
- **Approver:** `<name / role>`  ·  **Verdict:** ☐ Go ☐ Conditional-go ☐ No-go
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
