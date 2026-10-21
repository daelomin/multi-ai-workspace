# CHATGPT review — round 2

Reviewed local `spec.md` **v0.2** (2026-10-21), after reading all three round-1 reviews and `reviews/round-1/CONSOLIDATION.md`. Counts: **0 blocking, 0 major, 3 minor**. FB-D1–FB-D6 remain open and are not re-raised. The findings below concern residual inconsistencies in the merged text; they do not reopen the accepted safety or ECU-attribution requirements. Proposed identifiers are additions, not claims about existing implementation.

### CHATGPT-1 · Make the illustrative exchange result accommodate multiple responders

- **Section:** §5; §14
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The merged prose requires retaining every responding ECU, but `exchange(request): ObdResponse` can return only one `Payload` or one `Negative`, each with one source address. It cannot express two payloads, or a payload from one ECU and a negative response from another, for the same functional request. The normative behavior is clear, but an implementation following the illustrative signature would need to change the contract to satisfy the existing two-ECU acceptance fixture.
- **Proposed change:** Replace the illustrative return type with an exchange envelope containing a collection of per-responder outcomes and a separate exchange-completion status. State: “One exchange collects all responder outcomes until the adapter prompt or a bounded deadline; a failure or negative response from one responder does not discard another responder's valid payload. An incomplete exchange preserves completed responses with its completion status. The single-flight queue advances only once the channel is idle or has been recovered.” Extend the existing replay fixture to cover a positive and negative outcome in the same exchange.
- **Evidence:** reasoning only; comparison of the §5 sealed interface with its ECU-identity and single-owner paragraphs and §14's existing acceptance fixture. No external protocol claim is needed beyond the spec's own multiple-responder premise.
- **Confidence:** high

### CHATGPT-2 · Scope cached capabilities to the selected vehicle

- **Section:** §6; §7
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 scopes ECU addresses to the vehicle and protocol, but §7's explicit cache key is only adapter + firmware + protocol + ECU, and its rediscovery triggers do not explicitly include a selected-vehicle change. In the hypothetical case where one adapter is moved between two vehicles with the same protocol and ECU address, that key collides even when the supported PID sets differ. The existing per-ECU discovery requirement is correct; its cache rule needs to preserve the vehicle scope as well.
- **Proposed change:** Add `vehicle_id` to the capability-cache key and require rediscovery whenever the selected vehicle changes. State: “Cached capabilities are hints until validated for the current vehicle connection. If the current connection cannot be reliably associated with the cached vehicle, discover anew rather than reusing the cache as authoritative.” This uses the existing local vehicle identifier and does not require adding VIN reads or changing FB-D2.
- **Evidence:** reasoning only; the §6 vehicle identifier, §5 ECU-address scope, and §7 cache-key definition permit the described key collision without any assumption about a particular vehicle's PID support.
- **Confidence:** high

### CHATGPT-3 · Separate upload revocation from deletion of local recordings

- **Section:** §11; §14 Phase 2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The merged consent paragraph says revoking consent, disabling the module, or deleting telemetry “discards the matching samples in the database, the in-memory ring and the durable upload queue,” then says local recordings remain under the user's local policy. For upload-consent revocation or module disablement, these sentences give conflicting instructions about the same local recordings. The queue-cancellation requirement is already accepted; the remaining issue is the scope of local deletion, not entitlement expiry or the open storage-eviction policy.
- **Proposed change:** Replace the overlapping sentences with: “Revoking upload consent stops new dispatches, cancels pending retries, attempts to cancel in-flight transfers, and invalidates matching upload-queue entries; retained local recordings remain subject to the user's local policy. Disabling the module also stops acquisition without implicitly deleting retained recordings. An explicit telemetry-deletion request removes the requested records from local storage, the ring buffer and pending upload copies, and prevents retries from recreating them. Already accepted uploads require the disclosed cloud deletion flow.” Extend the existing revoke-while-offline test to verify that local recordings remain exportable while no revoked batch is dispatched; keep deletion-with-pending-retry as a separate case.
- **Evidence:** reasoning only; the two conflicting rules are adjacent in §11. This clarifies the spec's existing local-retention sentence and does not choose a new retention duration or eviction policy.
- **Confidence:** high

**Top 3**

1. Clarify whether upload revocation retains local recordings (CHATGPT-3).
2. Align the exchange result with the existing multiple-responder requirement (CHATGPT-1).
3. Include vehicle scope when reusing cached capabilities (CHATGPT-2).

Result: complete
