<!-- TEMPLATE · stage S5 QA Validation · owner: qa-squad lead · produced-by: executing-qa-test-suite (+ executing-* gap-fill skills) · audit_id: <audit_id:UUID> -->
# S5 QA Validation — Evidence Report

> **Dual output.** This stage emits **two** artifacts:
> 1. **Machine handoff:** a JSON verdict + this CSV evidence sidecar — the JSON (`verdict`, `findings[]`, `audit_id`) is the orchestrator's routing input. *S5 QA-execution is **deferred (GAP-05)**; when wired it emits a `qa-evidence` object (pass/fail per case). No boundary schema file under `../schemas/` yet.*
> 2. **This human-review document** — the **sync (L3)** gate (owner: qa-squad lead).
>
> **Mirrors** `agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/qa-report-csv.md`. Every fail must
> trace story → AC → expected → actual → evidence. Concrete language only; `evidence` links a file, never an inline blob.

## Verdict
- **Overall:** ☐ `pass` ☐ `code_mismatch` ☐ `criteria_unmet` ☐ `blocked`  ·  **Summary (1 paragraph):** `<…>`

## Evidence (one row per case)
```csv
case_id,scenario,verdict,expected,actual,ac_id,story_id,evidence
<svc>-001,"<one-sentence scenario>",pass,"<expected concrete>","matched",STORY_<SLUG>/AC-1,STORY_<SLUG>,<path/to/evidence.log>
<svc>-002,"<scenario>",fail,"<expected>","<divergence>",STORY_<SLUG>/AC-2,STORY_<SLUG>,<path/to/evidence.log>
```
Rules: `verdict` ∈ `pass|fail|skipped|error`; on `fail` `expected ≠ actual` and `evidence` non-empty; `ac_id`/`story_id` required for pass/fail.

## Failed cases → routing
| `case_id` | locus (file:handler) | routes_to | recommendation |
|---|---|---|---|
| `<…>` | `<…>` | `Dev` | `<one line>` |

## Sign-off (qa-squad lead — sync L3)
- **Approver:** `<name / role>`  ·  **Verdict:** ☐ Approve ☐ Approve-with-caveats ☐ Reject
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
