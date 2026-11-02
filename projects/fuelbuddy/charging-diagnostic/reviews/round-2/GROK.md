# GROK review — round 2

**Specification:** local `spec.md`, v0.3, dated 11 October 2026.
**Reviewer:** GROK. **Review date:** 2026-10-14.
**Method:** Read `reviews/round-1/` (CLAUDE, CHATGPT, DEEPSEEK, and `CONSOLIDATION.md`) before the current local spec. Accepted round-1 items are reopened only where the merged text is still wrong. FB-D1–FB-D7 are not reopened: no new evidence bears on those policy choices. External claims below were checked on 2026-10-14; ISO 15118-2 and IEC 61851-1 themselves were not opened (paywalled). No error code, campaign number, or clause number is invented.

**Overall:** 0 blocking, 3 major, 2 minor. The round-1 direction holds. The three majors are places where v0.3's merged contract is still factually wrong or cannot represent a case it already claims to diagnose. I agree with the measurement-identity gap (my GROK-3; same defect as the other round-2 major on §3.2/§6.4) and do not restate the other reviewers' wording nits.

### GROK-1 · The Plug & Charge stage order is reversed, and basic AC has no path

- **Section:** §3.3
- **Type:** error
- **Severity:** major
- **Finding:** The prose in §3.3 is right that Plug & Charge authorizes after communication setup and service selection. The normative table then places `parameter_negotiation` *before* `authorization`. Published ISO 15118-2 sequences do the opposite: communication setup, then identification and authorization (service discovery, payment-service selection, and for Plug & Charge the contract-certificate and Authorization exchange), and only then ChargeParameterDiscovery. "Last successful stage" against the table will treat a parameter-discovery failure as an authorization failure. Separately, the same `rfid`/`app` row always continues into `communication_setup`, but IEC 61851 Mode 3 AC uses mandatory control-pilot PWM and only optional high-level communication. A normal PWM-only session never enters `communication_setup` or `parameter_negotiation`, so the table marks a successful basic AC charge as a skipped stage. One `authorization` stage also conflates an external RFID/app action, which can precede plug-in, with the later ISO 15118 Authorization message.
- **Proposed change:** Replace the `plug_and_charge` row with: discovery → connected → communication_setup (SLAC, association, session setup) → authorization (service discovery, payment-service selection, and for Plug & Charge the contract and Authorization exchange) → parameter_negotiation → power_delivery → charging. Insert DC `safety_checks` (cable check, then precharge) only between parameter negotiation and power delivery; the AC high-level sequence goes from parameter discovery to power delivery without that pair. Split external identification from protocol authorization: record an optional `external_authorization` event whose order relative to plug-in is not fixed, and do not treat it as the ISO 15118 Authorization stage. Add a `communication_profile` of `iec61851_pwm_only` | `iso15118` | `din70121` | `chademo` | `unknown`. For `iec61851_pwm_only`, applicable stages are discovery, connected, external authorization, power_delivery, charging; `communication_setup` and `parameter_negotiation` are `not_applicable`, not failed. Do not reuse the ISO order for `chademo`; leave that profile's order unspecified until a sourced sequence is added. Interpret "last successful stage" only along stages applicable to the profile.
- **Evidence:** [Typhoon HIL, ISO 15118-2 protocol](https://typhoon-hil.com/documentation/typhoon-hil-software-manual/References/iso15118_protocol.html), checked 2026-10-14: Mode 3 is "Mandatory PWM signaling and optional High Level Communication"; the DC and AC sequences both run Authorization, then ChargeParameterDiscovery, then PowerDelivery; CableCheck and PreCharge are listed on the DC sequence only. Secondary description of the protocol, not the ISO text.
- **Confidence:** high on the authorization/parameter-discovery order and on PWM-only AC having no high-level session; medium on treating cable check as DC-only, because that rests on this secondary sequence rather than the standard.

### GROK-2 · An OCPP 2.0.1 fault still has no identity in the mapping key

- **Section:** §3.2, §4.5, §9.1
- **Type:** gap
- **Severity:** major
- **Finding:** Round-1 C4 was accepted, but the normative key is still `namespace + issuer + protocol_version + message_type + field_path + product_model + firmware_scope + raw_code`. There is no `component`, `variable`, or `tech_code`. In OCPP 2.0.1, `StatusNotification` no longer carries `errorCode`; faults are `NotifyEvent` reports for a specific device-model component and variable, with optional free-form `techCode` and `techInfo`. Two events with the same `techCode`, or with none, on different components collapse to one mapping. The only §9.1 example is still OCPP 1.6 `StatusNotification.errorCode`. `field_path` is not defined as an encoding of component and variable, so an implementer cannot build the key C4 asked for.
- **Proposed change:** Add nullable `component`, `variable`, and `tech_code` to the §3.2 record and to the §4.5 mapping key. For an OCPP 2.0.1 device-model event, a match requires `message_type = NotifyEvent` plus component name and variable name; `tech_code` distinguishes vendor detail when present and is not a substitute for the component and variable. A vendor mapping that lacks component and variable must not match. Keep the existing rule that unknown firmware does not satisfy a firmware-scoped vendor mapping. Add one illustrative `NotifyEvent` example whose component and variable are taken from the Open Charge Alliance white paper's device-model examples, labelled illustrative, with no invented fault code. Do not claim a fixed cross-version map from 1.6 `ChargePointErrorCode` values onto 2.0.1 events; the white paper says the station's device model decides what is reported.
- **Evidence:** [Open Charge Alliance, Improving Uptime Monitoring with OCPP, v1.2, August 2024](https://openchargealliance.org/wp-content/uploads/2024/08/improving_uptime_with_ocpp_v1_2.pdf), §§4.2.2 and 4.2.4, checked 2026-10-14. The OCPP 2.0.1 specification itself was not re-read.
- **Confidence:** high.

### GROK-3 · Measurement observations cannot carry the distinctions §5 and §6.4 already require

- **Section:** §3.2, §5, §6.4, §10
- **Type:** gap
- **Severity:** major
- **Finding:** §6.4 forbids comparing charger output with battery-reported power, and it requires measurement location, averaging interval, and observation window. §5 says ambient temperature is not battery temperature. §10 separates instantaneous power, energy, and averaged power. The only canonical measurement is `observation_type = measurement` plus `value` and a free-text `unit`. Subject type does not encode a meter, or a vehicle report of charger power, and two Celsius values on the vehicle cannot be told apart. Because §3.2 says no section may restate the record, an implementer cannot add these qualifiers beside it. The slow-charging comparison C8 added therefore cannot be computed from the observation the spec allows, and a wrong pairing is a false slow-charging diagnosis.
- **Proposed change:** On measurement observations, require a versioned `measurement_kind` with an allowed unit. Power kinds carry `measurement_location` (`vehicle_reported`, `charger_reported`, `meter`, `unknown`), `aggregation` (`instantaneous`, `average`, `energy`), and for an average the window start and end. Temperature kinds distinguish battery temperature from ambient temperature. A comparison whose required kind or qualifier is `unknown` returns `insufficient_evidence`. These fields belong to the §3.2 record. Add a fixture with two Celsius readings of different kinds and two kW readings at different locations and aggregations, and require that neither pair is substitutable.
- **Evidence:** reasoning only; local §3.2 against §5, §6.4, and §10. This is the same schema hole as the other round-2 measurement finding; the wording here is independent.
- **Confidence:** high.

### GROK-4 · The AFIR dates are confirmable, and "about a minute" is looser than the rule

- **Section:** §14, §15 [S6]
- **Type:** error
- **Severity:** minor
- **Finding:** §14 still says the 14 April 2025 and 14 April 2026 dates, and the one-minute freshness figure, come only from secondary sources and must not be relied on. Commission Implementing Regulation (EU) 2025/655 states them as law. Recital (1) says Article 20(2) of Regulation (EU) 2023/1804 requires operators, by 14 April 2025, to make static and dynamic data available at no cost, and that Member States make that data accessible through national access points under Article 20(4). Article 1(1)(b) requires the DATEX II model, at least CEN/TS 16157-10:2022, from 14 April 2026. Article 2 requires dynamic data to be updated no later than one minute after a change, and static data no later than twenty-four hours. "About a minute" is weaker than that duty. The base-regulation HTML was not re-fetched in this session; the implementing regulation, which quotes Article 20(2) and sets the format and frequency, was.
- **Proposed change:** In §14 and [S6], cite Regulation (EU) 2023/1804 Article 20(2) and 20(4) via Implementing Regulation (EU) 2025/655 recital (1), cite Article 1(1)(b) for the 14 April 2026 DATEX II duty, and cite Article 2 for "no later than one minute" (dynamic) and "no later than twenty-four hours" (static). Delete the sentence that these dates are secondary-only. Keep the existing limit: NAP data is operator-reported status, not internal diagnostics. Add `https://eur-lex.europa.eu/eli/reg_impl/2025/655/oj` beside [S6], retrieved 2026-10-14.
- **Evidence:** [Commission Implementing Regulation (EU) 2025/655](https://eur-lex.europa.eu/eli/reg_impl/2025/655/oj/eng), recital (1), Articles 1(1)(b), 2, and 5, checked 2026-10-14. EUR-Lex HTML for Regulation (EU) 2023/1804 itself timed out on this pass.
- **Confidence:** high on the implementing regulation; the base article is cited through that regulation rather than re-read.

### GROK-5 · State F is not the IEC 61851-1 error state the parenthetical describes

- **Section:** §4.5
- **Type:** error
- **Severity:** minor
- **Finding:** The `IEC61851_CP_STATE` bullet says "state F is an error state" and does not mention state E. A vendor summary of IEC 61851-1 distinguishes them: state E is the error state (0 V; utility problem or pilot short to earth), and state F is EVSE not available (−12 V), for example during maintenance. Both mean energy is not delivered. Naming only F as the error will mis-file a state-E fault and will treat a deliberate state-F outage as the same condition. The IEC standard text was not opened.
- **Proposed change:** Replace the parenthetical with: "States A–D are the normal connection sequence. State E is the error state (pilot short or utility power unavailable). State F means the EVSE is not available, for example maintenance. Neither state is energy transfer. Do not treat a displayed letter as one of these states until the source of the letter is identified." Do not add voltages or clause numbers to the spec until the IEC text is checked.
- **Evidence:** [Beckhoff, IEC 61851 low-level communication](https://infosys.beckhoff.com/content/1033/el6761/18724365579.html), state table, checked 2026-10-14. Vendor summary, not IEC 61851-1.
- **Confidence:** medium.

## Top 3

1. **GROK-1:** Put Plug & Charge authorization before parameter negotiation, and add a PWM-only AC path that does not require high-level communication.
2. **GROK-2:** Key OCPP 2.0.1 faults by component, variable, and optional tech code. The prose mention of `NotifyEvent` does not do that.
3. **GROK-3:** Give measurement observations a quantity kind and the location and aggregation qualifiers the slow-charging rule already assumes.

FB-D1–FB-D7 stay open HUMAN decisions. I have no new evidence on market, clearance policy, emergency stop, lawful basis, offline degradation, photo retention, or the base-rate ranking choice.

Result: complete
