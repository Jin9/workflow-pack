<!-- TEMPLATE · stage S2.5 Plan-Review · owner: Tech Lead · produced-by: red-teaming-implementation-plan · audit_id: <audit_id:UUID> -->
# S2.5 Plan-Review — Findings

> **Dual output.** This stage emits **two** artifacts:
> 1. **JSON contract → next node** (machine handoff): a `plan-review` object — `verdict`, `summary`, `findings[]`, `audit_id`. *(S2.5 is a supervision-design gate, not yet a wired pipeline stage, so it has no boundary schema file under `../schemas/` — the shape below is the contract.)*
> 2. **This human-review document** — surfaced to a human **on HardFail** (owner: Tech Lead).
>
> **Mirrors** the reference blueprint `agentic-delivery-pipeline/reference/squad-flow-v0.7/docs/templates/plan-reviewer-finding.md`.
> Red-team the BA + TL plan **before** the expensive fan-out. Calibration rule: *"could a careful human producer
> reasonably have written this and been right?"* → if yes, downgrade. Plan-stage cap = 1; second `block` ⇒ **HardFail**.

## Verdict
- **`verdict`:** ☐ `pass` ☐ `advisory_only` ☐ `block`
- **Summary (1 paragraph — state of the plan):** `<…>`

## Findings
| `id` | `severity` | `diagnosis_tag` | `routes_to` | `locus` | description (problem only) | recommendation (one line) |
|---|---|---|---|---|---|---|
| `PR-001` | `<high/medium/low>` | `<requirements_gap / requirement_ambiguity / missing_edge_case / architecture_risk / contract_ambiguity / unstated_assumption / complexity_misjudged / plan_polish>` | `<BA / Tech-Lead / null>` | `<ba.json#/… or contracts.json#/…>` | `<1-3 sentences>` | `<concrete fix>` |

*Routing: `requirements_gap`/`requirement_ambiguity`/`missing_edge_case` → BA · `architecture_risk`/`contract_ambiguity`/`complexity_misjudged` → Tech-Lead · `unstated_assumption` → specify BA or Tech-Lead · `plan_polish` → no route (advisory). `routes_to` is REQUIRED for every non-low finding.*

## Human review (on HardFail — Tech Lead)
- **Reviewer:** `<name / role>`  ·  **Decision:** ☐ Re-plan ☐ Override-with-rationale ☐ Abort
- **Date:** `<YYYY-MM-DD>`  ·  **audit_id:** `<audit_id:UUID>`  ·  **Notes:** `<…>`
