# CHATGPT review — round 3

Reviewed `spec.md` v0.5 after the round-2 reviews and consolidation and the round-1 consolidation, with `decisions.md`, all fifteen companion documents and all eight JSON fixtures in the manifest scope. AKIRA-D1–D6 remain fixed; U4–U16 are carried forward without new decision requests. The absent `assets/` directory is already recorded and is not raised again. This is a specification review, not verification of Akira or upstream runtime behaviour. Read-only checks confirmed JSON parsing, schema-version presence, task cost-subtotal arithmetic and matching task/checkpoint definition identity. No git commands, runtime integrations, installation, authentication, deployment or paid operations were run.

Findings: three minor; no blocking or major findings.

### CHATGPT-1 · Checkpoint backup output directory is never created
**Severity:** minor
**Finding:** `docs/12-operations.md` §5.2 creates a fresh `$GEN`, then writes each workspace's checkpoint-ref list and bundle under `$GEN/checkpoint-refs/` without creating that subdirectory. With the normal separate configuration and registry paths, nothing in the preceding steps creates it. Shell redirection therefore fails before the ref-list command runs, and bundle creation also lacks its destination directory. The subsequent file-based manifest cannot list files that were never created. This is a small remaining defect in N1's newly added checkpoint-export steps, rather than a repetition of the resolved source-tree merging or missing-backup-scope findings. The normative seven-item completeness gate still correctly prevents accepting such a generation.
**Proposed correction:** Create `$GEN/checkpoint-refs` before the workspace loop and require checked success for each ref-list/bundle operation before manifest completion. Define an explicit no-active-workspaces/no-checkpoint-refs result rather than treating a failed export as that case. Exercise T-13 with a fresh generation and at least one workspace containing checkpoint refs.
**Evidence:** `docs/12` §5.2 has `mkdir "$GEN"`, then redirection and bundle destinations under `$GEN/checkpoint-refs/`, with no creation of that child directory; §5.1 item 7 and T-13 require the checkpoint restore item. Static inspection only; no backup or git command executed.
**Confidence:** high

### CHATGPT-2 · Fault matrix mixes attempt outcomes with other result types
**Severity:** minor
**Finding:** `docs/10-tests-and-acceptance.md` §3 now requires every expected attempt outcome in the matrix to belong to `AttemptOutcomeClass`, but its column headed “Expected attempt outcome” still contains action state `unknown` (F-08), webhook result `idempotent ignore` (F-09), delivery transition `pending → delivered once` (F-10), watchdog activity (F-07), invariant rejection (F-14), no deletion (F-15), and quarantine `n/a` (F-16). These are sensible assertions about other components, but they are not attempt outcomes. A literal membership test cannot pass, and an implementer has to invent exceptions to distinguish non-attempt cases. N3 fixed the provider-error mappings; this remaining issue is the test contract's treatment of heterogeneous fault results.
**Proposed correction:** Separate a nullable attempt-outcome column from the component/state assertion, or give each row an explicit result kind. Apply enum membership only to actual attempt outcomes. In F-08, preserve the action-state assertion separately and state the expected interrupted attempt outcome if that scenario also grades restart recovery.
**Evidence:** `docs/10` §3 column heading, F-07–F-10 and F-14–F-16, and its final membership-test sentence; `docs/04-data-model.md` §4.2 defines the closed attempt-outcome set and §4.4 separately defines action states.
**Confidence:** high

### CHATGPT-3 · Integer currency minor units need a sub-cent accounting policy
**Severity:** minor
**Finding:** The unified `Money` representation in `docs/04-data-model.md` §1 and §5 stores each usage cost as integer currency minor units, but no rule explains how to retain or round smaller price-table estimates or provider charges. For a synthetic example, 100 turns costing USD 0.004 each total USD 0.40; rounding each turn to integer cents first yields zero, while rounding each up yields USD 1.00. That affects both task totals and route calibration even though each individual display looks plausible. N7 resolves the former shape mismatch, but does not resolve the precision boundary introduced by storing every turn in that shape.
**Proposed correction:** Specify one exact fixed-point/decimal representation with sufficient scale for per-record costs and price calculations, retaining the source amount where necessary; round to currency minor units at a documented aggregation/display boundary. Keep the representation consistent across costs and summaries and add the repeated sub-cent example to T-09. Do not invent more precise source data when the provider supplies only a rounded charge.
**Evidence:** `docs/04` §1 defines `amountMinor: integer` as currency minor units and prohibits stored decimals; §5 uses it on each `UsageRecord.cost`. `docs/09-accounting.md` §5 calculates estimates from tokens × price list, while AK-ACC-04/05/16 require honest, reconcilable totals usable for routing. The example is arithmetic over synthetic amounts, not a claim about current vendor pricing.
**Confidence:** high

Result: complete
