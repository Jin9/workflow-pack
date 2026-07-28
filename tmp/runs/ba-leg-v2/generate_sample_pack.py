#!/usr/bin/env python3
"""Emit the regenerated ShopPilot BA leg under the new breakdown/elaboration shape.

Deterministic by contract: no clock, no randomness, no environment reads. The
same inputs produce byte-identical output, so a rebuild can be diffed.

    python3 tmp/runs/ba-leg-v2/generate_sample_pack.py
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sample_data import (  # noqa: E402
    ENTITIES, FLOWS, GLOSSARY, IDEMPOTENCY_KEY, OPEN_QUESTIONS, RULES,
    SOURCE_DOC, STAKEHOLDERS,
)
from sample_stories import (  # noqa: E402
    ACCEPTANCE, ASSUMPTIONS, BANKING_GRADE, EDGE_LEDGER, EPICS, HIDDEN_SWEEP, STORIES,
)

HOUSE_NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://squad-delivery/audit")
OUT = ROOT / "sample-pack"
BGC_ORDER = ["pii_fields", "audit_events", "idempotency", "reversibility",
             "authn_authz", "regulatory", "tipping_off"]


def house_audit_id(stage: str) -> str:
    return str(uuid.uuid5(HOUSE_NS, f"{stage}:{IDEMPOTENCY_KEY}"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def slug(title: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")


BREAKDOWN_AUDIT = house_audit_id("ba-breakdown")
BRIEF_AUDIT = house_audit_id("ba-research")
DISCOVERY_AUDIT = house_audit_id("s1-discovery")

STORY_BY_ID = {s[0]: s for s in STORIES}
EPIC_BY_PREFIX = {e["story_prefix"]: e for e in EPICS}


def epic_of(story_id: str) -> dict:
    return EPIC_BY_PREFIX[story_id.split("-")[1]]


def rules_for_epic(epic_id: str) -> list[str]:
    out: list[str] = []
    for sid, *_rest in [(s[0],) for s in STORIES]:
        if epic_of(sid)["id"] != epic_id:
            continue
        for r in STORY_BY_ID[sid][6]:
            if r not in out:
                out.append(r)
    return out


def flows_for_epic(epic_id: str) -> list[str]:
    return [f["id"] for f in FLOWS
            if any(epic_of(sid)["id"] == epic_id for sid in f["story_refs"])]


# ---------------------------------------------------------------- S1a discovery
def emit_discovery() -> None:
    discovery = {
        "problem_framing": {
            "problem": (
                "A single Thai merchant sells only by phone and chat. Customers cannot complete a purchase "
                "themselves, and staff reconstruct stock, orders and promotions from memory and message threads."
            ),
            "who": (
                "B2C retail customers in Thailand, guest and registered, plus the merchant's own back-office "
                "staff. Isolation between customers is treated as non-negotiable."
            ),
            "why_now": (
                "This is the merchant's first online storefront and the squad's vehicle for proving an "
                "end-to-end delivery workflow on a small but complete MVP that must actually sell."
            ),
        },
        "opportunities": [
            "A direct self-serve sales channel: customers complete a purchase on the web without phone or chat.",
            "A unified back-office console for catalogue, stock, orders, fulfilment and coupons.",
            "A storefront that actually sells: real stock reservation, server-computed totals and idempotent confirm, so no overselling and no double charges.",
            "An extensible foundation that admits a real payment provider, real shipping and a loyalty programme without a rebuild.",
        ],
        "assumptions": [
            {"statement": "Thai B2C shoppers will complete purchases unassisted rather than reverting to phone or chat ordering.",
             "risk_type": "value", "confidence": "medium",
             "de_risk": "Instrument the registration-to-first-purchase and checkout-to-payment funnels (gap-closed 3.1, 3.2) and read them post-launch."},
            {"statement": "Guest, customer and admin can each complete their core flows without training, including applying a coupon at checkout.",
             "risk_type": "usability", "confidence": "medium",
             "de_risk": "Moderated prototype tests on the checkout and admin-fulfilment flows against the accessibility targets in gap-closed 20."},
            {"statement": "Atomic stock reservation with a 30-minute expiry, last-item-race resolution, idempotent confirm and replay-safe callbacks can be built and hardened in the one-sprint budget.",
             "risk_type": "feasibility", "confidence": "low",
             "de_risk": "Time-boxed spike on the reservation and idempotency concurrency model before commit."},
            {"statement": "PDPA obligations, the Consumer Protection Act disclosure duty and a PCI-out-of-scope payment model are all operable at single-merchant scale.",
             "risk_type": "viability", "confidence": "high",
             "de_risk": "Largely de-risked in the governance workshop (gap-closed 14 to 20: named owners, resolved citations); confirm the manual-refund SOP is staffed."},
        ],
        "regulatory_regimes": [
            "PDPA B.E. 2562: per-field lawful basis, data-subject access, correction and erasure, separate marketing consent, breach-notification path. Resolved in gap-closed 15 and 18.",
            "Data residency: personal data confined to the Thailand and Singapore (ap-southeast) region (gap-closed 16).",
            "Revenue Code: 5-year retention envelope for order, financial and audit records (gap-closed 16).",
            "Consumer Protection Act and Electronic Transactions Act: the total is shown before payment and the confirmation is an electronic record (gap-closed 18).",
            "PCI-DSS v4.0: no card data is collected or stored, so ShopPilot stays out of cardholder-data scope (gap-closed 18).",
            "Not in play: KYC, AML and sanctions screening. There is no account opening, lending or money movement beyond retail payment; flagged so the breakdown does not assume a financial-crime regime.",
        ],
        "recommendation": "proceed",
        "handoff_to_intake": {
            "tier_signal": "T2",
            "stakeholder_hints": ["Data Protection Officer", "Legal Counsel", "Compliance Officer", "Finance Lead"],
        },
        "audit_id": DISCOVERY_AUDIT,
    }
    write_json(OUT / "S1a-discovery" / "discovery.json", discovery)

    pf = discovery["problem_framing"]
    md = [
        "# BA Discovery — ShopPilot MVP",
        "",
        f"**Recommendation: {discovery['recommendation'].upper()}** — a named human decides at the gate; only `proceed` releases the breakdown.",
        "",
        "## Problem",
        "", f"**What.** {pf['problem']}", "", f"**Who.** {pf['who']}", "", f"**Why now.** {pf['why_now']}",
        "",
        "## Opportunities",
        "",
    ]
    md += [f"- {o}" for o in discovery["opportunities"]]
    md += ["", "## The four product risks", "", "| Risk | Assumption | Confidence | How we de-risk it |", "|---|---|---|---|"]
    for a in discovery["assumptions"]:
        md.append(f"| {a['risk_type']} | {a['statement']} | {a['confidence']} | {a['de_risk']} |")
    md += ["", "## Regulatory regimes in play", ""]
    md += [f"- {r}" for r in discovery["regulatory_regimes"]]
    md += ["", "## Handoff to breakdown", "",
           f"Tier floor `{discovery['handoff_to_intake']['tier_signal']}` and stakeholder hints "
           f"({', '.join(discovery['handoff_to_intake']['stakeholder_hints'])}) are **advisory**: "
           "they may raise a tier or seed a row, never suppress a detector or satisfy a citation.",
           "", f"`audit_id` {discovery['audit_id']}"]
    write_text(OUT / "S1a-discovery" / "discovery.md", "\n".join(md))


# ---------------------------------------------------------------- S1b breakdown
def emit_breakdown() -> None:
    d = OUT / "S1b-breakdown"

    write_json(d / "RULES.json", {
        "audit_id": BREAKDOWN_AUDIT,
        "rules": [
            {
                "id": rid, "statement": stmt, "type": rtype, "source_ref": src, "tier": tier,
                "applies_to_entities": ents,
                "story_refs": [s[0] for s in STORIES if rid in s[6]],
                **({"regulatory_tie": reg} if reg else {}),
                "open": False,
            }
            for rid, stmt, rtype, src, tier, ents, reg in RULES
        ],
    })

    write_json(d / "DOMAIN.json", {"audit_id": BREAKDOWN_AUDIT, "entities": ENTITIES, "glossary": GLOSSARY})

    for flow in FLOWS:
        write_json(d / f"{flow['id']}.json", flow)

    for epic in EPICS:
        stories = [s for s in STORIES if epic_of(s[0])["id"] == epic["id"]]
        write_json(d / f"{epic['id']}.json", {
            "id": epic["id"], "title": epic["title"], "story_prefix": epic["story_prefix"],
            "problem_statement": epic["problem_statement"], "business_value": epic["business_value"],
            "why_now": epic["why_now"], "success_criteria": epic["success_criteria"],
            "decoupling": epic["decoupling"], "scope": epic["scope"],
            "stakeholders": [{k: v for k, v in s.items() if k in ("role", "name_or_team", "raci", "status")}
                             for s in STAKEHOLDERS],
            "legal_status": epic["legal_status"], "inferred_tier": epic["inferred_tier"],
            "tier_signals": epic["tier_signals"],
            "rule_refs": rules_for_epic(epic["id"]), "flow_refs": flows_for_epic(epic["id"]),
            "story_refs": [{"id": s[0], "file": f"{s[0]}.json", "title": s[1]} for s in stories],
        })

    for sid, title, as_a, i_want, so_that, intent, rule_refs, entity_refs, prio, pts, cx, dep, blk in STORIES:
        oq = [q["id"] for q in OPEN_QUESTIONS if sid in q["related_story_ids"]]
        write_json(d / f"{sid}.json", {
            "id": sid, "epic_id": epic_of(sid)["id"], "title": title, "format": "classic_user_story",
            "card": {"as_a": as_a, "i_want": i_want, "so_that": so_that},
            "intent": intent, "rule_refs": rule_refs,
            "flow_refs": [f["id"] for f in FLOWS if sid in f["story_refs"]],
            "entity_refs": entity_refs, "priority": prio,
            "sizing": {"story_points": pts, "complexity": cx, "split_required": pts >= 13},
            "dependencies": {"depends_on": dep, "blocks": blk},
            **({"open_question_refs": oq} if oq else {}),
            "requirement_refs": ["shoppilot-mvp"],
        })

    index = {
        "audit_id": BREAKDOWN_AUDIT, "stage": "ba-breakdown", "state": "ready-for-amigos",
        "produced_by": "breaking-down-ba-scope 1.0.0", "idempotency_key": IDEMPOTENCY_KEY,
        "scope_kind": "multi-epic",
        "epics": [{"id": e["id"], "file": f"{e['id']}.json", "title": e["title"],
                   "story_prefix": e["story_prefix"],
                   "story_ids": [s[0] for s in STORIES if epic_of(s[0])["id"] == e["id"]]} for e in EPICS],
        "story_files": [{"id": s[0], "epic_id": epic_of(s[0])["id"], "file": f"{s[0]}.json",
                         "title": s[1], "priority": s[8]} for s in STORIES],
        "flows": [{"id": f["id"], "file": f"{f['id']}.json", "name": f["name"]} for f in FLOWS],
        "rules_file": "RULES.json", "domain_file": "DOMAIN.json",
        "stakeholders": STAKEHOLDERS, "legal_status": "present",
        "governance_gaps": [], "open_questions": OPEN_QUESTIONS, "blocks_elaboration": False,
        "count_check": {"epics": len(EPICS), "stories": len(STORIES), "rules": len(RULES),
                        "entities": len(ENTITIES), "flows": len(FLOWS),
                        "open_questions": len(OPEN_QUESTIONS)},
        "human_report": "breakdown.md",
        "upstream_refs": {"source_artifacts": [SOURCE_DOC], "discovery_audit_id": DISCOVERY_AUDIT},
    }
    write_json(d / "INDEX.json", index)
    write_text(d / "breakdown.md", render_breakdown_md(index))


def render_breakdown_md(index: dict) -> str:
    rules = {r[0]: r for r in RULES}
    c = index["count_check"]
    md = [
        "# Three-amigos review — ShopPilot MVP breakdown",
        "",
        "| Epics | Stories | Rules | Entities | Flows | Tier | State |",
        "|---|---|---|---|---|---|---|",
        f"| {c['epics']} | {c['stories']} | {c['rules']} | {c['entities']} | {c['flows']} | "
        f"{EPICS[0]['inferred_tier']} | `{index['state']}` |",
        "",
        "## Blockers",
        "",
        "None. `legal_status: present` — Legal, DPO and Compliance are named and engaged (gap-closed 14), "
        "so no P1 governance gap blocks elaboration.",
        "",
        "## Epics and why they are epics",
        "",
    ]
    for e in EPICS:
        md += [f"### {e['id']} — {e['title']}", "", f"**Value alone.** {e['business_value']}", "",
               f"**Why this is one epic.** {e['decoupling']['rationale']}", "", "**Folded in:**", ""]
        md += [f"- {m}" for m in e["decoupling"]["merged_from"]]
        md.append("")

    md += ["## Business flows", ""]
    for f in FLOWS:
        md += ["```", f"{f['id']}  (actor: {f['actor']})", f"  trigger: {f['trigger']}"]
        dps = {dp["at_step"]: dp for dp in f.get("decision_points", [])}
        for s in f["steps"]:
            refs = ", ".join(s.get("rule_refs", []))
            md.append(f"  {s['seq']} {s['actor']:<9}{s['action']}" + (f"  [{refs}]" if refs else ""))
            if s["seq"] in dps:
                dp = dps[s["seq"]]
                md.append(f"  ? {dp['question']}  [{', '.join(dp['rule_refs'])}]")
                for b in dp["branches"]:
                    md.append(f"      {b['condition']} -> {b['goes_to']}")
        md.append("  outcomes: " + " | ".join(f"{o['name']} ({o['entity_state']})" for o in f["outcomes"]))
        md += ["```", ""]

    md += ["## Business rules", "", "| Id | Rule | Type |", "|---|---|---|"]
    for rid, stmt, rtype, *_ in RULES:
        md.append(f"| `{rid}` | {stmt} | {rtype} |")
    md += ["", "No open rules — every value in the catalogue is stated by the source with a named approving owner "
               "(gap-closed 19).", "", "## Domain entities and state machines", ""]
    for ent in ENTITIES:
        pii = [f["name"] for f in ent["key_fields"] if f["pii_class"] != "none"]
        md.append(f"**{ent['id']}** — {ent['description']}")
        md.append(f"  - owner: {ent['owner']}; retention: {ent['retention']}")
        if pii:
            md.append(f"  - personal data: {', '.join(pii)}")
        for t in ent.get("transitions", []):
            md.append(f"  - {t['from']} -> {t['to']} on {t['trigger']} [{t.get('guard', 'no guard')}]")
        md.append("")

    md += ["## Story skeletons", ""]
    for e in EPICS:
        md += [f"**{e['id']}**", ""]
        for s in STORIES:
            if epic_of(s[0])["id"] != e["id"]:
                continue
            md.append(f"- `{s[0]}` {s[1]} — {s[8]}, {s[9]} pts — {', '.join(s[6])}")
        md.append("")

    md += ["## Questions for this session", ""]
    for who in ("dev", "tester", "PM"):
        rows = [q for q in OPEN_QUESTIONS if q["for"] == who]
        if not rows:
            continue
        md += [f"**For {who}**", ""]
        for q in rows:
            md.append(f"- `{q['id']}` ({q['severity']}) {q['question']}")
            md.append(f"  - why it matters: {q['why_matters']}")
            md.append(f"  - affects: {', '.join(q['related_story_ids'] + q['related_rule_ids'])}")
        md.append("")

    md += ["## What happens next", "",
           "Verdicts: `agreed` | `split-stories` | `descope` | `needs-rework`.",
           "Only `agreed` releases story elaboration.",
           "Anything else returns this breakdown with the findings attached.",
           "", f"`audit_id` {index['audit_id']}"]
    return "\n".join(md)


# ------------------------------------------------------------------- S1c brief
def emit_brief() -> None:
    d = OUT / "S1c-brief"
    ac_total = 0

    for epic in EPICS:
        stories = [s for s in STORIES if epic_of(s[0])["id"] == epic["id"]]
        ed = d / epic["id"]
        write_json(ed / f"{epic['id']}.json", {
            "id": epic["id"], "title": epic["title"], "story_prefix": epic["story_prefix"],
            "problem_statement": epic["problem_statement"], "business_value": epic["business_value"],
            "why_now": epic["why_now"], "success_criteria": epic["success_criteria"],
            "decoupling": epic["decoupling"], "scope": epic["scope"],
            "stakeholders": [{k: v for k, v in s.items() if k in ("role", "name_or_team", "raci", "status")}
                             for s in STAKEHOLDERS],
            "legal_status": epic["legal_status"], "inferred_tier": epic["inferred_tier"],
            "tier_signals": epic["tier_signals"],
            "rule_refs": rules_for_epic(epic["id"]), "flow_refs": flows_for_epic(epic["id"]),
            "story_refs": [{"id": s[0], "slug": slug(s[1]), "file": f"{s[0]}-{slug(s[1])}.json", "title": s[1]}
                           for s in stories],
        })

        for sid, title, as_a, i_want, so_that, intent, rule_refs, entity_refs, prio, pts, cx, dep, blk in stories:
            acs = [
                {"scenario_name": n, "scenario_type": t, "given": g, "when": w, "then": th,
                 "rule_ref": rr, "derived_from": df}
                for n, t, g, w, th, rr, df in ACCEPTANCE[sid]
            ]
            ac_total += len(acs)
            bgc = {}
            for key in BGC_ORDER:
                status, why, fields, treatment, comp = BANKING_GRADE[sid][key]
                row = {"status": status, "justification": why}
                if fields:
                    row["fields_or_events"] = fields
                if treatment:
                    row["treatment"] = treatment
                if comp:
                    row["compensating_action"] = comp
                bgc[key] = row
            write_json(ed / f"{sid}-{slug(title)}.json", {
                "id": sid, "epic_id": epic["id"], "title": title, "format": "classic_user_story",
                "card": {"as_a": as_a, "i_want": i_want, "so_that": so_that},
                "intent": intent, "rule_refs": rule_refs,
                "flow_refs": [f["id"] for f in FLOWS if sid in f["story_refs"]],
                "entity_refs": entity_refs,
                "acceptance_criteria": acs, "banking_grade_concerns": bgc,
                "edge_case_ledger": [
                    {"rule_ref": rr, "cases_written": written,
                     **({"cases_not_applicable": na} if na else {}),
                     **({"justification": why} if why else {})}
                    for rr, written, na, why in EDGE_LEDGER[sid]
                ],
                "priority": prio,
                "sizing": {"story_points": pts, "complexity": cx, "split_required": pts >= 13},
                "dependencies": {"depends_on": dep, "blocks": blk},
                "dor": "pass",
                "open_questions": [q["id"] for q in OPEN_QUESTIONS if sid in q["related_story_ids"]],
                "requirement_refs": ["shoppilot-mvp"], "scope_ref": "../INDEX.json",
            })

    referenced = sorted({r for s in STORIES for r in s[6]})
    covered = sorted({ac[5] for sid in ACCEPTANCE for ac in ACCEPTANCE[sid]})
    transitions = sum(len(e.get("transitions", [])) for e in ENTITIES)
    illegal = sum(1 for sid in ACCEPTANCE for ac in ACCEPTANCE[sid] if ac[1] == "illegal_transition")

    write_json(d / "INDEX.json", {
        "audit_id": BRIEF_AUDIT, "stage": "ba-research", "state": "ready-for-tl",
        "produced_by": "elaborating-user-stories 1.0.0", "idempotency_key": IDEMPOTENCY_KEY,
        "epics": [{"id": e["id"], "file": f"{e['id']}/{e['id']}.json", "title": e["title"],
                   "story_ids": [s[0] for s in STORIES if epic_of(s[0])["id"] == e["id"]]} for e in EPICS],
        "story_files": [{"id": s[0], "epic_id": epic_of(s[0])["id"],
                         "file": f"{epic_of(s[0])['id']}/{s[0]}-{slug(s[1])}.json",
                         "title": s[1], "slug": slug(s[1]), "priority": s[8]} for s in STORIES],
        "rules_file": "../S1b-breakdown/RULES.json",
        "domain_file": "../S1b-breakdown/DOMAIN.json",
        "flows": [{"id": f["id"], "file": f"../S1b-breakdown/{f['id']}.json", "name": f["name"]} for f in FLOWS],
        "governance_gaps": [],
        "open_questions": OPEN_QUESTIONS,
        "assumptions_made": ASSUMPTIONS,
        "rule_coverage": {
            "rules_total": len(referenced), "rules_covered": len(covered),
            "uncovered_rule_ids": [r for r in referenced if r not in covered],
            "transitions_total": transitions, "illegal_transition_cases": illegal,
            "open_rule_ids": [],
        },
        "hidden_requirements_sweep": HIDDEN_SWEEP,
        "count_check": {"epics": len(EPICS), "stories": len(STORIES),
                        "acceptance_criteria": ac_total, "open_questions": len(OPEN_QUESTIONS)},
        "upstream_refs": {
            "source_artifacts": [SOURCE_DOC],
            "breakdown_audit_id": BREAKDOWN_AUDIT, "discovery_audit_id": DISCOVERY_AUDIT,
            "amigos_approvers": ["Khun Pim (ba-lead)", "Khun Anan (dev-lead)", "Khun Ratree (qa-lead)"],
        },
    })


if __name__ == "__main__":
    emit_discovery()
    emit_breakdown()
    emit_brief()
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in files)
    print(f"wrote {len(files)} files, {lines} lines -> {OUT}")
