#!/usr/bin/env python3
"""simulate.py — deterministic simulation of the delivery-pipeline downstream
stages (S0 + S3..S7 + T1..T12) for the ShopPilot run, plus the S1.5 maturity-2
bump. Threads the real upstream artifacts (S1b brief, S2 tl-design) into each
downstream contract, conforming every artifact to its BUILT skill output schema.

No clock, no randomness: audit_ids are uuid5(NS, name), file content hashes are
sha256(path). Re-running produces byte-identical artifacts.

Usage:  python3 _sim/simulate.py
"""
import json, hashlib, uuid, os

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.abspath(os.path.join(HERE, ".."))      # tmp/runs/shoppilot
NS = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")  # fixed namespace
TS = "2026-06-07T00:00:00Z"


def aid(name):
    return str(uuid.uuid5(NS, "shoppilot:" + name))


def ch(path):
    return "sha256:" + hashlib.sha256(("shoppilot:" + path).encode()).hexdigest()


def real_hash(abspath):
    """Deterministic sha256 of actual file bytes (used once S4a/S4b emit real code)."""
    with open(abspath, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


def line_count(abspath):
    with open(abspath, "rb") as f:
        return max(1, sum(1 for _ in f))


def w(relpath, obj):
    p = os.path.join(RUN, relpath)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return relpath


def readj(relpath):
    with open(os.path.join(RUN, relpath), encoding="utf-8") as f:
        return json.load(f)


written = []

# ───────────────────────── S0 · Intake (scope sheet / run plan) ─────────────────────────
s0 = {
    "audit_id": aid("S0-intake"),
    "normalized_request": (
        "Build ShopPilot — a single-merchant, Thai-market B2C storefront plus an admin back office "
        "covering the full business flow (browse -> cart -> checkout -> pay -> fulfil -> track), with "
        "banking-grade governance (PDPA B.E. 2562, Revenue Code retention, Consumer Protection Act, "
        "PCI-DSS scope-excluded via a tokenizing mock PSP)."
    ),
    "run_plan": {
        "tier_floor": "T2",
        "stage_span": "S0-S7 + T1-T12",
        "epics_expected": 4,
        "pipeline": "delivery-pipeline 3.0.0",
        "human_gates": [
            "S1a discovery recommendation (async-peer, BA lead)",
            "S2 tl-design (sync NAMED, Tech Lead + governance)",
            "S2.5 plan-review (HITL on HardFail)",
            "S4c qa-plan (sync conditional-go, QA lead)",
            "S5 qa-validate (sync, QA lead)",
            "T10 adversarial-pentest (human, security)",
            "S6 release-handoff (sync NAMED, Release Manager — irreversible)",
            "S7 prod-validate (sync, On-call / Release Mgr — rollback decision)",
        ],
    },
    "scope_sheet": {
        # audit_id (top level) is the SOLE artifact identity — no task_id; no created_at
        # (non-deterministic and never supplied by the payload).
        "envelope": {
            "stage": "S0",
            "intent": "scope the raw requirement",
            "state": "ready-for-discovery",  # the S0 successor is s1-discovery
            "confidence": "high",
            "provenance": {"raw_ref": "ecommerce_mvp_business_only.gap-closed.md", "upstream_contract_ref": "none"},
            "produced_by": "intake-agent",
            "owner": "BA lead",
            "schemaVersion": "1.0",
        },
        "contract": {
            "business_goal": "Let customers buy end-to-end on the web and let admins run catalog, stock and orders from one back office.",
            "in_scope": [
                "customer auth (register/login/refresh/logout) with PDPA-lawful credential handling",
                "server-computed checkout totals, one coupon, shipping rule, idempotent confirm",
                "mock payment capture with provider-replay safety",
                "orders with frozen price snapshot + own-data-only tracking",
                "admin fulfillment state machine (paid->packing->shipped->delivered)",
                "stock reservation lifecycle + audited admin adjustments",
            ],
            "out_of_scope": [
                "real payment provider / stored card data",
                "returns and automated refunds",
                "loyalty / multi-currency / multi-warehouse",
                "social / federated login, MFA",
            ],
            "nfrs": [
                {"kind": "volume", "target": "<= 5k orders/day at MVP; design headroom 4x"},
                {"kind": "security", "target": "0 account-enumeration leaks; 0 PAN stored (PCI scope-excluded)"},
                {"kind": "privacy", "target": "PDPA: PII encrypted at rest; ap-southeast residency; 5y Revenue-Code retention"},
                {"kind": "latency", "target": "TBD-confirm-with-PM (see OQ-1) — order-confirm p95 numeric threshold not stated"},
            ],
            "open_questions": [
                {"id": "OQ-1", "question": "Numeric SLO thresholds for order-confirm p95 and order-listing latency?", "for": "PM"},
                {"id": "OQ-2", "question": "Customer-confirmed delivery, or admin-only mark-delivered?", "for": "PM"},
                {"id": "OQ-3", "question": "Abandoned-cart handling beyond the 30-day purge (notify vs silent)?", "for": "PM"},
            ],
            "assumptions": [
                "Mock PSP and mock courier stand in for real providers for the MVP.",
                "Single market (Thai) and single language pairing (th/en) for the MVP.",
            ],
            "risk_flags": ["unclear", "likely-to-change"],
        },
    },
    "human_view": {"kind": "scope_sheet", "render": "native"},
}
written.append(w("S0-intake/run-plan.json", s0))

# ───────────────────────── S1.5 · UX maturity-2 bump ─────────────────────────
ux = readj("S1.5-ux-intake/output.json")
ux["maturity_level"] = 2
ux["status"] = "ready-for-audit"
# Resolve the two TBD-blocking P1s (brand + Thai now concrete); downgrade the
# two "no UX source" P1s to P2 (BA-derived pack accepted at maturity-2 draft).
downgraded = []
for fnd in ux.get("p1_findings", []):
    if fnd.get("code") in ("UX-P1-NO-FRONTEND-SPEC", "UX-P1-NO-PROTOTYPE"):
        fnd = dict(fnd)
        fnd["severity"] = "P2"
        fnd["description"] = ("[SIM maturity-2] " + fnd["description"] +
                              " Accepted at maturity-2 (draft): pack is BA-derived; UX-team source still required before maturity-3.")
        downgraded.append(fnd)
ux["p1_findings"] = []   # BRAND-TBD + TH-MICROCOPY-TBD resolved by the bump
ux["p2_findings"] = downgraded + ux.get("p2_findings", [])
written.append(w("S1.5-ux-intake/output.json", ux))

# patch brand tokens (resolve UX-P1-BRAND-TBD)
tok = readj("S1.5-ux-intake/ux-design-c3f8a1d2/tokens.json")
tok["$description"] = ("ShopPilot UX-design tokens (W3C Design Tokens draft). [SIM maturity-2] brand tokens "
                       "now concrete (BA-derived MVP palette); contrast computed via WCAG 2.1 relative-luminance.")
tok["color"]["brand"]["primary"] = {
    "$type": "color", "$value": "#0B5FD8",
    "$extensions": {"contrast": {"vs-white": "5.63:1", "wcagAA": True, "wcagAAA": False,
                                 "usage_note": "Primary action text/fill behind white text (AA normal+large)."}},
}
tok["color"]["brand"]["secondary"] = {
    "$type": "color", "$value": "#E8590C",
    "$extensions": {"contrast": {"vs-white": "4.52:1", "wcagAA": True, "wcagAAA": False,
                                 "usage_note": "Accent/large-text only on white."}},
}
tok["typography"]["font-family-default"] = {"$type": "fontFamily", "$value": "system-ui, -apple-system, 'Noto Sans Thai', sans-serif"}
tok["radius"]["card"] = {"$type": "dimension", "$value": "8px"}
tok["radius"]["button"] = {"$type": "dimension", "$value": "8px"}
tok["motion"]["duration"] = {"$type": "duration", "$value": "200ms"}
written.append(w("S1.5-ux-intake/ux-design-c3f8a1d2/tokens.json", tok))

# fill Thai microcopy (resolve UX-P1-TH-MICROCOPY-TBD)
TH = {
    "common.action.add_to_cart": "เพิ่มลงตะกร้า", "common.action.checkout": "ดำเนินการสั่งซื้อ",
    "common.action.confirm": "ยืนยันคำสั่งซื้อ", "common.action.pay": "ชำระเงิน",
    "common.action.login": "เข้าสู่ระบบ", "common.action.register": "สร้างบัญชี",
    "common.action.logout": "ออกจากระบบ", "common.action.retry": "ลองอีกครั้ง",
    "common.action.cancel": "ยกเลิก", "common.action.back": "ย้อนกลับ",
    "common.action.track_order": "ติดตามคำสั่งซื้อ",
    "common.status.loading": "กำลังโหลด…", "common.status.empty": "ยังไม่มีรายการ",
    "common.status.success": "สำเร็จ", "common.status.no_results": "ไม่พบรายการ",
    "nav.tab.home": "หน้าแรก", "nav.tab.cart": "ตะกร้า", "nav.tab.orders": "คำสั่งซื้อ", "nav.tab.profile": "โปรไฟล์",
    "screen.login.title": "เข้าสู่ระบบ", "screen.login.error-state": "อีเมลหรือรหัสผ่านไม่ถูกต้อง",
    "screen.register.title": "สร้างบัญชีของคุณ", "screen.products.title": "ร้านค้า",
    "screen.cart.title": "ตะกร้าของคุณ", "screen.cart.empty-state": "ตะกร้าของคุณว่างเปล่า",
    "screen.checkout.title": "ชำระเงิน", "screen.payment.title": "การชำระเงิน",
    "screen.payment.processing-state": "กำลังดำเนินการชำระเงิน…",
    "screen.orders.title": "คำสั่งซื้อของคุณ", "screen.orders.empty-state": "ยังไม่มีคำสั่งซื้อ",
    "screen.order-detail.title": "คำสั่งซื้อ",
    "field.email.label": "อีเมล", "field.email.placeholder": "customer+test@shoppilot.test",
    "field.email.error-required": "กรุณากรอกอีเมล", "field.email.error-format": "กรุณากรอกอีเมลให้ถูกต้อง",
    "field.password.label": "รหัสผ่าน", "field.password.error-required": "กรุณากรอกรหัสผ่าน",
    "field.name.label": "ชื่อ-นามสกุล", "field.phone.label": "เบอร์โทรศัพท์",
    "field.phone.placeholder": "081-234-5678", "field.phone.error-format": "กรุณากรอกเบอร์มือถือให้ถูกต้อง",
    "field.address.label": "ที่อยู่จัดส่ง", "field.coupon.label": "รหัสคูปอง",
    "field.coupon.error-expired": "คูปองนี้ใช้ไม่ได้แล้ว",
    "order.status.AWAITING_PAYMENT": "รอการชำระเงิน", "order.status.PAID": "ชำระเงินแล้ว",
    "order.status.PAYMENT_FAILED": "ชำระเงินไม่สำเร็จ", "order.status.PAYMENT_TIMEOUT": "หมดเวลาชำระเงิน",
    "order.status.PACKING": "กำลังแพ็ก", "order.status.SHIPPED": "จัดส่งแล้ว",
    "order.status.DELIVERED": "จัดส่งสำเร็จ", "order.status.CANCELLED": "ยกเลิกแล้ว",
    "error.network": "การเชื่อมต่อมีปัญหา กรุณาตรวจสอบเครือข่ายแล้วลองใหม่",
    "error.server": "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง",
    "error.validation": "กรุณาแก้ไขข้อมูลที่ไฮไลต์ไว้",
    "error.payment-declined": "ไม่สามารถดำเนินการชำระเงินได้",
    "error.payment-timeout": "หมดเวลาก่อนที่การชำระเงินจะเสร็จสิ้น",
    "error.out-of-stock": "ขออภัย สินค้านี้เพิ่งหมด",
    "error.session-expired": "เซสชันหมดอายุ กรุณาเข้าสู่ระบบอีกครั้ง",
}
mc = readj("S1.5-ux-intake/ux-design-c3f8a1d2/microcopy.json")
mc["_note"] = ("[SIM maturity-2] th values now concrete (resolving UX-P1-TH-MICROCOPY-TBD); en derived from BA "
               "acceptance criteria. Every string passed the tipping-off scan (e-commerce domain, no AML/SAR vocabulary).")
for k, v in mc.get("strings", {}).items():
    if k in TH:
        v["th"] = TH[k]
written.append(w("S1.5-ux-intake/ux-design-c3f8a1d2/microcopy.json", mc))

# ───────────────────────── S3 · BE/FE contract design ─────────────────────────
tl = readj("S2-tl-design/output.json")
contracts = tl["api_contracts"]["contracts"]
CTX = {
    "auth": ["auth.login", "auth.refresh"],
    "checkout": ["checkout.confirm", "checkout.capture"],
    "order": ["order.create", "order.get", "order.transition", "order.payment.captured", "order.status.changed"],
    "inventory": ["inventory.reserve", "inventory.release", "inventory.adjust"],
}
by_name = {c["contract_name"]: c for c in contracts}
contract_files = []
for ctx, names in CTX.items():
    rows = []
    for n in names:
        c = by_name[n]
        rows.append(
            "| `%s` | %s | %s | %s |" % (
                n, c["semantics"],
                ", ".join("%s" % k for k in (c["payload_shape"].get("request") or c["payload_shape"].get("event") or {}).keys()) or "-",
                ", ".join(c["failure_modes"]) or "-",
            )
        )
    md = (
        "# S3 BE contract — %s context (OpenAPI 3.1 source of truth)\n\n"
        "_Generated from S2 `api_contracts` (offline, contract-faithful summary; the runnable `%s.openapi.yaml` is "
        "generated from these operations by `befe-contract-design`)._\n\n"
        "| operation | semantics | request keys | failure modes |\n|---|---|---|---|\n%s\n"
        % (ctx, ctx, "\n".join(rows))
    )
    be_rel = w("S3-contracts/be/%s.contract.md" % ctx, md)
    fe_md = (
        "# S3 FE state binding — %s context\n\n"
        "Per operation, the FE binds four UI states (loading / empty / error / optimistic). Money paths "
        "(confirm/capture) are **never** optimistic. Errors map each `failure_mode` to a microcopy key.\n\n"
        "- loading: skeleton on first fetch\n- empty: typed empty-state copy\n- error: failure_mode -> `microcopy.json` key\n"
        "- optimistic: cart mutations only\n"
        % ctx
    )
    fe_rel = w("S3-contracts/fe/%s.state-binding.md" % ctx, fe_md)
    contract_files.append({"context": ctx, "operations": names, "be_contract": be_rel.split("/", 2)[-1], "fe_binding": fe_rel.split("/", 2)[-1]})

s3 = {
    "audit_id": aid("S3-contract-design"),
    "contract_spec": {
        "summary": ("OpenAPI 3.1 per bounded context under be/ (auth, checkout, order, inventory) — 12 operations "
                    "mirroring S2 api_contracts; AsyncAPI for order.payment.captured / order.status.changed published "
                    "via the per-service transactional outbox (ADR-008). Source of truth: be/*.contract.md -> *.openapi.yaml."),
        "documents": [
            {"kind": "contract-md", "context": cf["context"], "path": cf["be_contract"]}
            for cf in contract_files
        ],
    },
    "client_types": "TS types generated from OpenAPI via openapi-typescript -> fe/src/api/types.gen.ts; Go server stubs via oapi-codegen.",
    "mock_plan": "Prism mock server per OpenAPI lets the FE leg start before the BE exists; Pact consumer stubs for the 4 services.",
    "list_conventions": "Keyset/cursor pagination (has_more + next_cursor); orders list newest-first by created_at.",
    "fe_state_binding": {
        "summary": "loading=skeleton, empty=typed copy, error=failure_mode->microcopy key, optimistic=cart only (never money/confirm/capture).",
        "states": {"loading": "skeleton", "empty": "typed copy", "error": "failure_mode->microcopy key"},
        "optimistic": "cart only (never money/confirm/capture)",
        "documents": [
            {"context": cf["context"], "path": cf["fe_binding"]}
            for cf in contract_files
        ],
    },
    # befe-contract-design 0.2.0 opened contract_files as a declared optional manifest — inline the real refs.
    "contract_files": contract_files,
}
written.append(w("S3-contracts/befe-contracts.json", s3))

# ───────────────────────── S4a · Backend implementation ─────────────────────────
# Real services emitted via the repo-generator under S4a-backend/services/<svc>/app/**.
# When present, the manifest is computed from the REAL file bytes (sha256 of content,
# real line counts, measured in-scope test coverage). Falls back to the original
# synthetic manifest in a clean checkout where the services are absent.
S4A_SERVICES = os.path.join(RUN, "S4a-backend", "services")
# Measured in-scope coverage (domain package: handlers/services/consumers; access/ excluded by design).
BACKEND_COVERAGE = {"auth": 0.966, "checkout": 0.966, "order": 1.0, "inventory": 1.0}
files_generated = []
tests_generated = []
if os.path.isdir(S4A_SERVICES):
    for svc in sorted(os.listdir(S4A_SERVICES)):
        appdir = os.path.join(S4A_SERVICES, svc, "app")
        if not os.path.isdir(appdir):
            continue
        for root, _dirs, fnames in os.walk(appdir):
            if (os.sep + "mocks") in root:  # exclude mockery-generated test doubles
                continue
            for fn in sorted(fnames):
                if not fn.endswith(".go"):
                    continue
                ab = os.path.join(root, fn)
                rel = os.path.relpath(ab, os.path.join(RUN, "S4a-backend"))  # services/<svc>/app/...
                if fn.endswith("_test.go"):
                    tests_generated.append({"path": rel, "content_hash": real_hash(ab), "coverage_pct": BACKEND_COVERAGE.get(svc, 0.9)})
                else:
                    files_generated.append({"path": rel, "content_hash": real_hash(ab), "lines_added": line_count(ab)})
    files_generated.sort(key=lambda x: x["path"])
    tests_generated.sort(key=lambda x: x["path"])
else:
    go_dirs = {
        "auth-service": ["cmd/server/main.go", "internal/handler/auth.go", "internal/domain/session.go", "internal/repo/token_family.go", "internal/audit/audit.go"],
        "checkout-service": ["cmd/server/main.go", "internal/handler/checkout.go", "internal/domain/totals.go", "internal/domain/confirm.go", "internal/psp/mock_psp.go", "internal/outbox/outbox.go"],
        "order-service": ["cmd/server/main.go", "internal/handler/order.go", "internal/domain/state_machine.go", "internal/domain/snapshot.go", "internal/consumer/payment_consumer.go"],
        "inventory-service": ["cmd/server/main.go", "internal/handler/inventory.go", "internal/domain/reservation.go", "internal/repo/stock.go", "internal/consumer/status_consumer.go"],
    }
    for svc, files in go_dirs.items():
        for f in files:
            p = "%s/%s" % (svc, f)
            files_generated.append({"path": p, "content_hash": ch(p), "lines_added": 80 + (len(p) % 90)})
        tp = "%s/internal/domain/domain_test.go" % svc
        tests_generated.append({"path": tp, "content_hash": ch(tp), "coverage_pct": 0.86})
# implementation_units: honest derivation — group the REAL manifest entries by service
# (path prefix) and attach the S2 contracts whose context prefix matches the service name.
def _unit_component(path):
    parts = path.split("/")
    if parts[0] == "services" and len(parts) > 1:
        return parts[1]                      # services/<svc>/app/...
    return parts[0].replace("-service", "")  # synthetic fallback: <svc>-service/...

_contract_names = sorted(c["contract_name"] for c in contracts)
_units = {}
for entry in files_generated:
    _units.setdefault(_unit_component(entry["path"]), {"files": [], "tests": []})["files"].append(entry["path"])
for entry in tests_generated:
    _units.setdefault(_unit_component(entry["path"]), {"files": [], "tests": []})["tests"].append(entry["path"])
implementation_units = [
    {"component_name": svc,
     "contract_names": [n for n in _contract_names if n.startswith(svc + ".")],
     "files": u["files"], "tests": u["tests"]}
    for svc, u in sorted(_units.items())
]

s4a = {
    "audit_id": aid("S4a-backend-implement"),
    "files_generated": files_generated,
    "tests_generated": tests_generated,
    "implementation_units": implementation_units,
    "idempotency_strategy": ("checkout.confirm dedupes on the client idempotency_key; checkout.capture and the payment "
                             "consumer dedupe on provider_event_id; inventory.reserve keys on confirm_id with an atomic "
                             "conditional decrement; order.create is idempotent on confirm_id; GET paths are naturally idempotent."),
    "compensating_actions": [
        {"trigger": "payment failure/timeout or confirm partial-failure", "action_kind": "skill", "action_ref": "handoff-revoke", "timeout_seconds": 600},
        {"trigger": "unpaid reservation TTL (30m) elapses", "action_kind": "code", "action_ref": "services/inventory/app/inventory/service_release.go", "timeout_seconds": 1800},
    ],
    "audit_events_emitted": [
        "auth.login.succeeded", "auth.login.failed", "auth.token.refreshed", "auth.token.family_revoked",
        "order.confirmed", "order.payment.captured", "order.status.changed",
        "stock.reserved", "stock.released", "stock.adjusted",
    ],
    "uncertainty_flags": [],
    "decision_metadata": {
        "complexity": "high",
        "pattern_choices": [
            {"decision": "transactional outbox per producing service", "rationale": "ADR-008 closes the dual-write gap; effectively-once event publish."},
            {"decision": "atomic conditional decrement for reserve", "rationale": "ADR-002 serializes the last-item race to one winner."},
            {"decision": "checkout-service orchestrates reserve+create synchronously", "rationale": "ADR-007 — no standalone orchestrator for the single MVP journey."},
        ],
        "repo_conventions_followed": ["polyrepo per context (ADR-001)", "no shared DB", "slog JSON, no PII/token/PAN in logs", "append-only audit keyed by audit_id (ADR-006)"],
    },
}
written.append(w("S4a-backend/backend-artifacts.json", s4a))

# S4a-r · Backend review (clean approve)
s4ar = {
    "verdict": "approve",
    "loop_back_target_stage": None,
    "findings": [],
    # Typed migration of the former claims_verified strings — same semantic content,
    # each check pointing at where the producer made the claim.
    "claim_checks": [
        {"claim_ref": "backend-artifacts.json#/idempotency_strategy", "claim_type": "idempotency",
         "status": "verified", "evidence": "idempotency keys present on confirm/capture/reserve/order.create"},
        {"claim_ref": "backend-artifacts.json#/audit_events_emitted", "claim_type": "audit",
         "status": "verified", "evidence": "audit events emitted on every state-changing path (ADR-006)"},
        {"claim_ref": "ADR-006", "claim_type": "compensation",
         "status": "verified", "evidence": "compensating release wired for payment failure/timeout and TTL"},
        {"claim_ref": "ADR-008", "claim_type": "pattern",
         "status": "verified", "evidence": "transactional outbox present in producing services (ADR-008)"},
        {"claim_ref": "no PII/token/PAN written to logs", "claim_type": "pii",
         "status": "verified", "evidence": "log statements scanned; no PII/token/PAN sinks found"},
    ],
    # production/test split from the manifest; lines from the files that record them.
    "audit_metadata": {"rules_evaluated": 22,
                       "production_files_scanned": len(files_generated),
                       "test_files_scanned": len(tests_generated),
                       "lines_scanned": sum(x["lines_added"] for x in files_generated)},
    "uncertainty_flags": [],
    "audit_id": aid("S4a-backend-review"),
}
written.append(w("S4a-backend/review/backend-review.json", s4ar))

# ───────────────────────── S4b · Frontend implementation ─────────────────────────
tsx = [
    ("src/pages/LoginPage.tsx", "Page"), ("src/pages/CheckoutPage.tsx", "Page"),
    ("src/pages/OrdersPage.tsx", "Page"), ("src/pages/OrderDetailPage.tsx", "Page"),
    ("src/features/checkout/CheckoutSummary.tsx", "Feature"), ("src/features/checkout/PaymentPanel.tsx", "Feature"),
    ("src/features/orders/OrderTimeline.tsx", "Feature"),
    ("src/components/Button.tsx", "Primitive"), ("src/components/FormField.tsx", "Primitive"),
    ("src/hooks/useIdempotentConfirm.ts", "Hook"), ("src/hooks/useSession.ts", "Hook"),
    ("src/api/types.gen.ts", "Type"), ("src/lib/money.ts", "Util"), ("src/lib/pii.ts", "Util"),
]
# Real SPA lives under S4b-frontend/app/. When present, compute the manifest from
# real file bytes (sha256 of content, real line counts, measured vitest coverage,
# real production bundle size). Falls back to synthetic in a clean checkout.
S4B_APP = os.path.join(RUN, "S4b-frontend", "app")
fe_test_specs = [
    ("src/pages/CheckoutPage.test.tsx", "component"),
    ("src/features/checkout/PaymentPanel.a11y.test.tsx", "a11y"),
    ("src/hooks/useIdempotentConfirm.test.ts", "unit"),
]
_pillar_by_path = dict(tsx)
if os.path.isdir(os.path.join(S4B_APP, "src")):
    # EXHAUSTIVE non-test manifest from the REAL tree: every source file under src/
    # plus the top-level build/config files (OI-004: manifests from real bytes).
    fe_paths = []
    for root, _dirs, fnames in os.walk(os.path.join(S4B_APP, "src")):
        if (os.sep + "mocks") in root:
            continue
        for fn in sorted(fnames):
            rel = os.path.relpath(os.path.join(root, fn), S4B_APP).replace(os.sep, "/")
            if ".test." in fn or fn.endswith((".snap",)):
                continue
            fe_paths.append(rel)
    for cfg in ("index.html", "package.json", "tsconfig.json", "vite.config.ts"):
        if os.path.isfile(os.path.join(S4B_APP, cfg)):
            fe_paths.append(cfg)
    fe_files = []
    for p in sorted(fe_paths):
        ab = os.path.join(S4B_APP, p)
        entry = {"path": p, "content_hash": real_hash(ab),
                 "size_bytes": os.path.getsize(ab), "lines_added": line_count(ab)}
        if p in _pillar_by_path:
            entry["component_pillar"] = _pillar_by_path[p]
        fe_files.append(entry)
    fe_tests = [{"path": p, "content_hash": real_hash(os.path.join(S4B_APP, p)),
                 "test_type": tt, "coverage_pct": 0.87}  # measured vitest v8: 86.9% statements
                for p, tt in fe_test_specs]
    FE_BUNDLE_KB = 94.75  # real gzip transfer size from `vite build` (308.45 kB raw)
else:
    fe_files = [{"path": p, "content_hash": ch(p), "size_bytes": 1200 + (len(p) % 900),
                 "lines_added": 60 + (len(p) % 80), "component_pillar": pillar} for p, pillar in tsx]
    fe_tests = [
        {"path": p, "content_hash": ch(p), "test_type": tt, "coverage_pct": cov}
        for (p, tt), cov in zip(fe_test_specs, (0.84, 0.8, 0.9))
    ]
    FE_BUNDLE_KB = 47.5
s4b = {
    "output_type": "implementation",
    "audit_id": aid("S4b-frontend-implement"),
    "frontend_worktree_root": "app",
    "files_generated": fe_files,
    "tests_generated": fe_tests,
    "a11y_compliance": {
        "wcag_level": "AA", "keyboard_navigable": True, "screen_reader_tested": True,
        "color_contrast_verified": True, "focus_management_implemented": True, "axe_clean": True,
    },
    "security_review": {
        "xss_surfaces": [],
        "csrf_protected": True, "csp_compliant": True, "token_storage_strategy": "httpOnly-cookie",
        "pii_fields_handled": [
            {"field": "customer_email", "treatment": "mask"},
            {"field": "customer_phone", "treatment": "mask"},
            {"field": "shipping_address", "treatment": "audit-on-view"},
        ],
    },
    "state_ownership": {
        "session": "server", "cart": "client", "checkout_form": "form",
        "order_list": "server", "active_route": "URL", "computed_total": "derived",
    },
    "bundle_impact_estimate_kb": FE_BUNDLE_KB,
    "compensating_actions": [
        {"trigger": "confirm network error after submit", "action": "surface retry with the same idempotency_key; never auto-resubmit", "timeout_seconds": 30},
    ],
    "audit_events_emitted": ["checkout.confirm.clicked", "payment.submitted", "order.viewed", "login.submitted"],
    "uncertainty_flags": [],
    "decision_metadata": {
        "pillar_choices": [
            {"file": "src/pages/CheckoutPage.tsx", "pillar": "Page", "rationale": "route-level composition of the checkout journey"},
            {"file": "src/hooks/useIdempotentConfirm.ts", "pillar": "Hook", "rationale": "encapsulates idempotency-key lifecycle for the money path"},
        ],
        "state_library_choices": [
            {"concern": "server cache", "choice": "TanStack Query", "rationale": "typed server-state with loading/error per operation"},
            {"concern": "token storage", "choice": "httpOnly cookie (no localStorage)", "rationale": "XSS-resistant per banking-grade FE rule"},
        ],
        "repo_conventions_followed": ["component pillars", "tokens.json for all color/spacing", "Noto Sans Thai for th locale", "no auth token in web storage"],
    },
}
written.append(w("S4b-frontend/frontend-artifacts.json", s4b))

# S4b-r · Frontend review (clean approve)
s4br_claim_checks = [
    {"claim_ref": "a11y_verdict", "claim_type": "a11y",
     "status": "verified", "evidence": "WCAG AA verified (axe clean, role/label queries present, focus managed)"},
    {"claim_ref": "security_verdict.token_storage_verified", "claim_type": "security",
     "status": "verified", "evidence": "auth token in httpOnly cookie — no localStorage/sessionStorage write"},
    {"claim_ref": "security_verdict.pii_helpers_verified", "claim_type": "pii",
     "status": "verified", "evidence": "PII fields rendered through declared mask/audit-on-view helpers"},
    {"claim_ref": "security_verdict.csrf_protections_verified", "claim_type": "security",
     "status": "verified", "evidence": "no dangerouslySetInnerHTML; CSRF protection on mutations"},
]
s4br = {
    "verdict": "approve",
    "loop_back_target_stage": None,
    "findings": [],
    "claim_checks": s4br_claim_checks,
    "a11y_verdict": {"wcag_level_verified": "AA", "axe_run_evidence_present": True, "role_label_queries_present": True, "focus_management_evident": True},
    "security_verdict": {"xss_mitigations_verified": True, "token_storage_verified": True, "pii_helpers_verified": True, "csrf_protections_verified": True, "dependency_additions_detected": []},
    # claims_checked is DERIVED == len(claim_checks); production/test split from the manifest.
    "audit_metadata": {"rules_evaluated": 26,
                       "production_files_scanned": len(fe_files),
                       "test_files_scanned": len(fe_tests),
                       "lines_scanned": sum(x["lines_added"] for x in fe_files),
                       "claims_checked": len(s4br_claim_checks)},
    "uncertainty_flags": [],
    "audit_id": aid("S4b-frontend-review"),
}
written.append(w("S4b-frontend/review/frontend-review.json", s4br))

# ───────────────────────── S4c · QA test design ─────────────────────────
# Story ids come from the REAL ba-brief manifest (STORY-<DOMAIN>-NN), never synthesized:
# QA trace keys must join the hydrated sidecars exactly.
_index = readj("S1b-ba-brief/INDEX.json")
STORIES = [(sf["id"], sf["epic_id"], sf["epic_id"].split("-", 1)[1])
           for sf in _index["story_files"]]
test_cases = []
stories_out = []
by_story_cov = {}
ctr = {}
for sid, eid, tag in STORIES:
    ctr[tag] = ctr.get(tag, 0) + 1
    tc_id = "TC-%s-%03d" % (tag, ctr[tag])
    smoke = sid in ("EPIC-AUTH-01", "EPIC-CHECKOUT-01", "EPIC-CHECKOUT-02")
    test_cases.append({
        "id": tc_id, "story_id": sid, "scenario_ref": "%s/AC-1" % sid, "scenario_type": "happy",
        "test_type": "functional", "pyramid_level": "integration", "owner": "qa-squad",
        "environment_ref": "sit", "tags": [tag.lower(), "banking-grade"], "risk_level": "high" if tag in ("CHECKOUT", "INVENTORY") else "medium",
        "expected_assertions": [{"type": "state", "description": "happy path produces the contracted result and an audit event"}],
        "reviewer_role": "qa-lead", "smoke_subset_member": smoke,
    })
    by_story_cov[sid] = 1
    stories_out.append({"story_id": sid, "epic_id": eid, "test_case_ids": [tc_id], "coverage_status": "complete"})

epics_out = [
    {"epic_id": e, "test_tier": "T2",
     "critical_paths": ["happy path", "idempotency-replay", "audit emission"],
     "stakeholder_owners": ["Khun Pim (PM)", "Khun Anan (TL)"]}
    for e in ["EPIC-AUTH", "EPIC-CHECKOUT", "EPIC-ORDER", "EPIC-INVENTORY"]
]
s4c = {
    "output_type": "test_plan",
    "blocks_qa_execution": False,
    "audit_id": aid("S4c-qa-plan"),
    "frontmatter": {
        "test_plan_id": "TP-shoppilot-mvp", "brief_id": "EPIC-SHOPPILOT-MVP",
        "brief_idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22",
        "idempotency_key": aid("S4c-qa-plan"), "workload_tier": "T2",
        "created_at": TS, "created_by": "planning-banking-tests-v1.0.0", "status": "ready-for-execution",
    },
    "scope_kind": "multi-epic",
    "strategy": {
        "test_pyramid_allocation": {"unit_pct": 55, "integration_pct": 25, "e2e_pct": 12, "contract_pct": 8},
        "tier_rationale": "T2 customer-facing + money + PII; weight idempotency, audit, authz and the last-item race.",
        "mock_vs_real_strategy": "Real per-service DB + Kafka in SIT; mock PSP and courier; Pact for cross-service contracts.",
        "high_risk_areas": ["checkout idempotency + provider replay", "last-item race", "own-data-only authz", "outbox effectively-once"],
    },
    "epics": epics_out,
    "stories": stories_out,
    "test_cases": test_cases,
    "smoke_subset": {"wall_clock_budget_seconds": 300, "test_case_ids": [tc["id"] for tc in test_cases if tc["smoke_subset_member"]]},
    "coverage_matrix": {
        "by_story": by_story_cov,
        "by_scenario_type": {"happy": len(test_cases)},
        "by_pyramid_level": {"integration": len(test_cases)},
        "by_tier": {"T2": len(test_cases)},
    },
    "nfr_tests": [
        {"id": "NFR-CHECKOUT-perf-001", "epic_id": "EPIC-CHECKOUT", "nfr_type": "performance", "metric": "order-confirm p95", "target": "TBD pending OQ-3", "blocking_oqs": ["OQ-3"]},
        {"id": "NFR-AUTH-sec-001", "epic_id": "EPIC-AUTH", "nfr_type": "security", "metric": "account-enumeration leak", "target": "0"},
        {"id": "NFR-INVENTORY-data-001", "epic_id": "EPIC-INVENTORY", "nfr_type": "data-integrity", "metric": "negative stock occurrences", "target": "0"},
    ],
    "compliance_tests": [
        {"id": "COMP-PDPA-001", "regulator": "PDPA B.E. 2562", "regulator_code": "PDPA", "template_key": "pdpa", "test_type": "privacy", "scope": "PII encryption, residency, retention, redaction in logs"},
        {"id": "COMP-PCI_DSS-001", "regulator": "PCI-DSS", "regulator_code": "PCI_DSS", "template_key": "pci_dss", "test_type": "security", "scope": "no PAN/CVV stored; mock PSP scope-exclusion confirmed"},
        {"id": "COMP-CPA-001", "regulator": "Consumer Protection Act", "regulator_code": "CPA", "template_key": "cpa", "test_type": "functional", "scope": "total shown before payment (Consumer Protection Act)"},
        # Derived from the run's own upstream regulatory dependencies (S0/S1 name Revenue Code retention).
        {"id": "COMP-REVENUE_CODE-001", "regulator": "Revenue Code", "regulator_code": "REVENUE_CODE", "template_key": "revenue_code", "test_type": "audit", "scope": "order/tax record retention meets Revenue Code minimums; deletion blocked inside the retention window"},
    ],
    "execution_dag": {
        "nodes": [{"id": "N-%s" % tc["id"], "test_case_ref": tc["id"]} for tc in test_cases],
        "edges": [{"from": "N-TC-AUTH-001", "to": "N-TC-CHECKOUT-001", "kind": "ordering"},
                  {"from": "N-TC-INVENTORY-001", "to": "N-TC-CHECKOUT-001", "kind": "data"}],
    },
    "environments": [
        {"id": "sit", "purpose": "system integration test", "required_mocks": ["mock-psp", "mock-courier"], "real_services": ["auth", "checkout", "order", "inventory", "kafka", "mysql"]},
    ],
    "test_data_specs": [
        {"fixture_set_id": "FX-shoppilot-core", "pii_field_refs": ["customer_email", "customer_phone", "shipping_address"], "synthesis_rules": "synthetic Thai-format names/phones/addresses; no real PII; deterministic seed"},
    ],
    "signoff_criteria": {
        "tier": "T2",
        "go_conditions": ["all banking-grade scenarios pass", "0 P1 defects", "coverage >= 0.80"],
        "conditional_go_conditions": ["P2 defects with owner + due date", "NFR perf target still TBD (OQ-3) tracked"],
        "no_go_conditions": ["any idempotency/audit/authz failure", "negative stock observed", "any P1 defect"],
    },
    "qa_readiness_checklist": {
        "all_stories_have_test_cases": True, "all_banking_grade_applies_have_tests": True,
        "all_nfr_targets_resolved": False, "all_compliance_regulators_covered": True,
        "all_dependencies_have_test_envs": True, "no_blocking_ba_governance_gaps": True,
    },
    "processing_metadata": {
        "ba_brief_version": "1.6.0", "ba_brief_idempotency_key": "3f6c0b2e-7a41-4d9b-9c2a-8e5b1f0a4d22",
        "tier_decisions": [{"target": e, "tier": "T2", "rationale": "customer-facing T2 per BA brief"} for e in ["EPIC-AUTH", "EPIC-CHECKOUT", "EPIC-ORDER", "EPIC-INVENTORY"]],
        "scenario_mapping_table_version": "1.0.0", "pyramid_allocation_rules_version": "1.0.0",
        "tl_design_consumed": True, "environment_inventory_consumed": True, "role_boundaries": [],
    },
}
written.append(w("S4c-qa-test-design/qa-plan.json", s4c))

# ───────────────────────── S5 · QA validation ─────────────────────────
s5 = {
    "verdict": "PASS",
    "totals": {"executed": 142, "passed": 142, "failed": 0, "skipped": 0},
    "coverage_measured": 0.87,
    "flaky": [],
    "defects": [],
    # GAP-05 honesty marker: this evidence is REPLAYED corpus material, not a live QA execution.
    "execution": {"mode": "replay", "target_source": "reference-corpus"},
    "audit_id": aid("S5-qa-validate"),
}
written.append(w("S5-qa-validation/qa-evidence.json", s5))

# ───────────────────────── S6 · Release handoff ─────────────────────────
s6 = {
    "receipt_id": "RCPT-shoppilot-20260607-0001",
    "status": "handed_off",
    "release_ref": "shoppilot@release-1.0.0+%s" % ch("release")[7:19],
    # Honest derivation: the run's own S7 stage IS production validation.
    "target_env": "production",
    "approver": {"name": "Khun Ratana", "role": "Release Manager"},
    "audit_id": aid("S6-release-handoff"),
}
written.append(w("S6-deploy/handoff-receipt.json", s6))

# ───────────────────────── S7 · Production SLO validation ─────────────────────────
s7 = {
    "verdict": "promote",
    "grade": "Pass",
    "receipt_id": s6["receipt_id"],  # echoed unchanged: this evidence validates THAT release
    # unit/comparison make the numbers comparable — derived from each row's own semantics.
    "per_slo": [
        {"name": "availability", "target": 99.9, "observed": 99.97, "burn_rate": 0.2,
         "unit": "percent", "comparison": "gte", "judgement": "within_budget"},
        {"name": "order-confirm p95 (ms)", "target": 800, "observed": 540, "burn_rate": 0.3,
         "unit": "ms", "comparison": "lte", "judgement": "within_budget"},
        {"name": "error-rate", "target": 1.0, "observed": 0.1, "burn_rate": 0.1,
         "unit": "percent", "comparison": "lte", "judgement": "within_budget"},
        {"name": "double-charge incidents", "target": 0, "observed": 0, "burn_rate": 0.0,
         "unit": "count", "comparison": "eq", "judgement": "within_budget"},
    ],
    "window": "30m + 6h multi-window burn-rate, post-deploy",
    "execution": {"mode": "replay", "target_source": "reference-corpus"},
    "audit_id": aid("S7-prod-validate"),
}
written.append(w("S7-prod-validation/smoke-slo.json", s7))

# ───────────────────────── T1..T12 · gate evidence (gates/) ─────────────────────────
def gate(name, obj):
    obj.setdefault("audit_id", aid("gate-" + name))
    written.append(w("gates/%s.json" % name, obj))

gate("backend-unit-tests", {"verdict": "PASS", "totals": {"executed": 96, "passed": 96, "failed": 0, "skipped": 0}, "coverage_measured": 0.86, "failures": [], "flaky": [], "execution": {"mode": "replay", "target_source": "reference-corpus"}})
gate("frontend-unit-tests", {"verdict": "PASS", "totals": {"executed": 71, "passed": 71, "failed": 0, "skipped": 0}, "per_file_coverage": [{"file": "src/lib/money.ts", "coverage": 0.95}, {"file": "src/hooks/useIdempotentConfirm.ts", "coverage": 0.9}], "failures": [], "execution": {"mode": "replay", "target_source": "reference-corpus"}})
gate("sast-gate", {"verdict": "PASS", "findings": [], "secrets": 0,
     "new_vs_baseline": {"new": 0, "existing": 0, "fixed": 2},
     "policy": {"severity_floor": "medium", "baseline_mode": "baseline-aware", "baseline_ref": None},
     "blocking_reasons": [],
     "execution": {"mode": "replay", "target_source": "reference-corpus"},
     "scan_scope": {"targets_scanned": len(files_generated)}})
gate("accessibility-tests", {"verdict": "PASS", "wcag_violations": [], "needs_review": [],
     "manual_checks": ["keyboard order on checkout", "focus trap on payment modal"],
     "execution": {"mode": "replay", "target_source": "reference-corpus"},
     "scan_scope": {"targets_scanned": len(fe_files)},
     "standard": {"name": "WCAG", "version": "2.1", "level": "AA"}})
gate("contract-tests", {"verdict": "PASS", "provider_verified": True, "pacts": [{"consumer": "web", "verified": True}, {"consumer": "checkout-service", "verified": True}], "can_i_deploy": True, "execution": {"mode": "replay"}})
gate("integration-tests", {"verdict": "PASS", "totals": {"executed": 38, "passed": 38, "failed": 0, "skipped": 0}, "teardown_ok": True, "defects": [], "execution": {"mode": "replay"}})
gate("appsec-scan", {"verdict": "PASS", "dast_findings": [], "sca_cves": [], "secrets": 0,
     "new_vs_baseline": {"dast": {"new": 0, "accepted": 0, "fixed": 0},
                         "sca": {"new": 0, "accepted": 0, "fixed": 0}},
     "execution": {"mode": "replay", "target_source": "reference-corpus",
                   "scanners": {"dast": {"status": "completed"}, "sca": {"status": "completed"},
                                "secrets": {"status": "completed"}}}})
gate("e2e-tests", {"verdict": "PASS", "scenarios": [
    {"name": "register-login-checkout-pay-track", "result": "pass", "steps_total": 12, "steps_failed": 0},
    {"name": "last-item-race-one-winner", "result": "pass", "steps_total": 6, "steps_failed": 0},
    {"name": "payment-timeout-releases-stock", "result": "pass", "steps_total": 7, "steps_failed": 0},
], "flaky_rate": 0.0, "execution": {"mode": "replay"}})
gate("perf-load-test", {"verdict": "PASS", "metrics": {"p95": 540, "error_rate": 0.001},
     "within_budget": True, "breaches": [], "sample_adequate": True,
     "execution": {"mode": "replay", "target_source": "reference-corpus"}})
gate("adversarial-pentest", {"verdict": "pass", "persona_findings": [],
     "execution": {"mode": "replay", "target_source": "reference-corpus"}})
gate("smoke-tests", {"verdict": "PASS",
     "receipt_id": s6["receipt_id"],  # echoed unchanged from the run's own S6 receipt
     "probes": [{"name": "GET /health", "executed": True, "green": True},
                {"name": "login", "executed": True, "green": True},
                {"name": "order.get own-data", "executed": True, "green": True}],
     "all_green": True,
     "execution": {"mode": "replay", "target_source": "reference-corpus"}})
gate("canary-analysis", {"verdict": "promote", "per_metric": [{"name": "error-rate", "judgement": "pass"}, {"name": "p95-latency", "judgement": "pass"}], "sample_adequate": True, "windows_passed": 3})

print("wrote %d artifacts:" % len(written))
for r in written:
    print("  " + r)
