# GROK review — round 2

Reviewed local `spec.md` **v0.2** (2026-10-21) after `README.md`, all three round-1 reviews, and `reviews/round-1/CONSOLIDATION.md`. Round-2 `CHATGPT.md` and `DEEPSEEK.md` were already present and were read. Counts: **0 blocking, 0 major, 8 minor**. FB-D1–FB-D6 stay open and are not re-raised. Accepted round-1 items are not re-opened; the findings below are residual holes in the merged text.

I agree with CHATGPT-1, CHATGPT-2, and CHATGPT-3, and with DEEPSEEK-1 through DEEPSEEK-7. Those stay under their ids. GROK-3 and GROK-8 add datasheet constraints to the payload-boundary and allowlist points those reviews already raised.

### GROK-1 · An expected-response count is a cap and can drop ECUs

- **Section:** §7 (also §5, §14)
- **Type:** gap
- **Severity:** minor
- **Finding:** §7 makes "shorter timeouts and expected-response counts" part of adapter validation, beside the default 200 ms / about 4 queries/s ceiling. On an ELM327 the extra hex digit is the maximum number of responses to obtain, and a digit below the real number returns to the prompt early, so later responders are not delivered. Adaptive timing also treats `AT ST` as a maximum and is described as learning the slower ECU's time; a timeout shortened under the slower responder has the same effect. §5 still requires every responder to a functional request to be kept. The spec never says the cap has to be measured first and then set to that measured number.
- **Proposed change:** Add to §7: "An expected-response count is a maximum, not a hint. Measure how many responses actually arrive for that request, then set the count to that number. A count below the measured number is forbidden, because the adapter returns early and the missing responders are dropped. A shortened response timeout stays at least as long as the slowest responder already observed for that request. Until that measurement exists, wait for the adapter prompt with the default timeout and do not send a count digit. The two-ECU acceptance fixture fails if either ECU is absent because the count or the timeout expired first."
- **Evidence:** Elm Electronics, ELM327 datasheet (copyright 2005 to 2020), https://www.elmelectronics.com/wp-content/uploads/2020/05/ELM327DSL.pdf, checked 2026-10-21. "Talking to the Vehicle": the extra hex digit is "the maximum number of responses to obtain"; a number that is too small makes the adapter "return to the prompt too early". "Setting Timeouts": if the digit "is less than the actual number of responses", required acknowledgements may not be sent; "always determine the number of responses that will be coming from the vehicle, and then set the responses digit to that value." Same section: adaptive timing "always uses your AT ST hh setting as the maximum", and the transmission "takes considerably longer" than the engine controller. The 200 ms / about 4 queries/s sentence matches this datasheet's own example.
- **Confidence:** high

### GROK-2 · Response pending is a wait, not a finished negative

- **Section:** §5 (also §7)
- **Type:** error
- **Severity:** minor
- **Finding:** §5 maps every response whose service byte is `7F` to `Negative` and treats that as the end of the exchange. A response of the form `7F xx 78` means the ECU is busy: the scan tool is supposed to keep waiting, and a further pending response extends the wait. Ending the exchange at the first `7F` discards the positive payload that follows. The same datasheet says its own pending handler does not track multiple ECUs, so a good reply from one ECU can be taken as the end of another ECU's pending wait.
- **Proposed change:** In §5, replace the blanket `7F` rule with: "A normalised response `7F <requested service> <code>` is `Negative` when the code is anything other than `0x78`. Code `0x78` (response pending) does not finish the exchange and does not become a sample: keep waiting for a later positive, negative, or timeout from that same responder, up to one bounded wait, and extend that wait once if the same responder sends `0x78` again. A positive payload from one responder does not cancel a pending wait on another. `Negative.code` is that third byte, and the second byte must equal the service that was requested."
- **Evidence:** Same ELM327 datasheet, "Response Pending Messages", checked 2026-10-21. It states a pending reply "will always be of the form: 7F xx 78", that the scan tool should wait up to 5 seconds and extend that wait if another pending reply arrives, and that the chip "does not keep track of multiple ECUs", so "a good reply from one ECU" may end "the Response Pending condition established by another". The 5-second figure is the datasheet's statement about J1979; this review does not cite a clause number.
- **Confidence:** high

### GROK-3 · Headers-on leaves the PCI byte in front of the service byte

