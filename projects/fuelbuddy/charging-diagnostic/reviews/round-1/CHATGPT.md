# CHATGPT review — round 1

**Specification:** FuelBuddy AI Charging Diagnostic System v0.2, 11 October 2026.
**Reviewer:** CHATGPT. **Date checked:** 2026-10-11.
**Method:** Independent review of the local spec; no other round-1 review was read. The requested GitHub README could not be fetched, so its local copy was used (checkout `cc5642c`). Primary sources S1–S3 and NHTSA's recall lookup explanation were opened separately. This review proposes changes; safety policy, scope, and privacy decisions remain with HUMAN.

The spec establishes useful boundaries around uncertain evidence, generic errors, source approval, and driver permissions. The main remaining implementation risks are incomplete safety transitions, asynchronous evaluation, and contracts that cannot enforce the promised output behavior. Findings below distinguish internal reasoning from externally checked facts. The stop rule is not met: there are **2 blocking, 12 major, and 1 minor findings**.

### CHATGPT-1 · Reported hazards and safety clearance need explicit rules

- **Section:** §3.2, §5, §12
- **Type:** gap
- **Severity:** blocking
- **Finding:** The ground/insulation-fault row requires a confirmed fault, but manual observations are often merely reported, and the spec does not say how reported damage, unreadable warnings, or conflicting hazard evidence affect action permission. It also lacks a rule for clearing a previously observed hazard; a later successful handshake or missing warning could otherwise restore retries without addressing it.
- **Proposed change:** Add, subject to HUMAN approval: "The safety engine maintains a typed state with matched rule IDs, affected vehicle/equipment scope, triggering observation IDs, and clearance conditions. Credible reports of damage or a potentially safety-related warning suspend retry and alternate-charging recommendations pending the relevant approved triage playbook; a generic unclassified error alone does not establish a hazard. Missing or contradictory observations do not clear an active restriction. Each restriction can be cleared only by evidence and an actor authorized by its approved rule; a successful charging session does not itself clear it." Add regression cases for reported damage, ambiguous warning text, and later contradictory observations.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-2 · Stale evaluations can restore obsolete actions

- **Section:** §2, §5, §9.2, §11
- **Type:** risk
- **Severity:** blocking
- **Finding:** Reevaluation after new observations is required, but neither response ordering nor invalidation of an in-flight LLM result is specified. A retry response for revision 1 can arrive after a hazard observation creates revision 2, and both responses could satisfy validation against their own inputs.
- **Proposed change:** Add: "Every accepted observation or context correction increments a session revision. Evaluations carry evaluation_id, input_revision, evaluated_at, relevant knowledge/rule versions, and action validity conditions. Before publication and before displaying an actionable response, require that its revision and permissions remain current; otherwise suppress it and reevaluate. The client invalidates older actions immediately upon reporting a hazard or changing the selected vehicle/connector, and displays approved pending guidance. Hazard handling must not wait for LLM completion." Test concurrent observations, delayed responses, and reconnecting clients.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-3 · Approved action IDs do not constrain free-form instructions

- **Section:** §2, §9.1–§9.2, §12
- **Type:** gap
- **Severity:** major
- **Finding:** The output includes free-form summary, questions, escalation, and limitations, while the validator promises to reject unsupported facts and unauthorized actions. An output can list only CONTACT_OPERATOR yet add an unapproved reset or unplug instruction in its summary; membership checks on action IDs cannot establish semantic compliance of that prose.
- **Proposed change:** Replace the executable-guidance contract with: "Driver actions, safety warnings, escalation instructions, and questions requesting physical intervention are rendered from approved versioned text and validated parameters. The LLM returns references to these items and a structured explanation whose claims reference supplied observations or assertions. It cannot add or rewrite executable instructions. If optional narrative cannot be validated to this contract, omit it and render the deterministic explanation." Add adversarial cases containing an unauthorized action only in summary, question, or escalation text, including localized outputs.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-4 · Observation identity, correction, and time semantics are missing

