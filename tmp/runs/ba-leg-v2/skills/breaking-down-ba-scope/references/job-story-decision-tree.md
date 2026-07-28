# Job Story vs Classic User Story Decision Tree

> Decide between Job Story and Classic User Story per candidate. Loaded by `SKILL.md` Step 7 when format choice is ambiguous (multiple candidate roles, concrete weighty trigger, no author format signal). Skip when format is obvious.

## Purpose & Default

**Default rule**: emit Job Story format unless role is clearly the primary differentiator. Job Stories emphasize situation/trigger over role; better for context-rich banking flows where multiple personas can use the same capability under different conditions.

Sources: ba-best-practices §3; C9 (story boundaries informs role-dominance); A4 §1, §2 (stakeholder role types).

## Decision Tree

Run nodes top-to-bottom; first match wins. Each leaf emits `format` + `confidence`.

1. Is **role** the primary differentiator (admin vs user; compliance officer vs applicant; senior approver vs analyst)? → **Classic** (high confidence).
2. Could **multiple roles** use the same capability under different conditions? → **Job** (high confidence).
3. Does the **trigger** (state, time, rate-limit, retry-count, hold-type) drive behavior more than the role? → **Job** (high).
4. Is there a **single dominant persona** with no situational variation? → **Classic** (medium).
5. Banking workflow with **trigger conditions** (rate-limit reached, hold-type compliance vs ops, retry-count exhausted, sanctions match)? → **Job** (high).
6. **Admin-vs-user permission split**, or capability scoped to authority? → **Classic** (high).
7. **Compliance officer reviewing a case**, signing off, or making a tiered approval decision? → **Classic** (high — authority-bound).
8. **Customer experiencing a state change** (rejection, hold, additional review, re-upload prompt)? → **Job** (high — situation-bound).
9. **Vendor liaison action** distinct from vendor entity action (Hua vs Acuant)? → **Classic** (medium — role-scoped).
10. **Note-taker / meta-stakeholder** action? → not a story (filter at Step 5).
11. Tie / can't decide? → **Default Job Story** (medium confidence; document override in BA Reasoning Trace).

## Job Story Format + Examples

Template:

```
When <situation/trigger>,
I want to <capability>,
So I can <outcome/benefit>.
```

Banking examples:

- **r1 (lending re-upload)**: `When my document upload fails verification, I want to re-upload a corrected document with a clear reason for the original rejection, So I can complete my loan application without re-starting.`
- **r2 (wire on additional review)**: `When my wire transfer is placed on additional review, I want to see a clear status and expected resolution window, So I can plan my cash flow without contacting support.`
- **r3 (EDD intake)**: `When I am asked for enhanced due diligence documents, I want to upload them via mobile or web with progress confirmation, So I can complete onboarding without back-and-forth email.`

## Classic User Story Format + Examples

Template:

```
As a <role>,
I want <capability>,
so that <benefit>.
```

Banking examples:

- **r3 (compliance officer reviewing high-risk)**: `As a compliance officer, I want to review a high-risk case with side-by-side risk-engine output and source documents, so that I can make a defensible tiered-approval decision within 4 business hours.`
- **r3 (senior approver dual sign-off)**: `As a senior approver, I want to receive a dual-signoff queue for cases above the high-risk threshold, so that I can ensure no high-risk case approves without second-level review.`

## Quality Criteria Per Format

### Job Story checklist

- Trigger is concrete (not "when needed" or "when applicable"). Resolves to a state / event / condition.
- Capability is bounded (one user-facing capability, not a workflow chain).
- Outcome is observable (not "feel good"; "complete loan application").

### Classic User Story checklist

- Role named with authority scope ("senior approver" not "user"; "compliance officer" not "team member").
- Capability is permission-scoped (action role can perform vs cannot).
- Benefit is role-specific (compliance audit defensibility; not generic "value").

## Default Rule & Override Conditions

**Default**: Job Story.

**Override to Classic** only when:

- Role is clearly the primary differentiator (admin vs user permission split).
- Authority scope drives the capability (only senior approvers can dual-sign).
- The same capability has materially different ACs by role boundary (use C28 to split into 2 stories instead of merging).

When overriding, record the decision as a P3 open question addressed to the BA with the source quote that named the role-dominance. (`ba_reasoning_trace` was cut on 2026-07-28 — the reasoning belongs where a human will act on it, not in a field nobody reads.)

## Mixed-Format Anti-Pattern

Do NOT switch format mid-epic without justification. If a single epic mixes Job and Classic stories, document why per story; otherwise the inconsistency signals unstructured decomposition. Most banking epics will mix legitimately (customer-facing stories Job; back-office stories Classic) — that's fine when each is justified.

## Cross-References

- `invest-checklist.md` §3 (V + N letters interact with format choice)
- `ba-best-practices.md` §3 (canonical authority)
- `epic-and-stories.template.md` (both format examples)