- **Section:** §5
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 allows "headers on, or physical addressing", then checks "the response service byte" against the request service + `0x40`. With CAN auto-formatting on, the ELM327 removes the ISO-TP PCI byte on receive only while headers are off. Headers-on, the configuration §5 uses so the responder is visible, leaves that PCI byte in the line ahead of the service byte. The same valid reply therefore has its service byte at a different index in the two configurations §5 both allow, and a `7F` check on the wrong index misses a negative response. This is the same hole as DEEPSEEK-7; the datasheet pins down which configuration includes the PCI byte.
- **Proposed change:** Add to §5: "`Payload.bytes` is the reassembled OBD payload for one responder, response service byte at index 0. The transport moves the responder address into `source`, removes the ISO-TP PCI byte (present in the adapter text when headers are on, even if CAN auto-formatting is on), and concatenates multiline frames for that responder before the service check. The `+ 0x40` test and the `7F` test both use that normalised byte 0. Raw adapter lines are not stored in `bytes`."
- **Evidence:** Same ELM327 datasheet, "CAN Message Types", checked 2026-10-21: with auto-formatting on (CAF1) the chip "remove[s] it for you when receiving. (If the headers are enabled, you will see it in the responses.)" PCI is "always the first of the data bytes".
- **Confidence:** high

### GROK-4 · Responder identity is specified only for 11-bit CAN

- **Section:** §5 (also §4, §7)
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 defines a functional request as CAN `7DF` and responders as `7E8`–`7EF`. An ELM327 automatic search also selects 29-bit ISO 15765-4 and the non-CAN protocols, and the datasheet's example of an OBD reply filter for the engine on 29-bit CAN is `18 DA F1 10`, which is outside `7E8`–`7EF`. A parser that only accepts `7E8`–`7EF` marks those responders `ambiguous` or drops them. §7 then caches capability per "protocol + ECU" using an address the identity rule cannot name.
- **Proposed change:** Add to §5: "Phase 1 records the protocol the adapter actually negotiated. On 11-bit ISO 15765-4 the functional request is `7DF` and responders are `7E8`–`7EF`. On 29-bit ISO 15765-4 the responder address is the 29-bit id the adapter reports (the datasheet's engine-reply example is `18 DA F1 10`), not a value in `7E8`–`7EF`. On non-CAN protocols the responder is the source byte of the header. An address that does not match the negotiated protocol is `ambiguous`. If Phase 1 support is later limited to 11-bit CAN, other negotiated protocols are refused at connect and are not parsed as `7E8`."
- **Evidence:** Same ELM327 datasheet, checked 2026-10-21. "Selecting Protocols": `AT SP 0` searches automatically; Figure 2's listed protocols include "ISO 15765-4 CAN (11 bit ID, 500 kbaud)", "ISO 15765-4 CAN (29 bit ID, 500 kbaud)", and the 250 kbaud 11-bit and 29-bit lines. "CAN Receive Filtering": "to see only the OBD replies sent by the engine to the scan tool" the example command is `AT CRA 18 DA F1 10`. This review does not add a 29-bit functional request id; the fetched pages did not state one.
- **Confidence:** high

### GROK-5 · A positive service byte does not identify which PID came back

- **Section:** §5 (also §6, §7)
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 accepts a payload as `valid` when the response service byte equals the request service + `0x40`. For service `01` the byte after that is the echoed PID. The ELM327 also accepts several PIDs in one request, and it states that the PIDs in the reply do not have to appear in the request order. A decoder that trusts the service byte and then reads values in request order assigns one PID's bytes to another PID's metric. Separately, the Phase 1 list says "short/long-term fuel trims" as one item, while the public PID table defines bank 1 and bank 2 as different PIDs (`06`/`07` and `08`/`09`).
- **Proposed change:** Add to §5: "For service `01`, a payload is `valid` only if the service byte matches and every data value is taken from a PID that this request asked for, using the echoed PID byte in the response, not the position of the PID in the request. A returned PID that was not requested is `error` and is not decoded. One request may ask for several supported PIDs; each echoed PID becomes its own sample. Bank 1 and bank 2 fuel trims stay on separate `metric_key`s (`06` and `08` short-term, `07` and `09` long-term) and are never averaged."
- **Evidence:** Same ELM327 datasheet, "Talking to the Vehicle", checked 2026-10-21: in `41 00 …` "the second number (00) repeats the PID number requested." "CAN Message Types" shows a multi-PID request and says "the order in which the PIDs appear in the response does not have to match the order in which they were requested." Wikipedia, "OBD-II PIDs", service 01 table, PIDs `06`–`09` (short/long-term fuel trim, bank 1 and bank 2), https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21. The provisional acceptance rates in FB-D6 are unchanged.
- **Confidence:** high

### GROK-6 · DTC padding, MIL, and occurrence count are not defined

