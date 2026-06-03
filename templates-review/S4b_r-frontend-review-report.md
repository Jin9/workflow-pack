<!-- TEMPLATE · stage S4b-r Frontend Review · owner: dev-squad · produced-by: review-frontend-code ^1.0.0 · audit_id: <audit_id:UUID> -->
# S4b-r Frontend Review — Report

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/frontend-review.json`](../schemas/frontend-review.json) — required fields `verdict`, `findings`, `audit_id`.
> 2. **This human-review document** — the async peer (L2) review gate (owner: dev-squad). Review identity ≠ impl identity.
>
> **Mirrors** `agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/reviewer-finding.md`.
> Severity routing: high/medium → back to Dev (loop cap 2) · low → ADVISORY. Same anti-inflation calibration as S4a-r.

## Verdict
- **`verdict`:** ☐ `pass` ☐ `advisory_only` ☐ `block`  ·  **Summary (1 paragraph):** `<…>`
- **Skills invoked:** `<reviewing-software-security, simplify, …>`

## Findings (quality + security + UI)
| `id` | `severity` | `diagnosis_tag` | `routes_to` | `locus` (file:line) | description | recommendation | `cwe_refs` |
|---|---|---|---|---|---|---|---|
| `REV-FE-001` | `<high/medium/low>` | `<code_security_issue / latent_bug / code_quality_issue / style_nit / a11y_issue / perf_issue>` | `<Dev / Tech-Designer / Tech-Lead / null>` | `<components/<x>.tsx:NN>` | `<1-3 sentences>` | `<one line>` | `<CWE-… / WCAG-…>` |

## Accessibility / performance notes
- **WCAG 2.1 AA:** `<contrast / keyboard / aria — pass or finding>` (track OI-004)  ·  **Perf budget:** `<bundle / LCP — pass or finding>`

## Sign-off (dev-squad — async peer L2, maker ≠ checker)
- **Reviewer:** `<name / role — not the implementer>`  ·  **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