- **Section:** §3.2–§3.3, §9.1, §11
- **Type:** gap
- **Severity:** major
- **Finding:** Candidates reference supporting_observation_ids, but the required observation envelope has no observation_id, subject, measurement type, or session-attempt association. Immutable observations also have no correction relation, leaving a mistaken photo transcription and its corrected value equally active; timestamps alone do not resolve which evidence belongs to a retry or a different connector.
- **Proposed change:** Extend the envelope with observation_id, session_id, attempt_id where applicable, subject_type/subject_id, observation_type, and optional corrects_observation_id. Specify UTC timestamps, nullable observed_at when unknown, timestamp origin/precision, and received_at assigned by the service; never substitute receipt time silently for event time. Define a versioned effective-observation view that preserves corrections and contradictions for audit, while excluding superseded transcription values from active matching. Validate subject/session ownership and evidence references.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-5 · Applicability predicates need three-valued evaluation

- **Section:** §4.2, §4.4, §4.6, §6.1
- **Type:** gap
- **Severity:** major
- **Finding:** Build ranges, equipment predicates, software ranges, and compatibility predicates are named but their evaluation semantics are unspecified. Treating null equipment as absent, comparing software versions lexically, or treating a partial voltage overlap as sufficient compatibility can produce confident but unsupported matches.
- **Proposed change:** Add: "Applicability predicates use a typed, versioned grammar and evaluate to true, false, or unknown. Unknown required equipment, build date, software, or electrical capability cannot satisfy a positive or negative predicate. Software comparison uses the issuer's documented ordering rather than generic string ordering. Compatibility requires a documented feasible operating point under all relevant constraints, including conversion and adapter limits; nominal voltage or interval overlap alone is insufficient. Conflicting applicable assertions return conflicting_evidence unless an approved precedence/supersession rule resolves them." Include boundary and null cases in §12.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-6 · Ranking lacks an actionable abstention contract

- **Section:** §1.1, §6.2–§6.3, §9.2, §12
- **Type:** gap
- **Severity:** major
- **Finding:** Abstention is a general requirement, but explicit unsupported-configuration handling appears only in the later probabilistic model, and the MVP has no decision_status or computable evidence-strength definition. Different implementations can label the same sparse evidence strong or present the top weak candidate as the probable diagnosis.
- **Proposed change:** Add a versioned MVP decision policy with decision_status values supported_hypothesis, insufficient_evidence, conflicting_evidence, and unsupported_scope. Define evidence-strength rules, tie handling, score contributions, and validated thresholds before pilot release; do not invent numeric thresholds in the spec. Require the output to include decision_status and reasons, allow an empty ranked list, and route abstention to approved questions/escalation rather than a component-specific recommendation. The supported scope manifest must identify market, variants, modes, station families, and action coverage, including what general guidance is still available outside it.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-7 · Slow-charging model and measurement contract are absent

- **Section:** §4.2–§4.3, §6.4, §12
- **Type:** gap
- **Severity:** major
- **Finding:** The existing FuelBuddy charging model is a dependency without an interface, version, applicability description, or failure behavior in this spec. The listed schema also lacks explicit fields for several required inputs, such as phase configuration, measurement location, averaging interval, battery temperature, and charging-curve provenance; charger output and battery-reported power could therefore be compared as though they measured the same quantity.
- **Proposed change:** Add a charging-model interface specifying model_version, applicable configuration, required/optional observations, input provenance, measured power location and averaging interval, and an expected power envelope with its uncertainty and applicability. Define how optional observations are represented in the observation_type catalog. Model failure or missing required inputs returns insufficient_evidence; no peak-power substitution. Define a validated observation window and deviation rule before classifying slow charging, and test ramp-up, taper, shared allocation, and incompatible measurement boundaries.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-8 · Retry bounds have no persistent action ledger

- **Section:** §3.3, §4.7, §5, §9.1, §11
- **Type:** gap
- **Severity:** major
- **Finding:** Playbooks specify maximum retries, but repeat_count does not identify which permitted action was attempted, on which equipment, or under which playbook version. Reevaluation, switching devices, or starting a new diagnostic session could repeatedly offer the first retry; the action IDs supplied to the LLM also have no defined registry connecting them to playbook permissions.
- **Proposed change:** Add a versioned action registry linking action_id to playbook_id/version, actor, approved localized text, parameters, prerequisites, hazards, and retry-budget scope. Record action recommendations and reported attempts with action_id/version, attempt_id, subject, timestamps, outcome, and confirmation quality. Consume and evaluate retry budgets across the scope specified by the playbook; changing sessions or clients must not silently reset a known exhausted budget. Ask for prior attempt history when unavailable and use a HUMAN-approved conservative policy for unknown history. Define handling of multiple applicable playbooks and incompatible action orders.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-9 · Recall state must be per campaign and preserve lookup limitations

