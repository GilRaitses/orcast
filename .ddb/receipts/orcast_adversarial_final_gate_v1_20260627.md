# orcast_adversarial_final_gate_v1_20260627

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_adversarial_final_gate_v1_20260627.yaml`
**Registered artifact:** `.sst/ax_adversarial_final_gate_v1.json`
**Registry decision_id:** `461ab56a443771e53d72721ae56988765e55d274f5af2406cd4cec49eb1ebf1e`
**Date:** 2026-06-27 America/New_York

---

## Summary

Pre-P1 adversarial final-gate (AX) + copy/prose sweep (CX). One P0 found and fixed;
all lanes clean; copy-gate green; tracked limits dispositioned. Full detail in
`.cca/AX_ADVERSARIAL_REGISTER.md`.

## Headline

P0 auth bypass: evidence/journal reachable on the public tunnel via a spoofed
reviewer header (PII). Fixed with router-level `require_api_key`, verified 401.

## Lane verdicts

AX-0 PASS, AX-1 FIXED(P0), AX-2 FLAG (ONC SSRF inert while disabled), AX-3 PASS,
AX-4 PASS, AX-5 PASS, AX-6 PASS, AX-7 PASS, AX-8 PASS. CX copy-gate GREEN.

## Open operator gates

SES production-access request; P1 OX gates (DynamoDB screenshot, Devpost, arXiv);
post-submission App Runner pause.

Authoritative registration lives in the paired YAML decision + the registered
`.sst` artifact. This receipt is a non-authoritative mirror.
