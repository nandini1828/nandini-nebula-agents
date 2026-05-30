# Action: Feature Review

## User Intent

Independently review a completed feature and answer:

```text
Is this feature truly done?
```

This action is a post-feature completion audit. It does not replace the code,
security, signoff, closeout, tracker-sync, or feature-evidence gates inside
`feature.md`; it gives a fresh reviewer a focused way to challenge the completed
vertical slice before merge, release, or stakeholder acceptance.

## Agent Flow

```
(Product Manager + Architect + Quality Engineer + Code Reviewer + Security + DevOps*)
  v [Parallel Completion Review]
[SELF-REVIEW GATE: reviewers verify evidence-backed findings]
  v
[DONE GATE: Truly Done / Conditionally Done / Not Done]
  v
Feature Review Complete
```

`DevOps` runs when runtime, deployment, environment, CI, or infrastructure
artifacts changed, or when deployability evidence is missing or disputed.

**Flow Type:** Parallel read-only completion review with a done gate

---

## Reviewer Independence Contract

- Prefer running this action in a fresh session or different coding tool than
  the one that implemented the feature.
- Reviewers must inspect the completed feature artifacts, evidence package,
  current diff, and runtime evidence directly.
- The action is read-only except for writing the review report under the
  non-feature evidence run folder.
- Findings route back to `feature.md`, `review.md`, `test.md`, or targeted
  owning-role rework. Reviewers do not silently fix implementation or evidence
  artifacts while reviewing.

## Output Location

Write review outputs to the base/manual run evidence path:

```text
{PRODUCT_ROOT}/planning-mds/operations/evidence/{RUN_ID}/
```

Required output:

- `feature-review-report.md`

Recommended supporting outputs when useful:

- `commands.log`
- `artifact-trace.md`
- `gate-decisions.md`

This action reads feature evidence packages but must not write into them. The
canonical feature evidence package is owned by `feature.md` / `build.md`.

## Context Files

Load in this order when the work is feature-scoped:

1. `agents/ROUTER.md`
2. `agents/agent-map.yaml`
3. `agents/docs/AGENT-USE.md`
4. `agents/actions/feature-review.md`
5. `agents/actions/feature.md`
6. `{PRODUCT_ROOT}/planning-mds/features/F{NNNN}-{slug}/feature-assembly-plan.md`
7. `{PRODUCT_ROOT}/planning-mds/features/F{NNNN}-{slug}/**`
8. `{PRODUCT_ROOT}/planning-mds/operations/evidence/F{NNNN}-{slug}/latest-run.json`
9. `{PRODUCT_ROOT}/planning-mds/operations/evidence/F{NNNN}-{slug}/{FEATURE_RUN_ID}/**`
10. `{PRODUCT_ROOT}/planning-mds/knowledge-graph/solution-ontology.yaml`
11. `{PRODUCT_ROOT}/planning-mds/knowledge-graph/canonical-nodes.yaml`
12. `{PRODUCT_ROOT}/planning-mds/knowledge-graph/feature-mappings.yaml`
13. `{PRODUCT_ROOT}/planning-mds/knowledge-graph/code-index.yaml`
14. `{PRODUCT_ROOT}/planning-mds/knowledge-graph/coverage-report.yaml`
15. Source files changed by the feature under `{PRODUCT_ROOT}/engine/`,
    `{PRODUCT_ROOT}/experience/`, and `{PRODUCT_ROOT}/neuron/` as applicable

## On-Demand Paths

- `{PRODUCT_ROOT}/planning-mds/api/<openapi-spec>.yaml`
- `{PRODUCT_ROOT}/planning-mds/schemas/**`
- `{PRODUCT_ROOT}/planning-mds/security/authorization-matrix.md`
- `{PRODUCT_ROOT}/planning-mds/security/policies/policy.csv`
- `{PRODUCT_ROOT}/planning-mds/architecture/**`
- Runtime, CI, test, lint, scan, and coverage artifacts cited by the feature
  evidence package
