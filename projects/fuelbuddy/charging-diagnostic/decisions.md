# FuelBuddy charging diagnostic — HUMAN decisions

Decisions made by HUMAN. A decision listed here is **settled**: reviewers must not re-open it, and CLAUDE applies it to `spec.md` at the next consolidation (replacing the matching "Pending HUMAN decision" passage and the affected sections). Open decisions stay in the latest `reviews/round-N/CONSOLIDATION.md`.

| ID | Decision | Date | Decided by |
| --- | --- | --- | --- |
| FB-D1 | **The MVP market is Europe.** Clarified the same day: Europe means the EU/EEA **plus the UK and Switzerland**, and generally **all countries that have an API**. | 2026-10-14 | HUMAN |
| FB-D7 | **Option A:** ship the documented ordering (ordinary causes first, specificity gated as in §6.2). Calibrated base rates stay deferred to §6.3; ranking is not blocked until calibration. | 2026-10-14 | HUMAN |

## Notes for the consolidator on FB-D1

HUMAN gave the decision as "Europe" only. Do not invent more precision than that:

- Apply it where the spec depends on the market (§1.1 scope; in-scope connector types; the recall/safety source class; seed sources and examples, which are US today; the privacy frame in §10 as a *proposal* for FB-D4).
- Scope in HUMAN's words: the EU/EEA, the UK and Switzerland, and generally every country that has an API. Treat "has an API" as the inclusion rule for a country, not a fixed list.
- HUMAN did not say *which* API makes a country eligible (for example public recall/safety data, charge-point status or location data). Do not choose: list it as an open question for HUMAN, and do not name specific APIs or endpoints you cannot source.
- Which countries launch first, and whether a country without a usable API is excluded or served in a reduced mode, are also open questions for HUMAN.
- Keep North America out of MVP scope; it may stay as a later-phase record set. A multi-country scope means the spec cannot assume one regulator, one recall source or one legal frame; surface that as a consequence.
- FB-D4 (legal basis, DPIA, processor agreement) is **not** settled by this decision and still needs legal review.

## Notes for the consolidator on FB-D7

- Replace the FB-D7 "Pending HUMAN decision" passage in §6.2 with the Option A text as the settled design, and remove FB-D7 from the carried-forward open list.
- Keep the calibration work in §6.3 as planned follow-up, and keep the release-gate wording consistent with a documented, not yet calibrated, ordering. Do not add calibrated numbers or sources that nobody has provided.
- D6 of round 2 (ordinary-cause ordering) referred to FB-D7; re-check that reference now reads as settled.
