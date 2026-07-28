#!/usr/bin/env python3
"""Validate the BA-leg-v2 staging: skills, schemas, sample pack, cuts and depth.

Mirrors tmp/runs/shoppilot/_sim/validate.py in spirit: every emitted artifact is
checked against the schema that owns it, then the cross-file invariants the
schemas cannot express are asserted separately.

    python3 tmp/runs/ba-leg-v2/validate.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PACK = ROOT / "sample-pack"
BD = ROOT / "skills" / "breaking-down-ba-scope"
EL = ROOT / "skills" / "elaborating-user-stories"
CORPUS = REPO / "tmp" / "runs" / "shoppilot" / "S1b-ba-brief"

FAILS: list[str] = []
NOTES: list[str] = []
CHECKS = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(f"{label}{': ' + detail if detail else ''}")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def validator(p: Path) -> Draft7Validator:
    return Draft7Validator(load(p))


def val(v: Draft7Validator, obj, label: str) -> None:
    errs = sorted(v.iter_errors(obj), key=lambda e: list(e.path))
    check(not errs, label, "; ".join(f"{list(e.path)}: {e.message}" for e in errs[:3]))


def lines(paths) -> int:
    return sum(len(p.read_text(encoding="utf-8").splitlines()) for p in paths)


# ---------------------------------------------------------------- 1. skillify
print("1. skillify gates")
for d in (BD, EL):
    for script in ("quick_validate.py", "check_links.py"):
        r = subprocess.run(
            [sys.executable, str(Path.home() / ".claude/skills/skillify/scripts" / script), str(d)],
            capture_output=True, text=True)
        check(r.returncode == 0, f"{script} {d.name}", (r.stdout + r.stderr).strip())
    check(len(( d / "SKILL.md").read_text(encoding="utf-8").splitlines()) <= 500, f"SKILL.md <=500 lines {d.name}")

# ------------------------------------------------------- 2. schemas + examples
print("2. schema syntax and SKILL.md examples")
for d in (BD, EL):
    for s in sorted((d / "schemas").glob("*.json")):
        try:
            Draft7Validator.check_schema(load(s))
        except Exception as exc:  # noqa: BLE001
            check(False, f"schema {d.name}/{s.name}", str(exc))
        else:
            check(True, f"schema {d.name}/{s.name}")
    blocks = re.findall(r"```json\n(.*?)\n```", (d / "SKILL.md").read_text(encoding="utf-8"), re.S)
    check(len(blocks) == 2, f"{d.name} has an input and an output example", f"found {len(blocks)}")
    for blk, name in zip(blocks, ("input.json", "output.json")):
        val(validator(d / "schemas" / name), json.loads(blk), f"{d.name} example vs {name}")

# ------------------------------------------------------- 3. sample pack schemas
print("3. sample pack vs its schemas")
bd_index = load(PACK / "S1b-breakdown" / "INDEX.json")
el_index = load(PACK / "S1c-brief" / "INDEX.json")
val(validator(BD / "schemas" / "output.json"), bd_index, "S1b INDEX")
val(validator(EL / "schemas" / "output.json"), el_index, "S1c INDEX")
val(validator(BD / "schemas" / "rules.json"), load(PACK / "S1b-breakdown" / "RULES.json"), "RULES.json")
val(validator(BD / "schemas" / "domain.json"), load(PACK / "S1b-breakdown" / "DOMAIN.json"), "DOMAIN.json")

v_epic, v_story = validator(BD / "schemas" / "epic.json"), validator(BD / "schemas" / "story-skeleton.json")
for e in bd_index["epics"]:
    val(v_epic, load(PACK / "S1b-breakdown" / e["file"]), f"breakdown {e['id']}")
for s in bd_index["story_files"]:
    val(v_story, load(PACK / "S1b-breakdown" / s["file"]), f"skeleton {s['id']}")
v_flow = validator(BD / "schemas" / "flow.json")
for f in bd_index["flows"]:
    val(v_flow, load(PACK / "S1b-breakdown" / f["file"]), f"flow {f['id']}")

v_esc, v_ssc = validator(EL / "schemas" / "epic-sidecar.json"), validator(EL / "schemas" / "story-sidecar.json")
stories = {}
for e in el_index["epics"]:
    val(v_esc, load(PACK / "S1c-brief" / e["file"]), f"elaborated {e['id']}")
for s in el_index["story_files"]:
    obj = load(PACK / "S1c-brief" / s["file"])
    stories[s["id"]] = obj
    val(v_ssc, obj, f"elaborated {s['id']}")

# ------------------------------------------ 4. backward compatibility (the claim)
print("4. downstream boundary compatibility")
val(Draft7Validator(load(REPO / "workflows/schemas/ba-brief.json")), el_index,
    "S1c INDEX still validates against the LIVE workflows/schemas/ba-brief.json boundary")
for key in ("epics", "story_files", "governance_gaps", "state", "audit_id"):
    check(key in el_index, f"boundary required field present: {key}")

disc = load(PACK / "S1a-ba-discovery" / "discovery.json")
v_disc = Draft7Validator(load(REPO / "workflows/schemas/discovery.json"))
val(v_disc, disc, "S1a discovery vs the LIVE workflows/schemas/discovery.json")
# The boundary now accepts BOTH shapes of problem_framing: the legacy narrative string that
# recorded artifacts carry, and the structured triple that replaced it. Prove both directions,
# so simplifying the report cannot invalidate provenance already on disk.
val(v_disc, load(REPO / "tmp/runs/shoppilot/S1a-ba-discovery/discovery.json"),
    "the RECORDED corpus discovery (string problem_framing) still validates")
check(isinstance(disc["problem_framing"], dict), "new discovery uses the structured problem_framing")
check(all(len(disc["problem_framing"][k]) <= 400 for k in ("problem", "who", "why_now")),
      "each problem_framing part stays under the 400-character report cap")
h = disc["handoff_to_intake"]
check(h["audit_id"] == disc["audit_id"] and h["recommendation"] == "proceed",
      "handoff_to_intake carries its audit_id and proceed recommendation")
check(all(isinstance(x, dict) and "role" in x for x in h["stakeholder_hints"]),
      "stakeholder_hints are typed objects, matching the boundary contract")

# -------------------------------------------------- 5. ref-chain and FM-14 counts
print("5. ref-chain integrity and count consistency")
rules = {r["id"]: r for r in load(PACK / "S1b-breakdown" / "RULES.json")["rules"]}
domain = load(PACK / "S1b-breakdown" / "DOMAIN.json")
entities = {e["id"]: e for e in domain["entities"]}
flows = [load(PACK / "S1b-breakdown" / f["file"]) for f in bd_index["flows"]]
skeletons = {s["id"]: load(PACK / "S1b-breakdown" / s["file"]) for s in bd_index["story_files"]}

cc = bd_index["count_check"]
check(cc["epics"] == len(bd_index["epics"]), "count_check.epics")
check(cc["stories"] == len(bd_index["story_files"]), "count_check.stories")
check(cc["stories"] == sum(len(e["story_ids"]) for e in bd_index["epics"]), "epic story_ids sum == stories")
check(cc["rules"] == len(rules), "count_check.rules")
check(cc["entities"] == len(entities), "count_check.entities")
check(cc["flows"] == len(flows), "count_check.flows")
epic_ids = {e["id"] for e in bd_index["epics"]}
check(all(s["epic_id"] in epic_ids for s in bd_index["story_files"]), "every story resolves to an epic")

for sid, sk in skeletons.items():
    check(all(r in rules for r in sk["rule_refs"]), f"{sid} rule_refs resolve")
    check(all(e in entities for e in sk.get("entity_refs", [])), f"{sid} entity_refs resolve")
    check(all(f in {fl["id"] for fl in flows} for f in sk["flow_refs"]), f"{sid} flow_refs resolve")
    check(len(sk["rule_refs"]) >= 1, f"{sid} references at least one rule")
    check("acceptance_criteria" not in sk, f"{sid} skeleton carries NO acceptance criteria")
    check("banking_grade_concerns" not in sk, f"{sid} skeleton carries NO banking-grade rows")

referenced = {r for sk in skeletons.values() for r in sk["rule_refs"]}
check(referenced == set(rules), "every catalogued rule is referenced by a story",
      f"orphans: {sorted(set(rules) - referenced)}")

for fl in flows:
    for dp in fl.get("decision_points", []):
        check(len(dp["rule_refs"]) >= 1 and all(r in rules for r in dp["rule_refs"]),
              f"{fl['id']} decision point at step {dp['at_step']} cites a resolvable rule")
    all_states = {s for e in entities.values() for s in e.get("states", [])}
    for o in fl["outcomes"]:
        check(o["entity_state"] in all_states, f"{fl['id']} outcome '{o['name']}' lands in a declared state")
    check(sum(1 for o in fl["outcomes"] if o["kind"] != "success") >= 1,
          f"{fl['id']} has at least one non-success outcome")

for eid, ent in entities.items():
    if ent.get("states"):
        check(bool(ent.get("transitions")), f"{eid} declares transitions with its states")
        names = set(ent["states"])
        check(all(t["from"] in names and t["to"] in names for t in ent["transitions"]),
              f"{eid} transitions reference declared states")
    for f in ent["key_fields"]:
        if f["pii_class"] != "none":
            check("lawful_basis" in f and "masking" in f, f"{eid}.{f['name']} personal field carries basis and masking")

# ---------------------------------------------------------- 6. DEPTH assertions
print("6. depth assertions")
BG = ["pii_fields", "audit_events", "idempotency", "reversibility", "authn_authz", "regulatory", "tipping_off"]
ac_total = 0
for sid, st in stories.items():
    acs = st["acceptance_criteria"]
    ac_total += len(acs)
    check(len(acs) >= 3, f"{sid} has at least three acceptance criteria")
    check(any(a["scenario_type"] == "happy" for a in acs), f"{sid} has a happy scenario")
    check(any(a["scenario_type"].startswith("banking_grade") for a in acs), f"{sid} has a banking-grade scenario")
    check(any(a["rule_ref"] in rules for a in acs if "rule_ref" in a), f"{sid} cites at least one catalogued rule in its AC")
    check(all(a["rule_ref"] in rules for a in acs if "rule_ref" in a), f"{sid} every cited rule_ref resolves")
    check(all(k in st["banking_grade_concerns"] for k in BG), f"{sid} carries all seven banking-grade rows")
    check(all(len(st["banking_grade_concerns"][k]["justification"]) >= 10 for k in BG),
          f"{sid} every banking-grade justification is substantive")
    check(st["rule_refs"] == skeletons[sid]["rule_refs"], f"{sid} rule_refs unchanged from the agreed skeleton")
    check(st["intent"] == skeletons[sid]["intent"], f"{sid} intent unchanged from the agreed skeleton")
    check("dor_checklist" not in st and "change_log" not in st, f"{sid} carries no all-true checklist or change log")
    ledger = {row["rule_ref"] for row in st.get("edge_case_ledger", [])}
    check(ledger == set(st["rule_refs"]), f"{sid} edge-case ledger covers every referenced rule")

covered = {a["rule_ref"] for st in stories.values() for a in st["acceptance_criteria"] if "rule_ref" in a}
check(covered == set(rules), "every rule has at least one derived scenario",
      f"uncovered: {sorted(set(rules) - covered)}")

rc = el_index["rule_coverage"]
check(rc["uncovered_rule_ids"] == [] and rc["open_rule_ids"] == [], "rule_coverage is clean for ready-for-tl")
check(rc["rules_covered"] == len(covered), "rule_coverage.rules_covered matches the artifacts")
check(el_index["count_check"]["acceptance_criteria"] == ac_total, "count_check.acceptance_criteria matches")

stateful = {eid for eid, e in entities.items() if e.get("states")}
illegal_entities = {e for sid, st in stories.items() for a in st["acceptance_criteria"]
                    if a["scenario_type"] == "illegal_transition" for e in st.get("entity_refs", [])}
check(stateful <= illegal_entities, "every stateful entity has an illegal-transition scenario",
      f"missing: {sorted(stateful - illegal_entities)}")
check(rc["illegal_transition_cases"] >= len(stateful), "at least one illegal-transition case per stateful entity")

# ------------------------------------------------------------ 7. CUT assertions
print("7. cut assertions")
check(not list(PACK.rglob("*viewer*.html")), "no per-run HTML viewer is emitted")
check(not list(PACK.rglob("*.html")), "the pack emits no HTML at all")
md = list(PACK.rglob("*.md"))
check(len(md) == 2, "exactly two human reports in the whole BA leg", f"found {[p.name for p in md]}")
check(lines([PACK / "S1b-breakdown" / "breakdown.md"]) <= 260, "breakdown.md stays a short agenda")
for banned in ("ba_reasoning_trace", "ba_compliance_checklist", "dor_checklist", "change_log",
               "downstream_will_be_consumed_by", "bilingual_output", "language_inventory"):
    hits = [p.name for p in PACK.rglob("*.json") if banned in p.read_text(encoding="utf-8")]
    check(not hits, f"cut field absent: {banned}", str(hits))

new_lines = lines([p for p in PACK.rglob("*") if p.is_file() and p.parent.name != "S1a-ba-discovery"])
old_lines = lines([p for p in CORPUS.rglob("*") if p.is_file()])
check(new_lines < old_lines, "the new breakdown plus brief is smaller than the brief it replaces",
      f"{new_lines} vs {old_lines}")
NOTES.append(f"artifact size: corpus S1b {old_lines} lines -> new S1b+S1c {new_lines} lines "
             f"({100 * (old_lines - new_lines) // old_lines}% smaller), with the acceptance criteria "
             f"count going 29 -> {ac_total} and rules/entities/flows going 0 -> "
             f"{len(rules)}/{len(entities)}/{len(flows)}.")

# ------------------------------------------- 8. determinism, offline, provenance
print("8. determinism, offline and provenance")
before = {p: p.read_bytes() for p in sorted(PACK.rglob("*")) if p.is_file()}
subprocess.run([sys.executable, str(ROOT / "generate_sample_pack.py")], capture_output=True, check=True)
after = {p: p.read_bytes() for p in sorted(PACK.rglob("*")) if p.is_file()}
check(before == after, "regenerating the pack is byte-identical")

for p in PACK.rglob("*"):
    if p.is_file():
        txt = p.read_text(encoding="utf-8")
        check("https://" not in txt and "http://" not in txt, f"offline: no URL in {p.name}")

import uuid as _uuid
NS = _uuid.uuid5(_uuid.NAMESPACE_URL, "https://squad-delivery/audit")
IDEM = bd_index["idempotency_key"]
check(bd_index["audit_id"] == str(_uuid.uuid5(NS, f"ba-breakdown:{IDEM}")), "breakdown audit_id uses the house formula")
check(el_index["audit_id"] == str(_uuid.uuid5(NS, f"ba-research:{IDEM}")), "brief audit_id uses the house formula")
check(el_index["upstream_refs"]["breakdown_audit_id"] == bd_index["audit_id"], "the brief records the breakdown it came from")
check(el_index["audit_id"] != bd_index["audit_id"], "the two stages carry distinct provenance ids")

# ------------------------------------------------------------------- report
print()
for n in NOTES:
    print(f"NOTE  {n}")
print()
if FAILS:
    print(f"FAIL  {len(FAILS)} of {CHECKS} checks failed")
    for f in FAILS:
        print(f"  - {f}")
    sys.exit(1)
print(f"PASS  {CHECKS}/{CHECKS} checks")
