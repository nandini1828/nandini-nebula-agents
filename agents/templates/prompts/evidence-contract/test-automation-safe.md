ACTION: agents/actions/test.md
CONTRACT: feature-evidence-package-standardization-plan-v2.md (effective 2026-05-19)
CONTRACT SCOPE: Test can run in two modes:
  (a) feature-scoped: writes test-plan.md, test-execution-report.md, coverage-report.md INTO an existing feature run folder; the parent feature action drives G2 and G5
  (b) standalone: writes QE reports under a base run evidence folder; does NOT produce a feature evidence package

REQUIRED INPUTS (operator must set before SESSION_SETUP):
  MODE:                 {feature-scoped | standalone}
  TEST_SCOPE:           {unit | component | integration | e2e | api | accessibility | regression | all}
  # When MODE=feature-scoped, also REQUIRED:
  FEATURE_ID:           {F####}                                # required when MODE=feature-scoped
  RUN_ID:               {YYYY-MM-DD-[a-z0-9]{8}}               # required when MODE=feature-scoped; the parent feature run ID

OPTIONAL INPUTS (defaults apply when omitted):
  STORIES:              [{F####-S####}, ...]                   # story IDs covered (only when MODE=feature-scoped); default: all stories in the feature breakdown
  PRODUCT_ROOT:         absolute product repo root             # default: sister-repo per agents/docs/AGENT-USE.md

AUTO-RESOLVED (do not set; SESSION_SETUP and the orchestrator compute these):
  FEATURE_SLUG          = kebab-case slug for {FEATURE_ID} from REGISTRY.md (only when MODE=feature-scoped)
  FEATURE_PATH          = {PRODUCT_ROOT}/planning-mds/features/{FEATURE_ID}-{FEATURE_SLUG} (only when MODE=feature-scoped)
  OUTPUT_FOLDER         = {PRODUCT_ROOT}/planning-mds/operations/evidence/{FEATURE_ID}-{FEATURE_SLUG}/{RUN_ID} (only when MODE=feature-scoped)
  ARTIFACTS_FOLDER      = {OUTPUT_FOLDER}/artifacts/test-results (only when MODE=feature-scoped)
  COVERAGE_FOLDER       = {OUTPUT_FOLDER}/artifacts/coverage (only when MODE=feature-scoped)
  SCREENSHOTS_FOLDER    = {OUTPUT_FOLDER}/artifacts/screenshots (only when MODE=feature-scoped)
  TEST_RUN_ID           = YYYY-MM-DD-{secrets.token_hex(4)} generated at SESSION_SETUP (only when MODE=standalone)
  TEST_RUN_FOLDER       = {PRODUCT_ROOT}/planning-mds/operations/evidence/{TEST_RUN_ID} (only when MODE=standalone)

SESSION_SETUP:
- Resolve {PRODUCT_ROOT} per agents/docs/AGENT-USE.md → Session Setup
- Echo resolved absolute {PRODUCT_ROOT}
- Determine MODE: feature-scoped or standalone
- Generate {TEST_RUN_ID} once at session start using contract format YYYY-MM-DD-[a-z0-9]{8} (suffix from `secrets.token_hex(4)`). DO NOT use uuid4.
- For MODE=feature-scoped:
    REQUIRED PARAM: FEATURE_ID, RUN_ID (parent feature run ID)
    OUTPUT_FOLDER = {PRODUCT_ROOT}/planning-mds/operations/evidence/{FEATURE_ID}-{FEATURE_SLUG}/{RUN_ID}/
    DO NOT create a new run folder; OUTPUT_FOLDER must already exist
    ARTIFACTS_FOLDER   = {OUTPUT_FOLDER}/artifacts/test-results/    (raw test output)
    COVERAGE_FOLDER    = {OUTPUT_FOLDER}/artifacts/coverage/        (raw coverage output)
    SCREENSHOTS_FOLDER = {OUTPUT_FOLDER}/artifacts/screenshots/     (visual regression snapshots from Playwright/Cypress/etc., when applicable)
- For MODE=standalone:
    TEST_RUN_FOLDER = {PRODUCT_ROOT}/planning-mds/operations/evidence/{TEST_RUN_ID}/
    mkdir -p {TEST_RUN_FOLDER}/artifacts/{test-results,coverage}
    Initialize base run files per §8

PRECONDITIONS:
- For MODE=feature-scoped: feature run folder exists; G1 has passed; coverage-report.md format known per §14
- For MODE=standalone: TEST_RUN_FOLDER created with base run files
- Application runtime containers healthy
- Test commands run inside runtime containers

CONTEXT LOADING ORDER:
1. agents/ROUTER.md
2. agents/agent-map.yaml
3. agents/docs/AGENT-USE.md
4. agents/actions/test.md
5. agents/quality-engineer/SKILL.md
6. For feature-scoped: {FEATURE_PATH}/feature-assembly-plan.md, {FEATURE_PATH}/STATUS.md, story files under {FEATURE_PATH}/stories/ (or feature-local convention), {OUTPUT_FOLDER}/evidence-manifest.json

FORBIDDEN:
- Generating run IDs with uuid4
- Writing QE reports outside {OUTPUT_FOLDER} or {TEST_RUN_FOLDER}
- For feature-scoped: creating a new run folder during test instead of using existing {OUTPUT_FOLDER}
- Skipping coverage-report.md entirely — the file must exist even when coverage is waived (§10)
- Mocking runtime layers in integration/E2E tests when raw runtime is available
- Citing summary prose alone as evidence for a passing gate; artifact paths are required
- Generic universal coverage thresholds; coverage targets are feature-scoped per §29 risk mitigation

REQUIRED TOOL INVOCATIONS:
- Test commands run inside runtime containers; record artifact paths in commands.log per §13
- Coverage tool output stored under ARTIFACTS_FOLDER (or implementation-layer path referenced from the report per §10)
- Append every shell command to commands.log

OWNERSHIP:
- quality-engineer owns: test-plan.md, test-execution-report.md, coverage-report.md (all required for completed terminal features per §10)
- developer-vs-QE split documented in test-plan.md

EVIDENCE OUTPUTS:
For MODE=feature-scoped, write into {OUTPUT_FOLDER}:
- test-plan.md (headings per §14: story-to-AC mapping; unit/component/integration/E2E/API/accessibility strategy; developer-vs-QE test ownership; test data/fixtures; happy/edge/error/auth/accessibility/regression cases; Result)
- test-execution-report.md (headings per §14: commands executed; pass/fail counts; skipped tests + rationale; raw test artifact paths; failed/retried command history; AC coverage; Result)
- coverage-report.md (always exists; headings per §14: coverage target and actual per layer; raw artifact paths; feature-scoped notes; waiver if coverage cannot be produced — with owner/date/scope/follow-up; Result)
- Copy or reference raw test results under {OUTPUT_FOLDER}/artifacts/test-results/
- Copy or reference raw coverage output under {OUTPUT_FOLDER}/artifacts/coverage/
- Copy or reference visual regression snapshots under {OUTPUT_FOLDER}/artifacts/screenshots/ when applicable (rule screenshot_reference_missing_fails when test-execution-report.md cites a screenshot path that does not resolve)
- Update {OUTPUT_FOLDER}/evidence-manifest.json role_results: Quality Engineer with required_artifacts=[test-plan.md, test-execution-report.md, coverage-report.md], verdict_artifact=test-execution-report.md, current verdict
- If coverage waived, also populate {OUTPUT_FOLDER}/evidence-manifest.json waivers.coverage with required, reason, owner, approved_on, follow_up

For MODE=standalone, write same reports plus six base run files into {TEST_RUN_FOLDER}

GATES:
- T0  TEST PLAN — test-plan.md produced and reviewed
- T1  TEST EXECUTION — test-execution-report.md produced with raw artifact paths
- T2  COVERAGE — coverage-report.md produced (with waiver inline if applicable)
- T3  SELF-REVIEW GATE — QE self-checks the three reports
- T4  QUALITY GATE — coverage and pass-rate thresholds met or waiver accepted
- T5  STAGE VALIDATION (feature-scoped only) — `validate-feature-evidence.py --feature {FEATURE_ID} --run-id {RUN_ID} --stage G2` exit 0 (G2 is where QE reports are first required)

STOP CONDITIONS:
- coverage-report.md missing (rule missing_coverage_report_fails)
- test-execution-report.md missing (rule missing_test_execution_fails)
- test-plan.md missing (rule missing_test_plan_fails)
- coverage waiver requested without PM acceptance at closeout (handled at G8)
- INSUFFICIENT_CONTEXT

EXIT VALIDATION:
- For MODE=feature-scoped: `validate-feature-evidence.py --feature {FEATURE_ID} --run-id {RUN_ID} --stage G2` exit 0
- For MODE=standalone: confirm base run files complete; no feature-stage validation

CONFLICT RESOLUTION:
- coverage target met but story has no test → fail; add test or document AC exception
- coverage report exists but raw artifacts missing → fail (rule coverage_claim_without_artifact_fails)
- test-execution-report.md cites artifact path that does not resolve → fail (rule test_results_reference_missing_fails)
- waiver in coverage-report.md missing PM acceptance at closeout → handled by G8 rule coverage_waiver_missing_pm_acceptance_fails
