# FuelBuddy charging diagnostic — HUMAN decisions

Decisions made by HUMAN. A decision listed here is **settled**: reviewers must not re-open it, and CLAUDE applies it to `spec.md` at the next consolidation (replacing the matching "Pending HUMAN decision" passage and the affected sections). Open decisions stay in the latest `reviews/round-N/CONSOLIDATION.md`.

| ID | Decision | Date | Decided by |
| --- | --- | --- | --- |
| FB-D1 | **The MVP market is Europe.** | 2026-10-14 | HUMAN |

## Notes for the consolidator on FB-D1

HUMAN gave the decision as "Europe" only. Do not invent more precision than that:

- Apply it where the spec depends on the market (§1.1 scope; in-scope connector types; the recall/safety source class; seed sources and examples, which are US today; the privacy frame in §10 as a *proposal* for FB-D4).
- Where the exact boundary matters (EU only, EEA, UK, which countries first), list it as a new open question for HUMAN instead of choosing.
- Keep North America out of MVP scope; it may stay as a later-phase record set.
- FB-D4 (legal basis, DPIA, processor agreement) is **not** settled by this decision and still needs legal review.
