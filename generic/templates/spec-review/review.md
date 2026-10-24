Automated loop rules (they override anything in the README about git or pull requests):
- Write ONLY {review_path} and a new entry at the top of CHANGELOG.md (repository root, same format as the existing entries, Agent: {agent}). Do not edit spec.md or any other file.
- Do not run git, do not create branches, do not open pull requests: the loop commits and pushes your files for you as "{agent}: {name} spec review round {n}".
{decisions_rule}- HUMAN is not answering during the loop. Items already listed as open HUMAN decisions in the previous CONSOLIDATION.md must not be raised again as blocking or major findings; comment on them only if you have new evidence, as a `question` of severity `minor`.
- Severity discipline: `blocking` and `major` keep the loop running, so use them only for problems that would make the spec unsafe, wrong or unimplementable. Use `minor` for the rest.
- Do not repeat findings that the previous consolidation already accepted and merged, unless the merged text is still wrong.
- End the review file with a line `Result: complete`. If you have no findings, write a line `Findings: none` before it. A file without `Result: complete` is treated as unfinished.
- When the file is written, stop.
