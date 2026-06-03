<!--
  =========================================================================
  USER-STORY TEMPLATE  (reusable)
  =========================================================================
  HOW TO USE
  1. Copy this file and rename it for your story (e.g. ISSUE-KEY-slug.md).
  2. Replace every `<placeholder>` (shown in backticks, angle brackets) with real content.
  3. Guidance lives in HTML comments tagged HOW: and EXAMPLE:. It is invisible in the
     rendered Markdown; delete it before publishing if you prefer a clean file.
  4. Keep the sections you need and delete the rest. Only Title and Description are required.
  5. Sections tagged METADATA are normally auto-populated by the tracker (Jira) — keep them
     only when you are mirroring a full ticket export.
  Story content may be written in any language; this scaffolding is English.
  =========================================================================
-->

`< Back`  ·  `<ISSUE-KEY>`  ·  `<RELATED-KEY>`

<!-- HOW: Breadcrumb plus the issue key(s) as they appear in the tracker. List related keys after the primary one. Drop this line if your tool shows keys elsewhere. -->
<!-- EXAMPLE: `< Back` · DGL-9820 · DGL-10081 -->

# [`<TYPE>`] `<imperative title>`

<!-- HOW: A type tag in brackets plus a short imperative title. Common tags: [BAU], [Feature], [Bug], [Spike]. -->
<!-- EXAMPLE: # [BAU] Enhance tier-rate offering for the Krungthai Jai Pa loan -->

## Description

<!-- HOW: Classic three-part user story. One role, one capability, one business value. Keep "I want" to a single capability. -->
<!-- EXAMPLE: As a business unit / I want to offer tier-rate interest on the personal-loan product to customers earning above the risk-engine threshold (30,000 THB) / So that the offered rate matches the salary base and stays competitive in the market. -->

*As a* `<role / persona>`

*I want* `<one capability>`

*So that* `<benefit / business value>`

## Product

<!-- HOW: The product or feature area this story belongs to. One line. -->
<!-- EXAMPLE: Krungthai Jai Pa — new loan -->

`<product / feature area>`

## Background

<!-- HOW: Why this story exists — the trigger, the prior state, or the business driver. Number the points if there are several. -->
<!-- EXAMPLE: 1. Add a tier-rate offer for customers whose monthly income exceeds 30,000 THB. -->

1. `<context point>`

## Business Logic

<!-- HOW: The rules the system must enforce, numbered. Use a./b./c. sub-items for detail.
     Add a table for decision matrices, and a > callout for cross-cutting notes (flexibility, effective dates, ownership). -->
<!-- EXAMPLE: 1. Support tier-rate: (a) requirement covers 2 tiers; (b) system supports at least 5 tiers. -->

1. `<rule>`
   a. `<detail>`
   b. `<detail>`
2. `<rule that references the decision table below>`

### `<Decision matrix name>`

<!-- HOW: A decision table mapping input conditions to outcomes — one row per case. Delete this sub-section if the story has no decision matrix. -->
<!-- EXAMPLE: "Income -> Interest-rate tiers": income source (SA/SE) x KTB payroll (Yes/No) x monthly income -> annual rate.
     e.g. SA + Yes + ">= 30,000 THB (multi-tier)" -> months 1-3: 7.99%, month 4+: 20%. -->

| `<Dimension 1>` | `<Dimension 2>` | `<Condition>` | `<Outcome>` |
|---|---|---|---|
| `<value>` | `<value>` | `<condition>` | `<outcome>` |
| `<value>` | `<value>` | `<condition (multi-tier)>` | `<e.g. months 1–3: rate A; month 4+: rate B>` |

<!-- HOW: Use a > callout for a rule that cuts across the whole table above. -->
<!-- EXAMPLE: rates follow whatever the risk engine returns; the driving inputs are income, income source, KTB payroll, and the effective dates. -->
> ⚠️ **Note:** `<cross-cutting rule or exception that applies across the rules above>`

## Acceptance Criteria

<!-- HOW: Testable pass/fail conditions. Each item must be verifiable. Number them. -->
<!-- EXAMPLE: 1. System offers a single-tier loan when income < 30,000 THB.  2. System offers multi-tier rates and stores up to 5 tiers. -->

1. `<testable condition>`
2. `<testable condition>`

## Out of Scope

<!-- HOW: What this story explicitly does NOT cover. Prevents scope creep; name the owning team when it belongs elsewhere. -->
<!-- EXAMPLE: 1. Renaming the "interest rate" label on the NEXT input screen (owned by the NEXT team). -->

1. `<excluded item>`

---

## Mock-up references

<!-- HOW: One numbered entry per mock-up. Show AS-IS / TO-BE (or Before / After) and add a Spec API line when an API changes.
     When the mock-up is only an image, describe the highlighted diff in words rather than pasting pixels. Delete this whole section if there are no mock-ups. -->
<!-- EXAMPLE: 1. Loan Decision — CMLOS to DGL (Before/After JSON): the After payload adds a tierList[] array
     (tierStartTier, interestIndex, interestSpread, paymentNo). Spec API: POST /api/smart-money/updateStatus v2025.11.24 -->

### 1. `<mock-up name>`

- **AS-IS:** `<current state>`
- **TO-BE:** `<changed state — call out the highlighted diff>`
- **Spec API:** `<METHOD /path version>`   <!-- optional; delete if no API change -->

---

## Attachments (`<N>`)

<!-- METADATA — the tracker usually auto-populates this. Keep only when mirroring a full ticket export. -->
<!-- HOW: List supporting files with size and date added. -->
<!-- EXAMPLE: | payment_calc.xlsx | 2.2 MB | Aug 15, 2025 | -->

| Name | Size | Date added |
|---|---|---|
| `<filename>` | `<size>` | `<date>` |

## Subtasks

<!-- METADATA — child tasks of this story. -->
<!-- EXAMPLE: - DGL-XXXX  `<short subtask title>` -->

*Add subtask* — `<none / list>`

## Linked work items

<!-- METADATA — related issues (blocks / is blocked by / relates to). -->

*Add linked work item* — `<none / list>`

## Confluence content

<!-- METADATA — linked Confluence pages or API specs. -->
<!-- EXAMPLE: - POST /api/smart-money/updateStatus v2025.11.24 — Updated -->

- `<linked page / spec>`

---

## Activity

<!-- METADATA — discussion log, usually captured by the tracker. -->

Tabs: **All · Comments · History · Work log · Approvals**

### Comments summary

<!-- HOW: A short prose summary of the key decisions and approvals, if you keep a written log. -->
<!-- EXAMPLE: Implemented tiered interest to improve competitiveness for customers earning > 30,000 THB; first deployment late Aug 2025, supporting up to 5 tiers. -->

`<summary>`
