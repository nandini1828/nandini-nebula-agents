ACTION: agents/actions/build.md
CONTRACT: feature-evidence-package-standardization-plan-v2.md (effective 2026-05-19)

REQUIRED INPUTS (operator must set before SESSION_SETUP):
  BUILD_SCOPE:          [{F####}, {F####}, ...]            # features marked Done/Archived in this build (may be empty for non-feature builds)

OPTIONAL INPUTS (defaults apply when omitted):
  MODE:                 {clean | drift-reconcile}          # default: clean
  PRODUCT_ROOT:         absolute product repo root         # default: sister-repo per agents/docs/AGENT-USE.md

AUTO-RESOLVED (do not set; SESSION_SETUP and the orchestrator compute these):
  BUILD_RUN_ID          = YYYY-MM-DD-{secrets.token_hex(4)} generated at SESSION_SETUP
  BUILD_RUN_FOLDER      = {PRODUCT_ROOT}/planning-mds/operations/evidence/{BUILD_RUN_ID}
  # Per-feature values, resolved from REGISTRY.md per FEATURE_ID in BUILD_SCOPE:
  FEATURE_SLUG          = kebab-case slug for {FEATURE_ID} from REGISTRY.md
  FEATURE_PATH          = {PRODUCT_ROOT}/planning-mds/features/{FEATURE_ID}-{FEATURE_SLUG}
  EVIDENCE_ROOT         = {PRODUCT_ROOT}/planning-mds/operations/evidence/{FEATURE_ID}-{FEATURE_SLUG}
  RUN_ID                = per-feature run ID generated when a new feature package is produced (YYYY-MM-DD-{secrets.token_hex(4)})
  RUN_FOLDER            = {EVIDENCE_ROOT}/{RUN_ID}
  RUN_ID_PRIOR          = prior approved run_id read from {EVIDENCE_ROOT}/latest-run.json (null if absent)
  RERUN_OF              = null | {RUN_ID_PRIOR} when this run regenerates evidence only

SESSION_SETUP:
- Resolve {PRODUCT_ROOT} per agents/docs/AGENT-USE.md → Session Setup
- Echo the resolved absolute {PRODUCT_ROOT} path on the first turn before any shell command
- Generate {BUILD_RUN_ID} once at session start using the contract format:
    date  = local date in ISO YYYY-MM-DD
    suffix = `python3 -c "import secrets; print(secrets.token_hex(4))"`
    BUILD_RUN_ID = {date}-{suffix}
  DO NOT use uuid4. DO NOT regenerate {BUILD_RUN_ID} after the session starts.
- Create the build run folder under the base run evidence profile (§8 of v2 plan):
    BUILD_RUN_FOLDER = {PRODUCT_ROOT}/planning-mds/operations/evidence/{BUILD_RUN_ID}/
    mkdir -p {BUILD_RUN_FOLDER}
- Initialize {BUILD_RUN_FOLDER} base run files from templates: README.md, action-context.md, artifact-trace.md, gate-decisions.md, commands.log (empty JSONL), lifecycle-gates.log (empty)
- DO NOT place a feature evidence package under {BUILD_RUN_FOLDER}; per-feature packages live at each feature's {RUN_FOLDER}
- Determine BUILD_SCOPE: the set of feature IDs this build closes or archives

PRECONDITIONS:
- {BUILD_RUN_FOLDER} created and base run files present
- Every feature in BUILD_SCOPE has either:
    (a) an existing approved feature evidence package referenced by {EVIDENCE_ROOT}/latest-run.json, OR
    (b) a planned canonical evidence package to be produced during this build
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py` exits 0 at start

CONTEXT LOADING ORDER:
1. agents/ROUTER.md
2. agents/agent-map.yaml
3. agents/docs/AGENT-USE.md
4. agents/actions/build.md
5. {PRODUCT_ROOT}/planning-mds/features/REGISTRY.md (parse Active, Planned, Archived, Retired)
6. For each FEATURE_ID in BUILD_SCOPE (resolve {FEATURE_SLUG} from REGISTRY.md per feature):
   - {FEATURE_PATH}/STATUS.md
   - {EVIDENCE_ROOT}/latest-run.json (if exists; non-existence is normal for features being closed for the first time in this build)

FORBIDDEN:
- Generating {BUILD_RUN_ID} or any feature {RUN_ID} with uuid4
- Closing a feature without a canonical feature evidence package at {EVIDENCE_ROOT}/latest-run.json with status="approved"
- Calling tracker sync (validate-trackers.py) before per-feature G6 candidate validation has passed for every feature being closed in this build
- Writing per-feature role reports (g0-*, test-*, code-review-*, etc.) into {BUILD_RUN_FOLDER} instead of the feature run folder
- Using the build run folder as a substitute for any feature's evidence package
- Marking a feature Archived in REGISTRY.md while its {EVIDENCE_ROOT}/latest-run.json is missing or non-approved
- Passing `--evidence-effective-date` earlier than the framework default

REQUIRED TOOL INVOCATIONS:
- For each FEATURE_ID in BUILD_SCOPE that does NOT yet have an approved feature evidence package:
  1. Invoke the feature action prompt (evidence-contract/feature-automation-safe.md) for that FEATURE_ID with a fresh {RUN_ID}
  2. Run through G0–G6 candidate to produce the package
- For each FEATURE_ID in BUILD_SCOPE:
  `python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --run-id {RUN_ID} --stage G6` exit 0
- Then (per build, once):
  `python3 agents/product-manager/scripts/validate-trackers.py` exit 0
- Append every shell command to {BUILD_RUN_FOLDER}/commands.log per §13 JSONL schema
- Append every lifecycle validator command (tracker, story-index, KG, validate_templates, per-feature validate-feature-evidence calls) to {BUILD_RUN_FOLDER}/lifecycle-gates.log

OWNERSHIP:
- product-manager owns: per-feature pm-closeout.md, evidence-manifest.json finalize, prior-manifest supersession patch, latest-run.json write, signoff-ledger.md; build-level archive decisions and REGISTRY.md updates
- build orchestrator owns: BUILD_RUN_FOLDER base run files, sequencing across features, lifecycle-gates.log aggregation
- per-feature ownership of role reports inherits from feature-automation-safe.md

BUILD GATES (sequential, all mandatory):

B0   BUILD SCOPE LOCK
     - Confirm BUILD_SCOPE list; record in {BUILD_RUN_FOLDER}/action-context.md
     - Confirm each feature's current state in REGISTRY.md and STATUS.md
     - Order BUILD_SCOPE by dependency before B1: if any feature's manifest changed_paths[] or feature-mappings.yaml references files newly bound by another feature in scope, the dependency must close first. Record the resolved order in gate-decisions.md as the B0 row. Ties resolve by FEATURE_ID ascending.

B1   PER-FEATURE EVIDENCE PACKAGE PRODUCTION
     - For each FEATURE_ID in BUILD_SCOPE without an approved evidence package:
       Run evidence-contract/feature-automation-safe.md sequence through G6 candidate (fresh {RUN_ID}; rerun_of=null)
     - For each FEATURE_ID being re-closed (already had an approved package, now changing again in this build):
       Produce a NEW {RUN_ID} for the feature; set manifest rerun_of=null if implementation changed, OR rerun_of={RUN_ID_PRIOR} if this run only regenerates evidence with empty changed_paths[] (per §11)
     - For each FEATURE_ID with an existing approved package being re-validated without changes:
       Confirm latest-run.json resolves and manifest status="approved"; do NOT create a new run folder

B2   PER-FEATURE G6 CANDIDATE VALIDATION
     - For each FEATURE_ID in BUILD_SCOPE: `validate-feature-evidence.py --feature {FEATURE_ID} --run-id {RUN_ID} --stage G6` exit 0
     - All in-progress runs must pass candidate validation before tracker sync

B3   TRACKER, STORY-INDEX, KG, TEMPLATE VALIDATION (lifecycle validators)
     - `python3 agents/product-manager/scripts/validate-trackers.py` exit 0
       (validate-trackers.py iterates BUILD_SCOPE; internally calls validate-feature-evidence.py --stage G6 per §22)
     - `python3 agents/product-manager/scripts/generate-story-index.py {PRODUCT_ROOT}/planning-mds/features/`
     - `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift` exit 0
     - `python3 agents/scripts/validate_templates.py` exit 0
     - Append every command + exit code to {BUILD_RUN_FOLDER}/lifecycle-gates.log

B4   PER-FEATURE G8 PM CLOSEOUT (PM role switch mandatory)
     - For each FEATURE_ID in BUILD_SCOPE being closed in this build:
       Execute the G8 PM CLOSEOUT CHECKLIST from evidence-contract/feature-automation-safe.md:
         - Write {RUN_FOLDER}/pm-closeout.md
         - Finalize evidence-manifest.json: status="approved", feature_state, feature_path_at_closeout
         - Run `python3 agents/product-manager/scripts/patch-prior-manifest.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --new-run-id {RUN_ID}`; it is idempotent and patches all prior approved sibling manifests to status="superseded"
         - Write {EVIDENCE_ROOT}/latest-run.json only after patch-prior-manifest.py exits 0
         - Update STATUS.md, REGISTRY.md, ROADMAP.md, BLUEPRINT.md, KG mappings
         - If Done/Completed: move feature folder to archive/
       - `validate-feature-evidence.py --feature {FEATURE_ID} --stage closeout` exit 0

B4.5 BUILD-LEVEL APPROVAL GATE
     - User reviews the aggregated per-feature closeouts (every pm-closeout.md from B4) plus the lifecycle validator results from B3
     - Decision recorded in {BUILD_RUN_FOLDER}/gate-decisions.md as the B4.5 row
     - On refusal: HALT; do not proceed to B5; any further changes restart at B1 for the affected features

B5   BUILD CLOSEOUT
     - Update {BUILD_RUN_FOLDER}/README.md, action-context.md, artifact-trace.md, gate-decisions.md with build-level summary
     - Record in {BUILD_RUN_FOLDER}/gate-decisions.md: per-feature decision rows pointing to each feature's pm-closeout.md
     - Run final validation sweep across all features touched:
       `for F in BUILD_SCOPE: validate-feature-evidence.py --feature $F --stage closeout` (each exit 0)

STOP CONDITIONS:
- Any feature in BUILD_SCOPE fails G6 candidate validation and the cause is not addressable in this build
- Tracker validation fails and cannot be auto-repaired
- A feature's prior approved manifest cannot be patched to superseded (e.g., file write fails or schema rejects)
- Two approved manifests detected for the same feature post-B4 (rule two_approved_runs_without_supersession_fails)
- INSUFFICIENT_CONTEXT for any feature in BUILD_SCOPE
- validate.py or --check-drift fails after one repair cycle

EXIT VALIDATION (run in order; all exit 0):
- For each FEATURE_ID in BUILD_SCOPE: `validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --stage closeout`
- `python3 agents/product-manager/scripts/validate-trackers.py`
- `python3 agents/product-manager/scripts/generate-story-index.py {PRODUCT_ROOT}/planning-mds/features/`
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-symbols`
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift`
- `python3 agents/scripts/validate_templates.py`

NON-FEATURE BUILD RUNS:
- A build that does NOT close or archive any feature still produces the base run evidence package at {BUILD_RUN_FOLDER} per §8 (README.md, action-context.md, artifact-trace.md, gate-decisions.md, commands.log, lifecycle-gates.log)
- It does NOT produce a feature evidence package and does NOT call validate-feature-evidence.py (no scope)
- Tracker validation still runs as a sanity check

CONFLICT RESOLUTION:
- feature evidence package present but STATUS.md missing current signoff rows → halt; feature is not closeout-ready
- REGISTRY.md says Archived but feature evidence package missing or non-approved → halt; do not retroactively backfill (per §4 non-goal); fix REGISTRY.md instead
- Per-feature manifest disagrees with STATUS.md current verdicts → fix the feature (run its G5 again) before continuing the build
- Build re-closing a feature that already has an approved package → produce a NEW {RUN_ID}, set RERUN_OF appropriately, and run patch-prior-manifest.py before writing the new latest-run.json at B4
