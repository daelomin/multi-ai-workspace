# Risk register

Likelihood and Impact left as `?` for HUMAN review (P0-11).

Only risks already stated in `TODO.md` or `DECISIONS.md` are listed; each row cites its source.

| Risk | Likelihood | Impact | Mitigation | Owner | Status | Source |
|---|---|---|---|---|---|---|
| Floating-car data (FCD) / personal data in DATEX sources (GDPR) | ? | ? | Per-source GDPR determination in P0-4; unresolved legal questions need human/legal review before production use | CLAUDE (draft) · HUMAN (verify) | open | TODO P0-4 |
| Source licence terms block reuse, redistribution or derivation; may decide whether the platform can ever be open or public-facing | ? | ? | Record per-source licence results in `DECISIONS.md` (P0-4); licence intent internal-only until end of Phase 3 (D3) | CLAUDE / HUMAN | open | TODO P0-4; DECISIONS D3 |
| Derived-data licence scope limited by upstream source licences | ? | ? | Scope `LICENSE` / derived data after P0-4 source review (P0-7) | CLAUDE · HUMAN | open | TODO P0-7 |
| DATEX credentials and other secrets leak into the repo | ? | ? | Secrets only in `.env`; gitleaks pre-commit; PR Actions workflow still missing (`workflow` scope) | CURSOR · HUMAN | open | TODO P0-6 |
| Unowned P0 items stall Phase 0 | ? | ? | Owner assigned to every P0 item (P0-9 done) | HUMAN | mitigated | TODO P0-9 |
| Concurrent edits to shared files without handoff | ? | ? | Single-writer claim/release via `CHANGELOG.md` (P0-5 / D4); no locking tool unless proven needed | all agents | open | TODO P0-5 |
| Overwriting raw measures on correction loses the audit trail | ? | ? | D11: append revisions + `traffic_measure_current` view (overwrite rejected) | decided | mitigated | TODO D11; DECISIONS D11 |
| Late source corrections outside continuous-aggregate refresh window leave aggregates stale | ? | ? | Explicit refresh logged in `docs/aggregates_history.md` (D11 / P1-9) | (P1) | open | TODO D11; DECISIONS D11 |
| A11 DATEX access/licences insufficient for the pilot | ? | ? | Inventories and fallbacks in P0-4; axis freeze is A11-only for Phases 0–1 (D1) | CLAUDE / HUMAN | open | DECISIONS D1 (prior A11 ADR noted fallback axis) |
| Event rate may later justify a broker before Kafka is planned | ? | ? | Defer Kafka/Redpanda; keep Redis Streams until P1-6 measured rate justifies a broker (P1-7) | (P1) | open | TODO P1-7; DECISIONS D1 (no Kafka before phase 3) |
| GitHub rendering glitch for `CONTRIBUTING.md` / `CHANGELOG.md` blocks other agents reading rules | ? | ? | P0-12 HUMAN check from a logged-out browser | HUMAN | open | TODO P0-12 |
