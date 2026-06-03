# Governance & Gates

> The supervision controls for the pipeline: where humans approve, what agents may and may not *do*, who is
> accountable, and how the work is observed. Companion to [`agentic-workflow.md`](./agentic-workflow.md).

## 1. Gate matrix (by reversibility & blast radius)

Gates are placed where an action is hard to reverse or has downstream blast radius — **not uniformly**. Reversible,
read-only drafting is auto/async; irreversible or high-blast actions require a **synchronous named human approval**,
regardless of how confident the agent is.

| Gate | After stage | Action being gated | Reversibility | Blast radius | Gate type | Approver |
|------|-------------|--------------------|---------------|--------------|-----------|----------|
| **G1** | S1 | confirm scope | reversible draft | anchors all downstream work | **sync named** | BA / PM |
| **G2** | S2 | accept Story Set | reversible artifact | low | async review | BA |
| **G3** | S3 | resolve a governance/compliance blocker | hard to reverse once shipped | **high** (legal/privacy) | **sync named** | BA + SME (Legal / DPO / Compliance) |
| **G4** | S4 | feasibility verdict | sets build scope & cost | medium–high | **sync named** | TL |
| **G5** | S5 | accept handoff bundle | engineering builds on it | **high** | **sync named** | TL (owner of record) |

Rule of thumb: **an agent never passes an irreversible or control-plane gate on its own confidence.** Confidence
tunes whether a *reversible* step gets async review; it never unlocks a sync-named gate.

## 2. Command-safety policy (allow / confirm / deny)

Enforced **outside the model**, at the tool-calling layer — so a drifting or hijacked agent cannot grant itself a
denied action. The agent does not decide what is allowed.

| Tier | Actions | Rationale |
|------|---------|-----------|
| **ALLOW** (reversible, sandboxed) | read the raw requirement; classify/parse it; draft a Scope Sheet / Story Set / Governance Check / Feasibility Note; render a diagram; write inside `output/` | reversible, no external effect — no human needed |
| **CONFIRM** (irreversible / control-plane) | publish the TL Handoff Bundle; mark a blocker resolved; set `state: ready-for-tl`; write to a shared backlog / Jira; override an upstream contract's scope | each maps to a gate above; needs the named human |
| **DENY** (outside allowlist) | echo real PII in any artifact; auto-resolve a governance blocker; write outside `output/`; call a non-allowlisted tool/MCP; modify another agent's contract or its own permissions | structurally unsafe — blocked by policy, not by prompt |

## 3. Never-do guardrails (harness-enforced)

A bounded set the harness/policy engine enforces — not prompt wishes:

1. **Never echo real PII.** Redact to `<PII:REDACTED:CLASS=…>`; personal data stays out of every artifact and log.
2. **Never silently repair a defect.** Ambiguities and gaps are *surfaced* (open questions / blockers), never quietly fixed.
3. **Never auto-resolve a blocker.** Only a named human clears a Governance Check blocker.
4. **Never hand off while a blocker is open.** `ready-for-tl` is impossible with an unresolved blocker.
5. **Never let an agent relax a gate** or approve its own output.
6. **Never conflate Compliance with Legal.** Compliance describes the rule; Legal interprets the wording — different owners.

## 4. Accountability map

AI output → distinct agent identity → accountable human owner of record. No AI is credited as an accountable co-author.

| Stage | Agent identity | Tools (least agency) | Human owner of record |
|-------|----------------|----------------------|-----------------------|
| S1 Intake & Scope | `intake-agent` | read input; write Scope Sheet | **BA lead** |
| S2 Story Drafting | `story-agent` | read Scope Sheet; write Story Set | **BA lead** |
| S3 Governance & Risk | `governance-agent` | read Story Set; write Governance Check (flag only) | **BA lead + named SME** (Legal/DPO/Compliance) |
| S4 Feasibility & Scope | `feasibility-agent` | read Story Set + Governance Check + raw req; write Feasibility Note | **Tech Lead** |
| S5 TL Handoff | (composition) | assemble bundle | **Tech Lead** (final owner of record) |

**Least agency:** each agent is scoped to its one stage; reading the raw input is separated from publishing the
handoff; no agent holds long-lived credentials or write access to engineering repos.

## 5. Observability

| Dimension | Design |
|-----------|--------|
| **Correlation** | one **`task_id`** (the requirement id) propagated S1→S5 — the single trace id |
| **Both halves of the loop** | per stage, log the **model call** *and* the **artifact emitted** (the tool effect) + the handoff event |
| **Model version** | recorded on every stage's log entry |
| **Tamper-evidence** | append-only / hash-chained stage log recommended (the worked example shows this audit posture) |
| **Reasoning** | agent reasoning kept as *context*, not treated as evidence of correctness |
| **What pages a human** | a `blocked` Governance Check; a stage exceeding its retry cap; a `needs-clarification` return |

## 6. Pre-execution caps

- **Retry cap** per stage for transient draft/schema errors (small, hard limit) — then stop, don't loop.
- **HITL escalation is the final tier**: when an agent cannot proceed safely it stops and asks a human; it never
  forces a path through a gate.
- Caps **terminate** the run; they are not alert-only dashboards.