- `agents/<role>/references/**` only after a matching `agents/ROUTER.md` row

## Primary Question

The review must answer whether the feature can be treated as actually complete:
requirements satisfied, implementation merged-ready, evidence trustworthy,
security acceptable, deployability proven, signoffs complete, and planning
trackers reconciled.

## Modes

- `closeout-audit` (default): run after `feature.md` G8 closeout and
  `latest-run.json` publication.
- `candidate-audit`: run after `feature.md` G6 candidate validation but
  before final closeout. In this mode, missing `latest-run.json` and final
  archive transitions are expected but must be listed as pending closeout items.

## Forbidden

- Editing implementation code, tests, feature docs, evidence packages, KG
  artifacts, trackers, or closeout files during the review.
- Treating a prior feature-action approval as proof that the feature is done.
- Approving from report summaries without checking raw evidence paths.
- Substituting global frontend/test lanes for feature-scoped role evidence.
- Ignoring uncommitted or unreviewed changed files in the feature diff.
- Declaring `TRULY DONE` while required evidence validation fails.
- Widening scope beyond the reviewed feature except to document discovered
  cross-feature impact.

## Stop Conditions

- The target feature or feature evidence run cannot be resolved.
- The feature evidence package is missing and the review is not explicitly in
  `candidate-audit` mode.
- The changed-file set cannot be identified from SCM, feature evidence, or an
  operator-provided diff range.
- Reviewers cannot cite concrete evidence for the done decision.

---

## Execution Steps

### Step 1: Resolve Feature Run And Diff

1. Identify `FEATURE_ID`, `FEATURE_PATH`, `FEATURE_RUN_ID`, and review mode.
2. In `closeout-audit` mode, read `latest-run.json` and verify it points to the
   reviewed run.
3. Identify the source diff range or changed-file set.
4. Record all resolved paths in `artifact-trace.md` or the report's artifact
   trace section.

### Step 2: Parallel Completion Review

Execute these review roles in parallel.

#### 2a. Product Manager Completion Review

1. Activate Product Manager agent by reading `agents/product-manager/SKILL.md`.
2. Review:
   - feature `STATUS.md`, `PRD.md`, stories, `README.md`, `GETTING-STARTED.md`
   - `pm-closeout.md`, `signoff-ledger.md`, `gate-decisions.md`
   - `REGISTRY.md`, `ROADMAP.md`, `BLUEPRINT.md`, `STORY-INDEX.md`
   - feature mapping path/status entries
3. Check completion:
   - [ ] Every story in scope has an explicit pass/fail disposition.
   - [ ] Acceptance criteria map to implementation and test evidence.
   - [ ] Deferred items are explicit, owned, and not build-critical.
   - [ ] Required signoff roles have passing reviewer/date/evidence entries.
   - [ ] Feature status, archive state, registry, roadmap, blueprint, story
         index, and feature mappings agree.
   - [ ] Remaining high findings, if any, have explicit mitigation acceptance.

#### 2b. Architect Completion Review

1. Activate Architect agent by reading `agents/architect/SKILL.md`.
2. Review:
   - `feature-assembly-plan.md`
   - architecture, API, schema, security, and KG artifacts touched by feature
   - code-index and coverage report bindings for changed code
3. Check completion:
   - [ ] Implementation matches the feature assembly plan or reconciles
         deviations in evidence.
   - [ ] API contracts and schemas match delivered behavior.
   - [ ] Workflow states, data model, authorization, and ADRs remain aligned.
   - [ ] KG bindings and code-index entries cover new or moved source files.
   - [ ] Drift checks pass or unresolved drift is documented as blocking.

#### 2c. Quality Engineer Completion Review

1. Activate Quality Engineer agent by reading
   `agents/quality-engineer/SKILL.md`.
