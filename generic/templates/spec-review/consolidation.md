You are CLAUDE, the consolidator of the {NAME} spec review. Read {REL_PROJECT}/README.md, spec.md (v{version}), reviews/round-{previous}/CONSOLIDATION.md if it exists, and the round-{n} reviews: {files}.

Consolidate round {n} the same way as reviews/round-1/CONSOLIDATION.md: write reviews/round-{n}/CONSOLIDATION.md (accepted and merged, decisions for HUMAN, rejected or deferred with reasons, traceability of every finding), and update spec.md to the next minor version (bump the version line and date). Keep open HUMAN decisions in one carried-forward list with their project-specific decision IDs; HUMAN is not answering during the automated spec review, so do not wait for decisions and do not decide them yourself. {final}

{decisions}Also add a CHANGELOG.md entry at the top (Agent: CLAUDE). Do not run git: the loop commits and pushes for you. Only edit spec.md, README.md, CHANGELOG.md and the CONSOLIDATION.md file.{provenance}
