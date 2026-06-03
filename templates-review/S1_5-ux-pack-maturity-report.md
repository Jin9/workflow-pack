<!-- TEMPLATE · stage S1.5 UX Intake · owner: Tech Lead · produced-by: generate-ux-pack ^0.1.0 / ux-intake-audit · audit_id: <audit_id:UUID> -->
# S1.5 UX Intake — UX Pack Maturity Report

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/ux-intake.json`](../schemas/ux-intake.json) — required fields `pack_dir`, `tokens_path`, `route_map_path`, `maturity_level`, `audit_id`.
> 2. **This human-review document** (rendered from this template) — the async peer (L2) review gate (owner: Tech Lead).
>
> Fill every `<…>` / `TBD-<what>-<who>`. Never invent coverage; mark missing assets explicitly. No real PII.

## Maturity verdict
- **`maturity_level`:** `<level / score>`  ·  **`pack_dir`:** `<path>`
- **One-line state:** `<is the UI work ready to design against? what's blocking?>`

## Design tokens
- **`tokens_path`:** `<path>`  ·  **Coverage:** `<color / type / spacing / elevation — present? gaps?>`

## Route map
- **`route_map_path`:** `<path>`  ·  **Routes covered vs stories:** `<N/M>`  ·  **Unmapped stories:** `<…>`

## Accessibility (WCAG 2.1 AA)
| Check | Status | Note |
|---|---|---|
| Contrast | `<pass/FAIL>` | OI-004 contrast finding — `TBD-contrast-resolution-UX` |
| Keyboard / focus order | `<…>` | … |
| Labels / alt text | `<…>` | … |

## TBD ledger (assets not yet provided)
- `TBD-<asset>-<who-provides>`

## Sign-off (Tech Lead — async peer L2)
- **Reviewer:** `<name / role>`  ·  **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