- **Section:** §4.4, §5, §9.1, §14
- **Type:** gap
- **Severity:** major
- **Finding:** The individual-vehicle recall state is described without an explicit vehicle–campaign relation, and the LLM example uses a single recall_status; completion of one campaign could conceal another open campaign. NHTSA says its VIN results omit repaired recalls, some recently announced recalls, and international vehicles, so a negative lookup cannot establish either campaign completion or global non-applicability.
- **Proposed change:** Add vehicle_campaign_status keyed by vehicle_instance_id and campaign_id, with status, checked_at, source reference, lookup scope/limitations, and supersession history. Require positive campaign-specific evidence for confirmed_completed and a justified applicability assessment for not_applicable. A no-result or zero-unrepaired result remains unknown for a campaign unless additional evidence resolves it. Replace the LLM's scalar recall_status with relevant campaign records and explicitly derived restrictions; a completed campaign does not establish absence of a current component fault.
- **Evidence:** [NHTSA recall search, “What won’t the license plate and VIN search show?”](https://www.nhtsa.gov/recalls), checked 2026-10-11; schema and proposed handling are reasoning only.
- **Confidence:** high

### CHATGPT-10 · Error mapping key omits the message field it must preserve

- **Section:** §4.5, §7.1, §9.1
- **Type:** inconsistency
- **Severity:** major
- **Finding:** The text requires exact message fields, but the mapping key and JSON observation omit message_type and field_path. OCA distinguishes OCPP 1.6 StatusNotification errorCode from its vendorErrorCode, and OCPP 2.0.1 NotifyEvent techCode; an OCPP namespace and raw string alone do not preserve these distinctions.
- **Proposed change:** Extend protocol observations and mapping identity with message_type, field_path, identifier_scheme, and issuer/vendor scope as applicable. Preserve station/EVSE/connector or component scope and source event identity separately from the lookup key. Distinguish protocol-standard mappings from product/firmware-specific mappings: an approved standard-field mapping may match a known protocol version with unknown firmware, but a vendor mapping requiring firmware confirmation must not. Update the example to identify StatusNotification.errorCode and include its observation reference.
- **Evidence:** [Open Charge Alliance, Improving Uptime Monitoring with OCPP v1.2](https://openchargealliance.org/wp-content/uploads/2024/08/improving_uptime_with_ocpp_v1_2.pdf), §4.1.3, §4.2.4, and §6.1, checked 2026-10-11; proposed key design is reasoning only.
- **Confidence:** high

### CHATGPT-11 · Evidence approval and offline validity are not propagated

- **Section:** §4.1, §4.7, §9.2, §12–§14
- **Type:** risk
- **Severity:** major
- **Finding:** Approved records can become superseded or unusable, but the spec does not define whether dependent assertions, safety rules, and playbooks are invalidated together. Offline guidance and fallback are required without specifying cached package validity, so a withdrawn retry playbook could remain actionable in a cached app.
- **Proposed change:** Add dependency-aware activation: a production assertion/playbook requires all required evidence and approvals to be currently usable under its approved policy. Releases are immutable manifests of rules, evidence, playbooks, and supported scope, with integrity checks, review dates, validity policy, rollback target, and revocation handling. Validate fallback permissions against the same current safety state as normal output. Subject to HUMAN approval, when offline validity cannot be established, offer only the approved minimal emergency/contact guidance and disclose unavailable diagnostic evidence; do not erase known restrictions. Test evidence withdrawal and expired offline packages.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-12 · Read authorization and provider identity must be explicit

- **Section:** §10–§11
- **Type:** gap
- **Severity:** major
- **Finding:** Authentication and authorization are expressly required only for mutations, although GET exposes sensitive diagnostic state. Neither partner-ingestion authority nor actor verification for operator/dealer-confirmed outcomes is defined; merely storing an actor field lets an ordinary user assert an independently confirmed label.
- **Proposed change:** Replace the API security sentence with: "All reads and writes require authentication and object-level authorization to the session, vehicle, observations, evidence attachments, and outcomes. Partner events require an authenticated provider identity and authorized mapping to the relevant subject/session. Confirmation labels distinguish user-reported service statements from authenticated or reviewer-verified operator/dealer evidence; unverified actor text cannot assign independently confirmed status. Apply least privilege, rate limits, access audit, and explicit attachment access controls." Add cross-account read/write and forged-provider/outcome tests.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-13 · Sensitive content can bypass structured-field exclusions

- **Section:** §3.2, §9, §10, §12
- **Type:** risk
- **Severity:** major
- **Finding:** Excluding full VIN and credentials from named fields does not cover their appearance in screenshots, raw error text, OCR, retrieved documents, or diagnostic logs. The photo-input path does not specify where transcription occurs or whether images and extracted text cross the LLM boundary before redaction.
- **Proposed change:** Add: "Define the data boundary for photo processing, OCR, retrieval, and explanation separately. Construct LLM payloads from an allowlisted minimal projection of authorized session data, and apply sensitive-content detection/redaction to free text and images before any relevant external model call. If safe processing cannot be established, ask for a manual sanitized transcription. Apply the same exclusions to prompts, traces, analytics, fallback diagnostics, and error logs; restrict original uploads independently." Before launch, HUMAN must approve purposes, recipients, retention/deletion behavior including derived stores, and the chosen photo-processing flow.
- **Evidence:** reasoning only; this is a proposed engineering requirement, not a legal determination.
- **Confidence:** high

### CHATGPT-14 · Release gates lack a reproducible evaluation definition

- **Section:** §12–§13
- **Type:** gap
- **Severity:** major
- **Finding:** Passing all curated safety cases is useful only if case coverage, expected behavior, and approval responsibility are specified. Diagnostic metrics also lack denominators and confirmation criteria, and repeated sessions or copied reports from the same incident could leak into both development and validation sets despite the ranking warning about correlation.
- **Proposed change:** Require a versioned release evaluation manifest specifying supported scope, cases and expected permitted/forbidden actions, provenance, adjudicators, unresolved labels, segment coverage, and mandatory gates. Group related incidents/vehicles/source reports when splitting development and held-out evaluation data; report unresolved-case coverage and confirmation quality separately. Define each metric's denominator and treatment of abstentions and unconfirmed outcomes. HUMAN approves case coverage and pilot thresholds before release; an aggregate pass cannot override a failed mandatory safety/privacy case. Include concurrency, corrections, reported hazards, offline expiry, and unauthorized prose from this review.
- **Evidence:** reasoning only.
- **Confidence:** high

### CHATGPT-15 · Source-backed examples must retain their verification boundary

- **Section:** §7.1, §15
- **Type:** risk
- **Severity:** minor
- **Finding:** The checked Hyundai notice supports the listed model years and campaign, and the checked Mercedes page supports the published converter qualification, but neither is evidence of a particular vehicle's current campaign state or converter fitment. The Mercedes page still phrases spring 2026 availability prospectively; checking it on 11 October 2026 does not independently confirm actual delivery or universal fitment from that date.
- **Proposed change:** Rename §7 to "Illustrative sourced examples and unresolved claims" and record a source locator, retrieval date, assertion status, and the exact scope for each example. For the CLA, phrase the date as the manufacturer's published availability statement, with actual availability/fitment requiring current configuration evidence. For Hyundai, retain the notice's specific campaign scope and do not infer an ICCU diagnosis, charging ban, or completed remedy from model/year. Require these distinctions in seed-import validation and example-output tests; examples remain inactive until structured review approval.
- **Evidence:** [Hyundai owner notice, NHTSA 24V-868 / Hyundai 272](https://static.nhtsa.gov/odi/rcl/2024/RCONL-24V868-8658.pdf), pp. 1–2, and [Mercedes-Benz USA 2026 CLA page](https://www.mbusa.com/en/future-vehicles/2026-mercedes-benz-cla-sedan), charging description and converter FAQ; both checked 2026-10-11. Interpretation of verification limits is reasoning only.
- **Confidence:** high

## Top 3

1. **CHATGPT-1:** Make safety state, treatment of reported hazards, and clearance conditions explicit before permitting retries.
2. **CHATGPT-2:** Bind evaluations and displayed actions to the current session revision so delayed responses cannot restore obsolete permissions.
3. **CHATGPT-3:** Render executable guidance from approved content; action-ID membership cannot validate arbitrary LLM instructions.
