# Signoff Ledger — F####-{slug} run {run-id}

> Required at G5 per §10. Strictly consistent with `STATUS.md` current signoff state (latest row per `(story, role)`). PM-owned.

## Required Role Matrix

Echo the STATUS.md `Required Role Matrix` table for this feature.

| Role | Required |
|------|----------|
| Quality Engineer | Yes |
| Code Reviewer | Yes |
| Security Reviewer | <Yes/No based on §7 scope> |
| DevOps | <Yes/No> |
| Architect | <Yes/No> |

## Current Signoff State

Latest passing row per `(story, role)` derived from STATUS.md provenance. Validator cross-checks `signoff_ledger_stale_fails` against STATUS rows.

```text
- F####-S0001 / Quality Engineer: PASS by <reviewer> on YYYY-MM-DD (test-execution-report.md)
- F####-S0001 / Code Reviewer: APPROVED by <reviewer> on YYYY-MM-DD (code-review-report.md)
```

## Recommendation Acceptances

Mirror or cross-reference each `WITH RECOMMENDATIONS` row from STATUS.md. Where this run's `pm-closeout.md` carries the canonical PM Acceptance Line, summarize it here.

## Waivers And Omissions

List every entry from `manifest.omissions[]` and `manifest.waivers` with the human-readable rationale. Per §18, omissions are only allowed for non-required artifacts.