2. Review:
   - `test-plan.md`, `test-execution-report.md`, `coverage-report.md`
   - command logs and raw runtime artifacts
   - E2E, integration, unit, component, visual, and accessibility evidence as
     applicable
3. Check completion:
   - [ ] Every acceptance criterion has test evidence or a justified manual
         verification path.
   - [ ] Tests ran in the required application runtime containers or CI jobs.
   - [ ] Runtime preflight evidence exists before validation commands.
   - [ ] Coverage values in summary reports match raw artifacts.
   - [ ] Failure/retry history distinguishes runtime-blocked failures from code
         defects.
   - [ ] No critical layer is skipped without explicit justification.

#### 2d. Code Reviewer Completion Review

1. Activate Code Reviewer agent by reading `agents/code-reviewer/SKILL.md`.
2. Review:
   - current diff / changed files
   - `code-review-report.md`
   - source and tests for changed surfaces
   - `feature-assembly-plan.md` and story acceptance criteria
3. Check completion:
   - [ ] Changed code is limited to the feature scope.
   - [ ] Source changes implement the planned vertical slice end to end.
   - [ ] Existing review findings are fixed, justified, or non-blocking.
   - [ ] No hidden TODOs, debug code, dead paths, or unreviewed files remain.
   - [ ] Error handling, naming, architecture boundaries, and test quality are
         acceptable for merge.
   - [ ] Non-obvious changes have required rationale comments or decision
         evidence.

#### 2e. Security Completion Review

1. Activate Security agent by reading `agents/security/SKILL.md`.
2. Review:
   - `security-review-report.md` when required
   - auth matrix, policy artifacts, audit/timeline requirements
   - source changes affecting inputs, auth, secrets, workflow transitions,
     document/file handling, AI tools, or external calls
3. Check completion:
   - [ ] Authorization is enforced server-side for new/changed actions.
   - [ ] Inputs, file/document handling, and external calls are validated.
   - [ ] Mutations create required audit/timeline evidence.
   - [ ] No hardcoded secrets, unsafe config, or sensitive data leakage.
   - [ ] Security findings are fixed or have explicit accepted mitigation.
   - [ ] Required security review was not skipped for security-sensitive scope.

#### 2f. DevOps Completion Review (Conditional)

1. Activate DevOps agent by reading `agents/devops/SKILL.md`.
2. Run when runtime, deployment, environment, CI, or infrastructure changed, or
   when deployability evidence is missing or disputed.
3. Review:
   - `deployability-check.md`
   - container, CI, environment, and runtime configuration changes
   - commands and logs cited as deployability evidence
4. Check completion:
   - [ ] Feature can start and run in the declared application runtime.
   - [ ] New environment variables, services, ports, jobs, or secrets are
         documented.
   - [ ] Container/CI changes do not break existing services.
   - [ ] Deployability command evidence is current and feature-scoped.

### Step 3: Required Validation Commands

Run applicable commands and cite results in `feature-review-report.md`:

1. `python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --stage closeout`
2. `python3 agents/product-manager/scripts/validate-trackers.py`
3. `python3 agents/product-manager/scripts/generate-story-index.py {PRODUCT_ROOT}/planning-mds/features/` when story files changed
4. `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-symbols`
5. `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift`
6. `python3 agents/scripts/validate_templates.py`

For `candidate-audit`, use the feature action's in-progress stage command
instead of closeout validation:

```text
python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --run-id {FEATURE_RUN_ID} --stage G6
```

If a command is not applicable, record why. If a command cannot run, record the
failure, likely cause, and whether it affects the done decision.

### Step 4: SELF-REVIEW GATE

Each reviewer checks their section before the done decision:

- [ ] Findings cite exact files, lines, report sections, or evidence paths.
- [ ] Severity matches the impact on whether the feature is truly done.
- [ ] No generic best-practice findings without feature-specific evidence.
- [ ] No hidden fixes were made during review.
- [ ] Any skipped command or artifact has an explicit justification.
- [ ] The changed-file set and evidence run are identified.