- **Section:** §6 (also §5)
- **Type:** gap
- **Severity:** minor
- **Finding:** `DtcRecord` has a code, a MIL status, and an occurrence count. A mode `03` payload is a list of two-byte codes. The ELM327's non-CAN example is padded with `0000`, and those pairs are not trouble codes; storing them creates a false code. MIL and the number of stored codes come from mode `01` PID `01` (MIL is bit A7 of byte A; bits A6–A0 are how many codes are stored), not from the mode `03` bytes. That count is not a per-code occurrence count, and each module can report its own PID `01` line.
- **Proposed change:** Add to the `DtcRecord` paragraph: "Each DTC is two bytes, decoded to the five-character form: bits A7–A6 of the first byte are the category (00 P, 01 C, 10 B, 11 U) and the remaining 14 bits are the four hex digits. On a response padded with `0000`, those pairs are not records. `mil_on` is copied from that same responder's mode `01` PID `01` bit A7, not from the mode `03` payload. `occurrence_count` is how many Phase 1 recordings have observed this code for this vehicle and responder; it is not read from the ECU. PID `01` bits A6–A0 are the module's code count and are not stored as `occurrence_count`."
- **Evidence:** Same ELM327 datasheet, "Interpreting Trouble Codes", checked 2026-10-21: PID `01` byte example, "the most significant bit" is the MIL and "the other 7 bits of this byte provide the actual number of stored trouble codes"; a mode `03` example "padded with 00's" where "the 0000's do not represent actual trouble codes"; other modules "each could have provided a line of response." Wikipedia, "OBD-II PIDs", checked 2026-10-21: PID `01` bit A7 is MIL and bits A6–A0 are the number of confirmed emissions-related DTCs; service 03, each code is two bytes with category in A7–A6.
- **Confidence:** high

### GROK-7 · Progress text is not an adapter failure, and one failure word is missing

- **Section:** §5
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 maps a fixed list of adapter words to `AdapterError`. During an automatic protocol search the ELM327 prints `SEARCHING...` and then the real reply. A parser that treats every unlisted word as a hard error, and then discards the rest of the exchange, throws away that reply. `BUS INIT: ...` followed by `OK` is the same kind of progress text on ISO 9141 / ISO 14230 when auto-search is off. `LV RESET` is a real failure word from a low-voltage reset and it is not in the list, so it can fall through into `Payload`.
- **Proposed change:** Add to §5: "Lines that are only progress (`SEARCHING...`, `BUS INIT: ...`, and a following `OK`) are ignored and the exchange keeps reading until the prompt. `LV RESET` is an `AdapterError`. Any other non-hex line is `AdapterError`. A progress line never discards a later payload in the same exchange."
- **Evidence:** Same ELM327 datasheet, checked 2026-10-21. "Talking to the Vehicle": the chip says "`SEARCHING...`" and then prints the reply bytes. "Bus Initiation": "`BUS INIT: ...`" followed by "`OK`" or an error. Version history for v1.3: "Introduced LV RESET message for resets from low voltage."
- **Confidence:** high

### GROK-8 · Two adapter commands write the bus or EEPROM outside the service allowlist

- **Section:** §12 (also §4, §7)
- **Type:** risk
- **Severity:** minor
- **Finding:** §12's adapter-command clause is the purpose phrase "needed to connect and enable response headers" (DEEPSEEK-1). Two documented commands sit on the wrong side of a read-only guarantee. `AT SP` writes the chosen protocol to EEPROM immediately, before a vehicle has answered. `AT WM` replaces the bytes the chip itself transmits as a keepalive: the ISO 9141 default is a mode `01` request, and the ISO 14230 default is `C1 33 F1 3E` (service `3E`, which is outside `01`/`03`/`07`/`0A`). CAN protocols have no such periodic message. A wakeup payload is an adapter-local command that can carry a vehicle service the OBD allowlist would otherwise reject.
- **Proposed change:** Add to §12, as a constraint on the closed adapter-command set from DEEPSEEK-1: "Ordinary connect uses try-protocol (`AT TP`), not set-protocol (`AT SP`). Commands that write adapter EEPROM, including programmable-parameter writes, are rejected. The app never sends a wakeup-message command. On ISO 9141 and ISO 14230 the chip's own default keepalive may occur; its payload is not replaced. Any adapter command whose data bytes contain a vehicle service outside `01`, `03`, `07`, and `0A` is rejected. CAN Phase 1 sessions have no app-defined periodic message."
- **Evidence:** Same ELM327 datasheet, checked 2026-10-21. "Selecting Protocols": set-protocol "cause[s] an immediate write to the internal EEPROM"; try-protocol writes "only after a valid protocol is found, and only if the memory function is enabled." "Periodic (Wakeup) Messages" and "Bus Initiation": ISO 9141 default keepalive `68 6A F1 01 00`, ISO 14230 default `C1 33 F1 3E`, user replacement via the wakeup-message command, and "the ELM327 does not currently support periodic messages for the CAN protocols."
- **Confidence:** high

**Top 3**

1. **GROK-1** — a response-count digit or a shortened timeout returns before later ECUs reply, which undoes the merged per-responder rule.
2. **GROK-2** — `7F xx 78` is a wait; treating every `7F` as a finished negative drops the payload that follows.
3. **GROK-6** — padded `0000` pairs and PID `01`'s code count are not per-code DTC fields, so the record as written stores false codes or a false occurrence count.

Result: complete
