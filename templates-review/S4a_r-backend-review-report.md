<!-- TEMPLATE · stage S4a-r Backend Review · owner: dev-squad · produced-by: review-backend-code ^1.0.0 · audit_id: <audit_id:UUID> -->
# S4a-r Backend Review — Report

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff, schema-validated): [`../schemas/backend-review.json`](../schemas/backend-review.json) — required fields `verdict`, `findings`, `audit_id`.
> 2. **This human-review document** — the async peer (L2) review gate (owner: dev-squad). **An agent never approves its own code** — review identity ≠ impl identity.
>
> **Mirrors** `agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/reviewer-finding.md` (L1).
> Calibration: *"could a careful human have written this and been right?"* — don't inflate a style nit to high.
> Severity routing: high/medium → back to Dev (loop cap 2) · low → ADVISORY.

## Verdict
- **`verdict`:** ☐ `pass` ☐ `advisory_only` ☐ `block`  ·  **Summary (1 paragraph):** `<…>`
- **Skills invoked:** `<reviewing-software-security, simplify, …>`

## Findings
| `id` | `severity` | `diagnosis_tag` | `routes_to` | `locus` (file:line) | description | recommendation | `cwe_refs` |
|---|---|---|---|---|---|---|---|
| `REV-<COMP>-001` | `<high/medium/low>` | `<code_security_issue / latent_bug / code_quality_issue / style_nit / spec_induced_security_issue / spec_induced_latent_bug>` | `<Dev / Tech-Designer / Tech-Lead / null>` | `<app/<svc>/service.go:NN>` | `<1-3 sentences>` | `<one line>` | `<CWE-… / ASVS-…>` |

## Sign-off (dev-squad — async peer L2, maker ≠ checker)
- **Reviewer:** `<name / role — not the implementer>`  ·  **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
