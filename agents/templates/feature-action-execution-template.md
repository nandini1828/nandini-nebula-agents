# Feature Action Execution — F####-{slug} run {run-id}

> Required at G6 per §10. Captures the orchestrator's per-gate execution log.

## Gate

Current/final gate reached: `G0` / `G1` / `G2` / `G3` / `G5` / `G6` / `G8` / `closeout`.

## Execution Timeline

For each gate transition, record:

- Timestamp (ISO 8601 with timezone)
- Gate entered
- Inputs consulted
- Validator invocations (with rule IDs, exit codes, evidence paths)
- Role outputs produced this gate
- Outcome (proceed / hold / rework)

Example:

```text
- 2026-05-19T10:15:00-04:00 — G0 entered
  - Inputs: agents/templates/feature-assembly-plan-template.md
  - Validators: validate-feature-evidence.py --stage G0 → exit 0
  - Outputs: g0-assembly-plan-validation.md (PASS)
  - Outcome: proceed to G1
```
