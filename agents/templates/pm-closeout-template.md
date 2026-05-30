# PM Closeout — F####-{slug} run {run-id}

> Required at G8/closeout per §10. PM-owned. Final approval artifact.

## Final Story Status

Per-story final status table. Each row references the STATUS.md current signoff and the evidence path.

| Story | Final Status | Evidence | Notes |
|-------|--------------|----------|-------|
| F####-S0001 | Done | test-execution-report.md / code-review-report.md | - |

## Archive Decision

State whether the feature is `Done`, `Completed`, or `Archived`. If archived, note the `Archived Date` (also recorded in `REGISTRY.md`).

## Deferred Follow-ups

Items the PM is explicitly deferring beyond closeout. Each has an owner and a ticket or target date.

## Recommendation Acceptances

Each accepted recommendation uses the §15 PM Acceptance Line Format:

```text
- Accepted: <identifier> — <type-specific details>
```

`<identifier>` examples:
- `coverage` — for a coverage waiver
- `<rule_id>` — for a validator_defect waiver (mirrored in `Validator Defects` subsection)
- `<recommendation text or ID>` — for a deferred role-report recommendation
- `<custom waiver key>` — for a product-specific waiver key

For `high`/`critical` recommendations, details must begin with `mitigation:` (case-insensitive).

## Tracker Updates

Confirm `REGISTRY.md`, `ROADMAP.md`, `STORY-INDEX.md`, `BLUEPRINT.md` were updated. Cite the `validate-trackers.py` invocation in `lifecycle-gates.log`.

## Validator Results

Summarize every validator run for this closeout — tracker, story-index, KG, template, feature-evidence — with exit codes and rule IDs. Mirror `lifecycle-gates.log`.

<!--
## Validator Defects (conditional)

Activate this subsection only when `manifest.waivers.validator_defect` is present. One acceptance line per affected rule ID:

- Accepted: <rule_id> — defect: <description>; target: YYYY-MM-DD
-->
