# FuelBuddy charging diagnostic — HUMAN decisions

Decisions made by HUMAN. A decision listed here is **settled**: reviewers must not re-open it, and CLAUDE applies it to `spec.md` at the next consolidation (replacing the matching "Pending HUMAN decision" passage and the affected sections). Open decisions stay in the latest `reviews/round-N/CONSOLIDATION.md`.

| ID | Decision | Date | Decided by |
| --- | --- | --- | --- |
| FB-D1 | **The MVP market is Europe.** Clarified the same day: Europe means the EU/EEA **plus the UK and Switzerland**, and generally **all countries that have an API**. | 2026-10-14 | HUMAN |
| FB-D2 | **Approved with amendments:** the proposed clearance semantics of §5 stand (restrictions are cleared only by evidence and an authorized actor, never by time, a missing warning or a later successful session), amended as in the FB-D2 notes below. | 2026-10-14 | HUMAN |
| FB-D3 | **Approved as recommended, simplified.** (1) The app never originates a "press the station's emergency stop" instruction. (2) A stuck connector after charging gets an OEM-sourced playbook. (3) Every session screens for hazards. See the FB-D3 notes below. | 2026-10-14 | HUMAN |
| FB-D5 | **Approved as recommended:** when package validity cannot be established, the app degrades by risk (see the FB-D5 notes below); stale data never makes it more permissive than fresh data. | 2026-10-14 | HUMAN |
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

## Notes for the consolidator on FB-D2

Replace the FB-D2 "Pending HUMAN decision" passages (§4.4 `restriction` enum, §5 clearance semantics) with the settled text, apply these amendments, and remove FB-D2 from the carried-forward open list:

1. **Fail closed on unknowns.** `other`, or any restriction value without a human-approved mapping, behaves as `do_not_charge` until a reviewed mapping exists. Free text is never read to infer a milder behaviour.
2. **Authorized actor per class.** Recall restriction: cleared only by an authority or OEM source showing that campaign completed (VIN-level lookup or remedy record), never by driver statement. Damaged or faulted charging equipment: cleared by the operator or site owner, or their status feed. Vehicle high-voltage fault or fire/thermal event: cleared by qualified service or an OEM-authorized inspection.
3. **Users can raise, not clear.** A driver report can raise a restriction. Self-clearing is out of MVP scope.
4. **Scope.** Equipment-scoped restrictions (charger, connector) stay with that equipment and do not block the vehicle elsewhere. Vehicle-scoped and campaign-scoped restrictions follow the vehicle. When restrictions conflict, the most restrictive wins.
5. **Equipment restrictions get a re-verification prompt, not an expiry.** After a period HUMAN approves, advice to other drivers downgrades to "unverified, last reported on <date>, check the operator". The restriction is never cleared by time alone. The period is an open parameter: list it as a question for HUMAN and do not invent a number.

Restriction values map to driver-facing behaviour as follows:

| Value | Driver-facing behaviour |
| --- | --- |
| `none` | Normal flow with the usual bounded approved actions |
| `do_not_charge` | No retry or alternate-charging advice; show the exact approved text; escalate to OEM or service |
| `charge_limited` | Only the approved limited-charging instructions as published; nothing else |
| `do_not_charge_indoor` | Outdoor-only guidance with the approved warning |
| `other` or unmapped | Treated as `do_not_charge` (amendment 1) |

Emergency numbers stay reviewed per-country configuration (EU/EEA, UK, Switzerland); do not hard-code them. The wording of this safety policy should get legal review, together with FB-D4; that is not a blocker for the loop.

## Notes for the consolidator on FB-D3

Replace the FB-D3 "Pending HUMAN decision" passage in §4.7 with the settled text and remove FB-D3 from the carried-forward open list.

1. **No emergency-stop instruction from the app.** The app has no sensor on the charger; a hazard reaches it only through what the driver reports (typed or spoken text, an intake answer, a photo hint) or through an operator or station fault feed. When the driver reports smoke, sparks, burning, or melted or burnt parts, the app stops troubleshooting and shows the approved §5 message (move away, keep others clear, contact local emergency services, do not touch the equipment). It does not originate advice to use a physical emergency control. It may display an instruction that the station operator has published and the registry has approved, as operator-originated guidance.
2. **Stuck connector.** Add a playbook for a connector that will not release after charging. Every action comes from an OEM or standards source with `evidence_ids`, like any other playbook; it never advises forcing the plug or pulling the cable. When the OEM publishes no procedure, the app says so and escalates to the operator or roadside assistance instead of improvising.
3. **Hazard screening.** Every session begins with a hazard screening question (smoke, sparks, melted or burnt parts, burning smell). A yes goes straight to the emergency message. The same check runs on free-text and voice input. A photo can at most raise a hazard hint that becomes a question to the driver, never a conclusion. Fault codes from a station feed (for example OCPP `GroundFailure`, `OverCurrentFailure`, `HighTemperature`) are not by themselves evidence of fire (§5).
4. Do not treat the app as a smoke or fire detector anywhere in the spec; check the wording of §5 so its "observation" rows are visibly driver-reported or feed-reported.
5. The emergency-message wording should get legal review together with FB-D4; that is not a blocker for the loop.

## Notes for the consolidator on FB-D5

Replace the FB-D5 reference in the §12 offline/failure row, and add the settled behaviour where the spec describes cached knowledge packages. Remove FB-D5 from the carried-forward open list.

Principle: stale or unverifiable data must never make the app more permissive than verified data would.

| Cached content | Behaviour when validity cannot be established |
| --- | --- |
| Safety rules and the hazard message | Always available and always shown; they are conservative, so staleness cannot make them more dangerous. |
| Restrictions and recall campaigns | Known restrictions stay in force and are never cleared offline. Show "last checked <date>". A missing or old recall status is never treated as "no recall" (it stays `unknown`). |
| Approved diagnostic playbooks | Available with a visible "may be out of date, last updated <date>" notice; only bounded approved actions with fixed retry limits. |
| Items marked withdrawn or superseded | Not shown once the app knows. When it cannot know, show as "unverified", not as current guidance. |
| LLM-written explanations | Not available offline; fall back to the approved rendered text (§9). |

A package that is merely old keeps working with the notice. A package older than a hard limit is restricted to safety content plus a plain "update when you have signal" message. **The hard limit is an open parameter for HUMAN: list it as a question, do not invent a number.** Also record that weak connectivity is common at charging sites, so a hard block on "cannot verify" is not acceptable behaviour.
