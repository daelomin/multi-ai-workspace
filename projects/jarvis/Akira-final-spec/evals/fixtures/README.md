# Fixture notes

Representative records for schema tests, golden-file tests and export/restore tests.
Identifiers are shortened for readability (`task_T142`, `use_T142_2`) but keep the typed
prefix convention; production ids are ULIDs. Amounts are illustrative and internally
consistent with the worked example in `docs/09-accounting.md` §4.

v0.7 aligns route permission snapshots and skill predicates, action logical/provider keys
and retry links, and globally namespaced usage source identity/revisions. All examples
are synthetic. API permission remains unknown where no permission check is evidenced;
subscription permission uses AKIRA-D5's assumed-for-personal-use, never invented vendor
verification. Embedded Task.cost intentionally omits query-only byCategory/failedAttempts;
T-09 defines the required drill-down and infrastructure/multi-currency contract cases.
Earlier draft-shape migration handling is in docs/05 §7.
