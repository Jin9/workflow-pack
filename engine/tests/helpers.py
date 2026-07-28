"""Shared test helpers. A real module, NOT conftest: importing conftest directly
creates a second module object and makes test order significant."""
from __future__ import annotations

# One DISTINCT named human per quorum role — the three-amigos gate refuses a
# single approver signing three times, so tests must supply three names.
AMIGOS = {"ba-lead": "Khun Pim", "dev-lead": "Khun Anan", "qa-lead": "Khun Ratree"}


def quorum_aware_hook(approver: str):
    """An approve_hook that handles BOTH gate shapes: one decision for an ordinary
    gate, and one decision per outstanding role for a quorum gate."""
    def hook(gate):
        verdict = gate.spec.proceed_when or (
            "approve" if "approve" in gate.spec.verdicts else gate.spec.verdicts[0])
        if gate.spec.quorum:
            for role in gate.outstanding_roles:
                return (verdict, AMIGOS[role], f"test {role} approval", role)
            return None
        return (verdict, approver, "test approval")
    return hook
