#!/usr/bin/env python3
"""Deterministic renderer: canonical output.json -> markdown tree.

Reads a validated planning-banking-tests output.json and emits the test-plan
directory tree per references/markdown-rendering-spec.md.

Determinism rules:
- JSON keys sorted before serialization.
- Iteration over epics/stories/test_cases/nfr_tests/compliance_tests by sorted id.
- No system clock reads at render time.
- No LLM calls.
- No random/uuid generation; all IDs come from input output.json.

CLI:
    python3 render_test_plan_tree.py --input output.json --output-dir test-plan-{idem8}/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SUCCESS_TOP_DOCS = [
    ("README.md", "render_readme"),
    ("00-STRATEGY.md", "render_strategy"),
    ("01-environments.md", "render_environments"),
    ("02-test-data.md", "render_test_data"),
    ("03-coverage-matrix.md", "render_coverage_matrix"),
    ("04-nfr-tests.md", "render_nfr_tests"),
    ("05-compliance-tests.md", "render_compliance_tests"),
    ("06-execution-order.md", "render_execution_order"),
    ("07-signoff-criteria.md", "render_signoff_criteria"),
    ("08-coverage-gaps.md", "render_coverage_gaps"),
    ("09-tl-design-dependencies.md", "render_tl_design_deps"),
    ("10-audit-trace.md", "render_audit_trace"),
]


def fail(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def canonical_json(data: Any) -> str:
    """Sort keys, stable formatting. Trailing newline for POSIX text files."""
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def slugify(text: str, max_len: int = 60) -> str:
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_/":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    return slug[:max_len]


def fm(pairs: dict[str, Any]) -> str:
    """Emit YAML frontmatter from a dict (sorted keys)."""
    lines = ["---"]
    for k in sorted(pairs.keys()):
        v = pairs[k]
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
            else:
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# --- Section renderers ---


def render_readme(data: dict) -> str:
    fmd = data["frontmatter"]
    blocks = data.get("blocks_qa_execution", False)
    status = fmd.get("status", "draft")
    banner = (
        "**Status**: Ready for QA execution" if status == "ready-for-execution"
        else f"**Status**: {status.upper()}"
    )
    body = [
        fm({
            "artifact_type": "qa-test-plan-readme",
            "test_plan_id": fmd["test_plan_id"],
            "brief_id": fmd["brief_id"],
            "brief_idempotency_key": fmd["brief_idempotency_key"],
            "workload_tier": fmd["workload_tier"],
            "status": status,
            "blocks_qa_execution": blocks,
        }),
        f"# Test Plan — {fmd['test_plan_id']}\n",
        f"{banner}\n",
        "## At a glance\n",
        f"- Epics: {len(data.get('epics', []))}",
        f"- Stories: {len(data.get('stories', []))}",
        f"- Test cases: {len(data.get('test_cases', []))}",
        f"- NFR tests: {len(data.get('nfr_tests', []))}",
        f"- Compliance tests: {len(data.get('compliance_tests', []))}",
        f"- Coverage gaps: {len(data.get('coverage_gaps', []))}",
        "",
        "## Navigation\n",
    ]
    for fname, _ in SUCCESS_TOP_DOCS[1:]:
        body.append(f"- [{fname}]({fname})")
    body.append("- [epics/](epics/)")
    return "\n".join(body) + "\n"


def render_strategy(data: dict) -> str:
    s = data.get("strategy", {})
    body = [
        fm({"artifact_type": "qa-strategy", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Test Strategy\n",
        "## Pyramid Allocation\n",
        canonical_json(s.get("test_pyramid_allocation", {})),
        "\n## Tier Rationale\n",
        s.get("tier_rationale", "_(not set)_"),
        "\n\n## Mock vs Real Strategy\n",
        s.get("mock_vs_real_strategy", "_(not set)_"),
        "\n\n## High Risk Areas\n",
    ]
    for area in s.get("high_risk_areas", []):
        body.append(f"- {area}")
    return "\n".join(body) + "\n"


def render_environments(data: dict) -> str:
    envs = sorted(data.get("environments", []), key=lambda e: e.get("id", ""))
    body = [
        fm({"artifact_type": "qa-environments", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Environments\n",
    ]
    for env in envs:
        body.append(f"## {env['id']}\n")
        body.append(f"- Purpose: {env.get('purpose', '')}")
        body.append(f"- Required mocks: {', '.join(env.get('required_mocks', [])) or '_(none)_'}")
        body.append(f"- Real services: {', '.join(env.get('real_services', [])) or '_(none)_'}")
        body.append("")
    return "\n".join(body) + "\n"


def render_test_data(data: dict) -> str:
    specs = sorted(data.get("test_data_specs", []), key=lambda s: s.get("fixture_set_id", ""))
    body = [
        fm({"artifact_type": "qa-test-data", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Test Data Design\n",
    ]
    for spec in specs:
        body.append(f"## {spec['fixture_set_id']}\n")
        body.append(f"- PII field refs: {', '.join(spec.get('pii_field_refs', [])) or '_(none)_'}")
        body.append(f"- Synthesis rules: {spec.get('synthesis_rules', '')}")
        anchors = spec.get("time_anchors", [])
        if anchors:
            body.append(f"- Time anchors: {', '.join(anchors)}")
        body.append("")
    return "\n".join(body) + "\n"


def render_coverage_matrix(data: dict) -> str:
    cm = data.get("coverage_matrix", {})
    body = [
        fm({"artifact_type": "qa-coverage-matrix", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Coverage Matrix\n",
    ]
    for view in ("by_story", "by_scenario_type", "by_pyramid_level", "by_tier"):
        body.append(f"## {view}\n")
        body.append("```json")
        body.append(canonical_json(cm.get(view, {})).rstrip())
        body.append("```\n")
    return "\n".join(body) + "\n"


def render_nfr_tests(data: dict) -> str:
    tests = sorted(data.get("nfr_tests", []), key=lambda t: t.get("id", ""))
    body = [
        fm({"artifact_type": "qa-nfr-tests", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# NFR Tests\n",
    ]
    by_type: dict[str, list[dict]] = {}
    for t in tests:
        by_type.setdefault(t.get("nfr_type", "uncategorized"), []).append(t)
    for nfr_type in sorted(by_type.keys()):
        body.append(f"## {nfr_type}\n")
        for t in by_type[nfr_type]:
            body.append(f"### {t['id']} — {t.get('metric', '')}")
            body.append(f"- Epic: {t.get('epic_id', '')}")
            body.append(f"- Target: {t.get('target', '')}")
            if t.get("blocking_oqs"):
                body.append(f"- Blocking OQs: {', '.join(t['blocking_oqs'])}")
            body.append("")
    return "\n".join(body) + "\n"


def render_compliance_tests(data: dict) -> str:
    tests = sorted(data.get("compliance_tests", []), key=lambda t: t.get("id", ""))
    body = [
        fm({"artifact_type": "qa-compliance-tests", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Compliance Tests\n",
    ]
    by_reg: dict[str, list[dict]] = {}
    for t in tests:
        by_reg.setdefault(t.get("regulator_code", "uncategorized"), []).append(t)
    for code in sorted(by_reg.keys()):
        body.append(f"## {code}\n")
        for t in by_reg[code]:
            body.append(f"### {t['id']} — {t.get('test_type', '')}")
            body.append(f"- Scope: {t.get('scope', '')}")
            if t.get("compliance_scope_blocked"):
                body.append(f"- Scope blocked: true")
            if t.get("blocking_governance_gaps"):
                body.append(f"- Blocking governance gaps: {', '.join(t['blocking_governance_gaps'])}")
            body.append("")
    return "\n".join(body) + "\n"


def render_execution_order(data: dict) -> str:
    dag = data.get("execution_dag", {})
    nodes = sorted(dag.get("nodes", []), key=lambda n: n.get("id", ""))
    edges = sorted(dag.get("edges", []), key=lambda e: (e.get("from", ""), e.get("to", "")))
    body = [
        fm({"artifact_type": "qa-execution-order", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Execution Order\n",
        "## Nodes\n",
    ]
    for n in nodes:
        body.append(f"- {n['id']} → {n.get('test_case_ref', '')}")
    body.append("\n## Edges\n")
    for e in edges:
        kind = f" ({e['kind']})" if e.get("kind") else ""
        body.append(f"- {e['from']} → {e['to']}{kind}")
    return "\n".join(body) + "\n"


def render_signoff_criteria(data: dict) -> str:
    sc = data.get("signoff_criteria", {})
    body = [
        fm({"artifact_type": "qa-signoff-criteria", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Sign-off Criteria\n",
        f"## Tier: {sc.get('tier', '')}\n",
        "## Go Conditions\n",
    ]
    for c in sc.get("go_conditions", []):
        body.append(f"- {c}")
    body.append("\n## Conditional-Go Conditions\n")
    for c in sc.get("conditional_go_conditions", []):
        body.append(f"- {c}")
    body.append("\n## No-Go Conditions\n")
    for c in sc.get("no_go_conditions", []):
        body.append(f"- {c}")
    return "\n".join(body) + "\n"


def render_coverage_gaps(data: dict) -> str:
    gaps = sorted(data.get("coverage_gaps", []), key=lambda g: (g.get("severity", ""), g.get("type", ""), g.get("story_id", "")))
    body = [
        fm({"artifact_type": "qa-coverage-gaps", "test_plan_id": data["frontmatter"]["test_plan_id"], "gap_count": len(gaps)}),
        "# Coverage Gaps\n",
    ]
    for g in gaps:
        body.append(f"## [{g['severity']}] {g['type']}")
        if g.get("story_id"):
            body.append(f"- Story: {g['story_id']}")
        body.append(f"- Description: {g['description']}")
        body.append(f"- Required action: {g['required_action']}")
        body.append(f"- Escalate to: {g['escalation_target']}")
        body.append("")
    return "\n".join(body) + "\n"


def render_tl_design_deps(data: dict) -> str:
    deps = sorted(data.get("tl_design_dependencies", []), key=lambda d: d.get("type", ""))
    body = [
        fm({"artifact_type": "qa-tl-design-dependencies", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# TL Design Dependencies\n",
    ]
    if not deps:
        body.append("_(none — TL Design either consumed or not required by this plan)_")
    for d in deps:
        body.append(f"## {d['type']}")
        body.append(f"- Description: {d['description']}")
        body.append(f"- Needed by: {', '.join(sorted(d.get('needed_by_test_cases', [])))}")
        body.append("")
    return "\n".join(body) + "\n"


def render_audit_trace(data: dict) -> str:
    pm = data.get("processing_metadata", {})
    chk = data.get("qa_readiness_checklist", {})
    body = [
        fm({"artifact_type": "qa-audit-trace", "test_plan_id": data["frontmatter"]["test_plan_id"]}),
        "# Audit Trace\n",
        "## Processing Metadata\n",
        "```json",
        canonical_json(pm).rstrip(),
        "```\n",
        "## QA Readiness Checklist\n",
    ]
    for k in sorted(chk.keys()):
        body.append(f"- {k}: {chk[k]}")
    return "\n".join(body) + "\n"


def render_epic_test_plan(epic: dict, stories: list[dict], data: dict) -> str:
    body = [
        fm({
            "artifact_type": "qa-epic-test-plan",
            "epic_id": epic["epic_id"],
            "test_tier": epic["test_tier"],
            "story_count": len(stories),
            "test_plan_id": data["frontmatter"]["test_plan_id"],
        }),
        f"# Epic Test Plan — {epic['epic_id']}\n",
        f"- Tier: {epic['test_tier']}",
        f"- Stories: {len(stories)}",
        "",
        "## Critical Paths\n",
    ]
    for cp in epic.get("critical_paths", []):
        body.append(f"- {cp}")
    body.append("\n## Stakeholder Owners\n")
    for so in epic.get("stakeholder_owners", []):
        body.append(f"- {so}")
    body.append("\n## Stories\n")
    for s in sorted(stories, key=lambda x: x["story_id"]):
        body.append(f"- {s['story_id']} — coverage: {s.get('coverage_status', '')}, tests: {len(s.get('test_case_ids', []))}")
    return "\n".join(body) + "\n"


def render_story_test_plan(story: dict, story_test_cases: list[dict], data: dict) -> str:
    body = [
        fm({
            "artifact_type": "qa-story-plan",
            "story_id": story["story_id"],
            "epic_id": story["epic_id"],
            "test_case_count": len(story_test_cases),
            "coverage_status": story.get("coverage_status", ""),
            "blocking_oqs": story.get("blocking_oqs", []),
            "test_plan_id": data["frontmatter"]["test_plan_id"],
        }),
        f"# Story Test Plan — {story['story_id']}\n",
        "## Test Case Roster\n",
        "| ID | Scenario | Type | Pyramid | Owner | Risk |",
        "|---|---|---|---|---|---|",
    ]
    for tc in sorted(story_test_cases, key=lambda t: t["id"]):
        body.append(
            f"| {tc['id']} | {tc['scenario_ref']} | {tc['test_type']} | {tc['pyramid_level']} | {tc['owner']} | {tc['risk_level']} |"
        )
    body.append("\n## Test Case Details\n")
    for tc in sorted(story_test_cases, key=lambda t: t["id"]):
        body.append(f"### {tc['id']} — {tc['scenario_ref']}\n")
        body.append(f"- Scenario type: {tc['scenario_type']}")
        body.append(f"- Test type: {tc['test_type']}")
        body.append(f"- Pyramid level: {tc['pyramid_level']}")
        body.append(f"- Environment: {tc['environment_ref']}")
        body.append(f"- Owner: {tc['owner']}")
        body.append(f"- Reviewer role: {tc['reviewer_role']}")
        body.append(f"- Risk: {tc['risk_level']}")
        body.append(f"- Smoke subset: {tc['smoke_subset_member']}")
        if tc.get("tags"):
            body.append(f"- Tags: {', '.join(sorted(tc['tags']))}")
        if tc.get("compliance_tags"):
            body.append(f"- Compliance tags: {', '.join(sorted(tc['compliance_tags']))}")
        if tc.get("depends_on_test_cases"):
            body.append(f"- Depends on: {', '.join(sorted(tc['depends_on_test_cases']))}")
        if tc.get("quarantine_policy"):
            qp = tc["quarantine_policy"]
            body.append(f"- Quarantined until {qp['quarantine_until_date']}: {qp['reason']}")
        body.append("\n#### Expected Assertions")
        for a in tc.get("expected_assertions", []):
            body.append(f"- [{a['type']}] {a['description']}")
        body.append("")
    return "\n".join(body) + "\n"


def render_failure_tree(data: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "output.json").write_text(canonical_json(data), encoding="utf-8")
    fmd = data["frontmatter"]
    fs = data.get("failure_state", {})
    readme = "\n".join([
        fm({
            "artifact_type": "qa-test-plan-readme",
            "test_plan_id": fmd["test_plan_id"],
            "brief_id": fmd.get("brief_id", ""),
            "workload_tier": fmd.get("workload_tier", ""),
            "status": "blocked",
            "blocks_qa_execution": True,
        }),
        "# Test Plan — FAILURE\n",
        f"**Failure code**: {fs.get('failure_code', 'unknown')}\n",
        "See [FAILURE.md](FAILURE.md) for details.\n",
    ])
    (out_dir / "README.md").write_text(readme + "\n", encoding="utf-8")
    failure = "\n".join([
        f"# Failure — {fs.get('failure_code', 'unknown')}\n",
        f"## Message\n\n{fs.get('message', '')}\n",
        f"## Remediation\n\n{fs.get('remediation', '')}\n",
        f"## Blocking Evidence\n",
        *[f"- {e}" for e in fs.get("blocking_evidence", [])],
        "",
        f"## Validation Errors\n",
        *[f"- {e}" for e in fs.get("validation_errors", [])],
    ])
    (out_dir / "FAILURE.md").write_text(failure + "\n", encoding="utf-8")


def render_success_tree(data: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "output.json").write_text(canonical_json(data), encoding="utf-8")
    renderers = {
        "render_readme": render_readme,
        "render_strategy": render_strategy,
        "render_environments": render_environments,
        "render_test_data": render_test_data,
        "render_coverage_matrix": render_coverage_matrix,
        "render_nfr_tests": render_nfr_tests,
        "render_compliance_tests": render_compliance_tests,
        "render_execution_order": render_execution_order,
        "render_signoff_criteria": render_signoff_criteria,
        "render_coverage_gaps": render_coverage_gaps,
        "render_tl_design_deps": render_tl_design_deps,
        "render_audit_trace": render_audit_trace,
    }
    for fname, rname in SUCCESS_TOP_DOCS:
        (out_dir / fname).write_text(renderers[rname](data), encoding="utf-8")

    epics_dir = out_dir / "epics"
    epics_dir.mkdir(exist_ok=True)
    epic_index = {e["epic_id"]: e for e in data.get("epics", [])}
    stories_by_epic: dict[str, list[dict]] = {}
    for s in data.get("stories", []):
        stories_by_epic.setdefault(s["epic_id"], []).append(s)
    tcs_by_story: dict[str, list[dict]] = {}
    for tc in data.get("test_cases", []):
        tcs_by_story.setdefault(tc["story_id"], []).append(tc)

    for epic_id in sorted(epic_index.keys()):
        epic = epic_index[epic_id]
        edir = epics_dir / epic_id
        edir.mkdir(exist_ok=True)
        stories = stories_by_epic.get(epic_id, [])
        (edir / "EPIC-test-plan.md").write_text(
            render_epic_test_plan(epic, stories, data), encoding="utf-8"
        )
        sdir = edir / "stories"
        sdir.mkdir(exist_ok=True)
        for story in sorted(stories, key=lambda x: x["story_id"]):
            slug = slugify(story["story_id"])
            (sdir / f"{slug}-test-plan.md").write_text(
                render_story_test_plan(story, tcs_by_story.get(story["story_id"], []), data),
                encoding="utf-8",
            )


def main() -> int:
    p = argparse.ArgumentParser(description="Render planning-banking-tests output.json into a markdown tree.")
    p.add_argument("--input", required=True, help="Path to canonical output.json")
    p.add_argument("--output-dir", required=True, help="Directory to render the tree into")
    args = p.parse_args()

    src = Path(args.input)
    if not src.is_file():
        fail(f"input not found: {src}")
    out_dir = Path(args.output_dir)

    data = json.loads(src.read_text(encoding="utf-8"))
    output_type = data.get("output_type", "")
    if output_type == "failure_shape":
        render_failure_tree(data, out_dir)
    elif output_type in ("test_plan", "blocked_test_plan", "partial_test_plan"):
        render_success_tree(data, out_dir)
    else:
        fail(f"unknown output_type: {output_type!r}")

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