### Step 5: DONE GATE

Compute done state from combined findings and validation evidence:

```text
IF required evidence validation fails OR any critical finding:
  STATUS: NOT DONE
  NEXT: repair via feature.md / review.md / test.md / owning-role rework, then rerun feature-review.md

ELSE IF any high finding:
  STATUS: CONDITIONALLY DONE
  NEXT: fix high findings before merge/release, or capture explicit user risk
        acceptance with owner, mitigation, and target date

ELSE:
  STATUS: TRULY DONE
  NEXT: merge/release/stakeholder acceptance can proceed
```

Machine-readable gate state:

```json
{
  "gate": "feature_review",
  "question": "is_this_feature_truly_done",
  "status": "truly_done | conditionally_done | not_done",
  "mode": "closeout_audit | candidate_audit",
  "findings": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "evidence_validation": "pass | fail | skipped",
  "can_merge_or_release": true,
  "requires_risk_acceptance": false,
  "available_actions": ["merge_or_release", "fix_findings", "accept_risk", "cancel"]
}
```

### Step 6: Produce Feature Review Report

Use this structure:

```markdown
# Feature Review Report

Feature: F####-{slug}
Feature Run ID: <FEATURE_RUN_ID>
Review Run ID: <RUN_ID>
Date: YYYY-MM-DD
Mode: closeout-audit / candidate-audit
Review Question: Is this feature truly done?

## Decision
- Status: TRULY DONE / CONDITIONALLY DONE / NOT DONE
- Rationale: <short evidence-backed rationale>
- Next Action: <merge/release / repair / accept risk>

## Findings By Severity

### Critical
- [critical] <finding> - Location: <file:line-or-section>; Evidence: <path>; Impact: <why done is blocked>; Owner: <role>; Recommendation: <fix>

### High
- [high] <finding> - Location: <file:line-or-section>; Evidence: <path>; Impact: <risk>; Owner: <role>; Recommendation: <fix or risk acceptance>

### Medium
- [medium] <finding> - Location: <file:line-or-section>; Recommendation: <fix or defer>

### Low
- [low] <finding> - Location: <file:line-or-section>; Recommendation: <optional improvement>

## Completion Checks
- Requirements satisfaction:
- Architecture and KG alignment:
- Code quality:
- Security:
- Test evidence:
- Deployability:
- Signoff and closeout:
- Tracker sync:

## Validation Evidence
- <command>: PASS/FAIL/SKIPPED - <notes>

## Artifact Trace
- Feature path:
- Feature evidence run:
- latest-run.json:
- Changed-file set:
- Runtime evidence:
```

---

## Completion Criteria

- [ ] `feature-review-report.md` exists under the base run evidence path.
- [ ] Done decision answers "Is this feature truly done?"
- [ ] Findings are severity-ranked and cite concrete files/evidence paths.
- [ ] Required validation commands ran or have explicit skip/failure notes.
- [ ] The reviewed feature run and changed-file set are identified.
- [ ] No implementation, feature, tracker, KG, or evidence artifacts were edited
      by the review action.

## Prerequisites

- [ ] `feature.md` has reached G6 or G8 for the target feature.
- [ ] Feature evidence run ID is known or resolvable from `latest-run.json`.
- [ ] Changed-file set or diff range is available.
- [ ] User has identified whether the review is a `candidate-audit` or
      `closeout-audit`.

## Related Actions

- **Before:** [feature action](./feature.md) - Build and close out the feature.
- **Alternative:** [review action](./review.md) - Code/security review only.
- **Alternative:** [validate action](./validate.md) - Broad artifact alignment.
- **After Findings:** Return to [feature action](./feature.md),
  [review action](./review.md), [test action](./test.md), or direct owning-role
  rework for targeted repairs.
