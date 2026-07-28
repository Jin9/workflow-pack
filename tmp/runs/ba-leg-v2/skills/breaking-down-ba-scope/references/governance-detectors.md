# Governance detectors and failure modes

Binding rules for Procedure steps 1–4 and 10. Failure-mode codes are carried over
from the predecessor skill unchanged, so the fleet vocabulary and the audit trail
survive the split. Codes that belong to elaboration (FM-02, FM-15, FM-16, FM-17)
are not this skill's and are not listed here.

**Why these run before the three-amigos gate:** a P1 governance gap discovered
during elaboration has already wasted the session. Detect it here, and a blocked
breakdown reaches a named human instead of three people's calendars.

## Step 1 — Preflight

**Ground-truth strip.** Detect the literal heading `## Intentional Issues for R6
to Catch` and the variants matching `^## (Intentional|Hidden|Ground[- ]Truth|Audit
Annotation)`; strip from that line to end of input as the **first** pass, before
anything else reads the text. Strip failure, boundary overlap, multiple blocks or
substring survival all **fail closed** — FM-12, `state: needs-clarification`,
`failure_code: preprocessing_failure`, and do not proceed.

**Firewall.** The strip operates on `raw_request` only. The `discovery` and
`scope` objects are structured input: never scanned for the heading, never
stripped. Neither can contaminate the strip pass nor be contaminated by it.

**Source-type detection.** Classify Jira / Slack / meeting / email / doc-prose:

| Type | Markers |
|---|---|
| Jira | bracketed key `[A-Z]+-\d+`; `Project:` / `Type:` / `Priority:` headers |
| Slack | channel banner; `Name (Role) — Today HH:MM`; emoji reactions |
| Meeting | `Meeting:` / `Date:` / `Attendees:` metadata; numbered agenda |
| Email | `From:` / `To:` / `Subject:` / `Date:` quartet; quote prefixes |
| doc-prose | no canonical markers — generic fallback at reduced confidence |

**FM-01.** Non-whitespace under 200 characters, or no extractable capability at
all, or composite input quality below 5.0 → `state: needs-clarification`,
`failure_code: empty_or_minimal_input`. Never fabricate an epic to have something
to emit.

## Step 2 — PII classification and redaction

Match direct identifiers (national id, passport, biometric), indirect (account
number, source of funds, politically-exposed-person status, sanctions match),
regulatory-confidential (suspicious-activity filing, tipping-off communication)
and financial (bank statement, wire detail).

**Never echo an actual value.** Replace with `[PII:REDACTED:CLASS=NRIC]` before
any analysis writes anything, and raise a P1 alert — a channel carrying raw
personal data is itself a finding. FM-13: if a clean output cannot be guaranteed,
emit `failure_code: pii_echo_blocked`.

Classification lands in `DOMAIN.json` `key_fields[].pii_class`, not in a separate
inventory. An entity holding customer data whose every field is `none` raises
`pii_class_missing` (P1, blocks) unless the entity file justifies it.

## Step 3 — Regulatory citations

Match `[A-Z]{2,}-[A-Z]{2,}-[A-Z0-9-]+` and named regulators
(`BOT|MAS|OFAC|FATF|FinCEN|PDPA|GDPR|PCI`). Classify each as **resolved**
(a specific section is cited) or **unresolved** (a regulator is named with no
citation).

FM-04: unresolved on T1 scope → `regulatory_citation_unresolved` (P1, blocks).
Unresolved on T2 → P1 open question addressed to Compliance, non-blocking.

Discovery may seed `regulatory_dependencies` leads at `citation_status: pending`.
A lead is **not** a citation: an unresolved citation still blocks T1. Discovery
cannot satisfy this detector.

## Step 4 — Stakeholders and the Legal-absence gate

Distinguish owner / sponsor / approver / subject-matter expert / affected /
external. **Never collapse roles.** Stamp each contribution's `authority_mode`
(rule / proposal / preference / estimate / pain) — rule mode is binding, the rest
are negotiable. Down-weight anonymous or paraphrased content via
`attribution_confidence`; an anonymous numeric policy parameter takes an
automatic P2 floor (AP-2.3).

**Enumerate the absent.** Include stakeholders who are implied but not present —
a data-protection officer once any field carries personal data, Treasury once
funds move, a security reviewer on biometric or upload scope — as
`stakeholders[]` rows with `status: absent` and `engagement_required_for`.
Declaring something out of scope does **not** discharge the enumeration row.

**`legal_status` is always emitted.** When it is anything other than `present`
and the scope touches retention, customer-facing language, tipping-off,
sanctions, biometrics, a regulator citation or dual approval → raise
`legal_absent_on_regulatory` at P1 with `blocks: true`. This fires on essentially
every regulatory-scope input; that is the intended behaviour, not a false
positive.

**Compliance is not Legal** (AP-3.2). Compliance describes what the regulation
says; Legal interprets what wording is permitted. A present compliance officer
never satisfies the Legal gate.

**Dual write.** Every absent-but-implied stakeholder appears BOTH as a
`stakeholders[]` row and, where it raises one, in `governance_gaps[]`. The gap
names the systemic risk; the row preserves the enumeration audit trail.

## Step 4b — Tipping-off scan

Run over every customer-facing string in the source for forbidden terms
(sanctions, anti-money-laundering, flagged, suspicious, regulated, suspicious
activity report, politically exposed person, adverse media, enhanced due
diligence). On a hit: FM-06 → `tipping_off_violation` at P1, replace with an
approved phrase from `references/non-tipping-vocabulary.md`, set
`legal_signoff_required`, and block.

## Step 10 — Assembly gates

Run all of these before emitting; any failure changes `state`, never the content.

| Code | Condition | Result |
|---|---|---|
| FM-01 | input too thin to break down | `needs-clarification` |
| FM-04 | unresolved citation on T1 | P1 gap, `blocked` |
| FM-05 | Legal absent on regulatory scope | P1 gap, `blocked` |
| FM-06 | tipping-off term in a customer-facing string | P1 gap, `blocked` |
| FM-11 | any emitted file fails its schema | emit nothing; never a malformed pack |
| FM-12 | ground-truth strip failed | `needs-clarification`, do not proceed |
| FM-13 | personal data would reach the output | `needs-clarification`, auto-redact |
| FM-14 | count inconsistency | schema error — see below |

**FM-14 count consistency.** All of: `count_check.epics` equals `epics[]` length;
`count_check.stories` equals `story_files[]` length and equals the sum of
`epics[].story_ids` lengths; every `story_files[].epic_id` resolves to an epic;
every `epics[].story_ids` entry resolves to a story file; `stakeholders[]`
contains a row for every absent role named in `governance_gaps[]`.

**`blocks_elaboration`** is true when any gap carries `blocks: true`. A blocked
breakdown may still go to the three-amigos session — the reviewers often have the
context that clears it — but elaboration never starts until a named human
resolves the gap. No verdict at the gate can clear a P1 governance gap; that is
deliberate and must not be relaxed.

## Cross-references

- `references/anti-patterns.md` — AP-2.3, AP-3.2, AP-5.1 and the full catalogue
- `references/non-tipping-vocabulary.md` — approved phrases and forbidden terms
- `references/rules-domain-flows.md` — where PII and retention findings land
