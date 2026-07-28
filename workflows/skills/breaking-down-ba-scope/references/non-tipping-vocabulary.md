# Non-Tipping-Off Vocabulary Reference

> **Loaded when**: Step 7 detects a state-change story whose `audience` includes external customer OR `notification` Gherkin scenarios exist
> **Used by**: SKILL.md Step 7 (banking-grade evaluation) + `anti-patterns.md` AP-4.4 + `gherkin-templates.md` §6.3 (tipping-off-safe rejection)
> **Tier scope**: T1 mandatory, T2 strongly recommended, T3 best-effort
> **Authority**: Skill defaults reflect industry-standard non-tipping language. Specific regulator wording (MAS, OFAC, FinCEN, FCA) must be confirmed by Legal before production use — substitution is a hint, not a final ruling.

---

## 🛑 Forbidden Customer-Facing Phrases (P1 Tipping-Off Risk)

If the skill detects ANY of these in proposed customer-facing language, emit `governance_gap: tipping_off_risk` with `severity: P1` and `blocks_tl_handoff: true`.

| Forbidden phrase | Why dangerous | Domain it appears in |
|------------------|---------------|----------------------|
| "sanctions hold" / "sanctions screening" | Tips off OFAC / MAS sanctions subject | Wire / payments / KYC |
| "AML review" / "anti-money-laundering" | Tips off SAR target | Onboarding / payments |
| "PEP screening" / "PEP hit" | Tips off politically-exposed-person flag | KYC / EDD |
| "adverse media" / "negative news" | Tips off reputational screening | KYC / EDD |
| "suspicious activity" / "SAR" / "STR" | Direct tipping-off — reportable | Payments / cards / accounts |
| "flagged for fraud" / "fraud investigation" | Tips off internal fraud case | Cards / payments / accounts |
| "blocked by compliance" / "compliance hold" | Tips off compliance review | All |
| "regulator request" / "law enforcement" | Tips off legal-process recipient | All |
| "frozen by court order" / "subpoena" | Tips off enforcement | Accounts / cards |
| "high-risk customer" / "PEP customer" | Tips off risk tiering | KYC / onboarding |

---

## ✅ Safe Substitution Vocabulary (Suggested)

When the skill rewrites prose ACs into Gherkin scenarios involving rejection / hold / decline language, use SAFE phrases (still must be Legal-reviewed before production).

| Internal state (back-office) | Safe customer-facing language |
|------------------------------|--------------------------------|
| sanctions_hold / aml_review / pep_screen | "additional review" / "pending verification" |
| sanctions_reject / aml_decline | "the transfer could not be completed" / "the application could not proceed at this time" |
| fraud_hold / fraud_decline | "additional security review" / "transaction not approved" |
| compliance_hold (any reason) | "in review" / "verification in progress" |
| court_order_freeze | "access to this account is currently restricted" |
| pep_hit | "enhanced verification required" |
| adverse_media_hit | "additional information required" |
| sar_filed | (no customer-facing communication permitted) |
| blocked_jurisdiction | "this service is not available in your region" |
| velocity_limit_hit | "transaction limits reached — please try again later" |

---

## 🎯 ETA / Resolution Bucket Templates (Banking-Compliant)

When the skill proposes ETA buckets for customer-facing status messages, use CONSERVATIVE language:

| Internal SLA | Customer-facing ETA |
|--------------|---------------------|
| < 4 hours | "shortly" / "within a few hours" |
| 4-24 hours | "within 1 business day" |
| 24-72 hours | "within 3 business days" |
| 24-120 hours (variance) | "up to 5 business days" (conservative — covers long tail) |
| > 5 business days | "we will contact you with an update" (no specific ETA) |

**Anti-pattern**: Flattening different SLAs into single ETA bucket (eg compliance-hold = 24-72h + ops-review = same-day mashed into "up to 5 business days") — surface this as P2 (granularity loss, not safety).

---

## 🔁 State-Transition Notification Rules

For each customer-facing state change, evaluate notification policy:

| State transition | Notify customer? | Channel | Tipping-off risk |
|------------------|------------------|---------|-------------------|
| pending → in-review (additional review) | Yes | In-app + email | Low — generic |
| in-review → approved | Yes | In-app + email | None |
| in-review → declined (generic) | Yes — generic only | Email only | High — language must be tipping-off-safe |
| in-review → declined (sanctions/AML) | No customer-facing detail | Email generic only | CRITICAL — refer to Legal |
| any → SAR-filed | NO communication permitted | None | CRITICAL — quiet hold |

The skill must NEVER emit a Gherkin scenario where Then-clause directly communicates a regulated-reason to the customer.

---

## 🛡️ Forced-Evaluation Rule (Skill-Side)

When the skill processes any input that contains:
- "tell the customer..." / "notify the customer..." / "customer-facing message..."
- "decline reason" / "rejection message" / "hold reason shown to customer"
- "in-app status" / "push notification" / "email template"

The skill MUST:
1. Run a tipping-off scan against this reference's Forbidden Phrases table
2. Set `processing_metadata.tipping_off_scan_clean: false` if any match
3. Emit `governance_gap: tipping_off_risk` at P1
4. Add OQ: "Confirm customer-facing language with Legal — proposed phrasing reviewed against tipping-off prohibition"
5. Suggest safe substitutions where possible

If `tipping_off_scan_clean: true`, the field is still emitted (force-fill — evaluation is mandatory, not the result).

---

## 📚 Cross-References

- `SKILL.md` Step 7 — Banking-grade per-story evaluation (consumes this file)
- `anti-patterns.md` AP-4.4 — "Tipping-off-risky language echoed to customer"
- `gherkin-templates.md` §6.3 — Tipping-off-safe rejection scenarios
- `ambiguity-patterns.md` §3.3 — Mandatory-vagueness (regulator-required) exception

---

## ⚠️ Legal Disclaimer

This reference reflects general industry practice. **Specific phrasing requires Legal review** before production deployment. The skill emitting a substitution is a HINT for downstream Legal review, not a final approval. Always loop in Legal when proposing customer-facing language touching any regulated state.
