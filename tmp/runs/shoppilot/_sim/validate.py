#!/usr/bin/env python3
"""validate.py — validate every ShopPilot run artifact against BOTH its built
skill output schema AND its boundary schema (workflows/schemas/*.json).
Exit 0 only if all pass. Run from the workspace root."""
import json, os, sys
from jsonschema.validators import validator_for
from jsonschema import FormatChecker

ROOT = os.getcwd()
RUN = "tmp/runs/shoppilot"
SK = "workflows/skills/%s/schemas/output.json"
BD = "workflows/schemas/%s.json"

# artifact -> (skill_schema_or_None, boundary_schema)
CHECKS = [
    # downstream stages produced by the simulation
    (f"{RUN}/S0-intake/run-plan.json", SK % "scoping-ba-intake", BD % "run-plan"),
    (f"{RUN}/S1.5-ux-intake/output.json", SK % "generate-ux-pack", BD % "ux-intake"),
    (f"{RUN}/S3-contracts/befe-contracts.json", SK % "befe-contract-design", BD % "befe-contracts"),
    (f"{RUN}/S4a-backend/backend-artifacts.json", SK % "implement-backend-feature", BD % "backend-artifacts"),
    (f"{RUN}/S4a-backend/review/backend-review.json", SK % "review-backend-code", BD % "backend-review"),
    (f"{RUN}/S4b-frontend/frontend-artifacts.json", SK % "implement-frontend-feature", BD % "frontend-artifacts"),
    (f"{RUN}/S4b-frontend/review/frontend-review.json", SK % "review-frontend-code", BD % "frontend-review"),
    (f"{RUN}/S4c-qa-test-design/qa-plan.json", SK % "planning-banking-tests", BD % "qa-plan"),
    (f"{RUN}/S5-qa-validation/qa-evidence.json", SK % "executing-qa-test-suite", BD % "qa-evidence"),
    (f"{RUN}/S6-deploy/handoff-receipt.json", SK % "handoff-to-deploy", BD % "handoff-receipt"),
    # SAGA compensation fixture (deterministic; the happy-path run never exercises revoke,
    # so the revoke contract needs its own oracle entry — fleet adjudication F8)
    (f"{RUN}/S6-deploy/revoke-receipt.fixture.json", SK % "handoff-revoke", BD % "revoke-receipt"),
    (f"{RUN}/S7-prod-validation/smoke-slo.json", SK % "validating-production-slo", BD % "smoke-slo"),
    # pre-existing real upstream artifacts (regression guard)
    (f"{RUN}/S1a-ba-discovery/discovery.json", SK % "researching-ba-problem-space", BD % "discovery"),
    (f"{RUN}/S1b-ba-brief/INDEX.json", None, BD % "ba-brief"),
    (f"{RUN}/S2-tl-design/output.json", SK % "designing-tech-lead-handoff", BD % "tl-design"),
    (f"{RUN}/S2.5-plan-review/plan-review.json", SK % "red-teaming-implementation-plan", BD % "plan-review"),
]

GATE_SKILL = {
    "backend-unit-tests": "executing-backend-unit-tests", "frontend-unit-tests": "executing-frontend-unit-tests",
    "sast-gate": "running-sast-security-gate", "accessibility-tests": "running-accessibility-tests",
    "contract-tests": "contract-testing-pact", "integration-tests": "executing-integration-tests",
    "appsec-scan": "scanning-appsec-pipeline-gate", "e2e-tests": "authoring-e2e-test-suite",
    "perf-load-test": "running-performance-load-test", "adversarial-pentest": "validating-banking-implementation",
    "smoke-tests": "running-smoke-tests", "canary-analysis": "analyzing-canary-rollout",
}
for g, skill in GATE_SKILL.items():
    CHECKS.append((f"{RUN}/gates/{g}.json", SK % skill, BD % g))


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def errs(instance, schema_path):
    if schema_path is None or not os.path.exists(schema_path):
        return None  # not applicable
    schema = load(schema_path)
    cls = validator_for(schema)
    v = cls(schema, format_checker=FormatChecker())
    out = []
    for e in sorted(v.iter_errors(instance), key=lambda e: list(e.path)):
        loc = "/".join(str(x) for x in e.path) or "<root>"
        out.append("    [%s] %s" % (loc, e.message))
    return out


fails = 0
for art, sk, bd in CHECKS:
    if not os.path.exists(art):
        print("MISSING  %s" % art); fails += 1; continue
    inst = load(art)
    line = []
    for label, sp in (("skill", sk), ("bound", bd)):
        e = errs(inst, sp)
        if e is None:
            line.append("%s:n/a" % label)
        elif e:
            line.append("%s:FAIL" % label); fails += 1
            print("FAIL %s  (%s schema=%s)" % (art, label, sp))
            for m in e[:6]:
                print(m)
        else:
            line.append("%s:ok" % label)
    print("%-7s %-52s %s" % ("PASS" if all("FAIL" not in x for x in line) else "----", art.replace(RUN + "/", ""), " ".join(line)))

print("\n%s — %d failure(s)" % ("ALL PASS" if fails == 0 else "HAS FAILURES", fails))
sys.exit(1 if fails else 0)
