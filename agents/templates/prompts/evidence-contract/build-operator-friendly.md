This prompt encodes the build action under the feature evidence contract from `feature-evidence-package-standardization-plan-v2.md` (effective `2026-05-19`).

REQUIRED INPUTS (you must set):
- `BUILD_SCOPE=[{F####}, {F####}, ...]` — features marked Done/Archived in this build (may be empty for non-feature builds)

OPTIONAL INPUTS (defaults apply when omitted):
- `MODE={clean | drift-reconcile}` — default: `clean`
- `PRODUCT_ROOT=` — default: sister-repo resolved per `agents/docs/AGENT-USE.md` → Session Setup; override only for non-standard layouts

AUTO-RESOLVED (do not set; SESSION_SETUP and the orchestrator compute these):
- `BUILD_RUN_ID` — `YYYY-MM-DD-{secrets.token_hex(4)}` generated once at session start
- `BUILD_RUN_FOLDER` — `{PRODUCT_ROOT}/planning-mds/operations/evidence/{BUILD_RUN_ID}`
- For each `FEATURE_ID` in `BUILD_SCOPE`, the orchestrator resolves `FEATURE_SLUG`, `FEATURE_PATH={PRODUCT_ROOT}/planning-mds/features/{FEATURE_ID}-{FEATURE_SLUG}`, `EVIDENCE_ROOT={PRODUCT_ROOT}/planning-mds/operations/evidence/{FEATURE_ID}-{FEATURE_SLUG}`, the per-feature `RUN_ID` (new if producing a new package; existing if re-validating), `RUN_FOLDER={EVIDENCE_ROOT}/{RUN_ID}`, `RUN_ID_PRIOR` (from `{EVIDENCE_ROOT}/latest-run.json` if it exists), and `RERUN_OF` (null, or `{RUN_ID_PRIOR}` for an evidence-only rerun)

Echo the resolved absolute `{PRODUCT_ROOT}` path on your first turn before any shell command; every command below assumes that resolution.

Generate `{BUILD_RUN_ID}` once at session start using the contract format `YYYY-MM-DD-[a-z0-9]{8}` — the date is the local date and the 8-character suffix comes from cryptographic randomness, e.g. `python3 -c "import secrets; print(secrets.token_hex(4))"`. Do not use `uuid4`. Do not regenerate `{BUILD_RUN_ID}` after the session starts.

Set up the build run folder under the base run evidence profile (§8 of the v2 plan). Create `BUILD_RUN_FOLDER` and initialize the base run files from templates: `README.md`, `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, an empty `commands.log` (JSONL), and an empty `lifecycle-gates.log`. The build run folder is NOT a feature evidence package — every feature you close in this build keeps its own package at that feature's `RUN_FOLDER`.

Determine `BUILD_SCOPE`: the set of feature IDs this build closes or archives. Record it in `{BUILD_RUN_FOLDER}/action-context.md` as the first artifact.

Run `agents/actions/build.md` with `BUILD_RUN_ID` set as above and `BUILD_SCOPE=[{F####}, {F####}, ...]`. Start only when `BUILD_RUN_FOLDER` is initialized, every feature in `BUILD_SCOPE` either already has an approved evidence package or is scheduled to produce one during this build, and `python3 {PRODUCT_ROOT}/scripts/kg/validate.py` exits 0.

Load context in this order:
1. `agents/ROUTER.md`
2. `agents/agent-map.yaml`
3. `agents/docs/AGENT-USE.md`
4. `agents/actions/build.md`
5. `{PRODUCT_ROOT}/planning-mds/features/REGISTRY.md` (parse Active, Planned, Archived, Retired sections)
6. For each `FEATURE_ID` in `BUILD_SCOPE`: that feature's `STATUS.md` and (if present) `{EVIDENCE_ROOT}/latest-run.json`

Don't generate `{BUILD_RUN_ID}` or any feature `{RUN_ID}` with `uuid4`. Don't close a feature without a canonical evidence package at `{EVIDENCE_ROOT}/latest-run.json` with `status=approved`. Don't call `validate-trackers.py` before per-feature G6 candidate validation has passed for every feature being closed in this build. Don't write per-feature role reports (`g0-*`, `test-*`, `code-review-*`, etc.) into `{BUILD_RUN_FOLDER}` instead of the feature run folder. Don't use the build run folder as a substitute for any feature's evidence package. Don't mark a feature `Archived` in `REGISTRY.md` while its `latest-run.json` is missing or non-approved. Don't pass `--evidence-effective-date` earlier than the framework default.

Append every shell command you run to `{BUILD_RUN_FOLDER}/commands.log` as JSON Lines per the §13 schema (`schema_version`, `timestamp` with timezone, `cwd`, `command`, `exit_code`, `artifacts[]`, `redactions[]`). Append every lifecycle validator command (tracker, story-index, KG, validate_templates, per-feature `validate-feature-evidence` calls) to `{BUILD_RUN_FOLDER}/lifecycle-gates.log`.

Follow these build gates exactly:

- `B0 BUILD SCOPE LOCK` — confirm `BUILD_SCOPE`; record it in `action-context.md`; confirm each feature's current state in `REGISTRY.md` and `STATUS.md`; order `BUILD_SCOPE` by dependency before B1 (if any feature's manifest `changed_paths[]` or `feature-mappings.yaml` references files newly bound by another feature in scope, the dependency closes first; ties resolve by `FEATURE_ID` ascending; record the resolved order in `gate-decisions.md`)
- `B1 PER-FEATURE EVIDENCE PACKAGE PRODUCTION` — for each `FEATURE_ID` in `BUILD_SCOPE` without an approved evidence package, invoke `evidence-contract/feature-automation-safe.md` (or its operator-friendly mirror) with a fresh `{RUN_ID}` and `rerun_of=null` and run that feature through G0–G6 candidate; for each `FEATURE_ID` being re-closed (already had an approved package, now changing again in this build) produce a new `{RUN_ID}` and set `rerun_of=null` if implementation changed or `rerun_of={RUN_ID_PRIOR}` for an evidence-only rerun with empty `changed_paths[]` per §11; for each `FEATURE_ID` with an existing approved package being re-validated without changes, confirm `latest-run.json` resolves and the manifest carries `status=approved` and do NOT create a new run folder
- `B2 PER-FEATURE G6 CANDIDATE VALIDATION` — for each `FEATURE_ID` in `BUILD_SCOPE`: `python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --run-id {RUN_ID} --stage G6` must exit 0. All in-progress runs must pass candidate validation before tracker sync
- `B3 LIFECYCLE VALIDATORS` — run `validate-trackers.py` (it iterates `BUILD_SCOPE` and internally calls `validate-feature-evidence.py --stage G6` per §22), `generate-story-index.py`, `kg/validate.py --check-drift`, and `validate_templates.py` — each must exit 0; append every command + exit code to `lifecycle-gates.log`
- `B4 PER-FEATURE G8 PM CLOSEOUT` — for each `FEATURE_ID` in `BUILD_SCOPE` being closed in this build, switch to the PM role (read `agents/product-manager/SKILL.md`) and execute the G8 PM CLOSEOUT CHECKLIST from `evidence-contract/feature-automation-safe.md`: write `pm-closeout.md`, finalize that feature's manifest (`status=approved`, `feature_state`, `feature_path_at_closeout`), run `python3 agents/product-manager/scripts/patch-prior-manifest.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --new-run-id {RUN_ID}` to patch prior approved sibling manifests, write `{EVIDENCE_ROOT}/latest-run.json` only after the patch script exits 0, update `STATUS.md` + `REGISTRY.md` + `ROADMAP.md` + `BLUEPRINT.md` + KG mappings, move the feature folder to `archive/` if Done/Completed, and run `validate-feature-evidence.py --feature {FEATURE_ID} --stage closeout` exit 0
- `B4.5 BUILD-LEVEL APPROVAL GATE` — user reviews the aggregated per-feature closeouts from B4 plus the lifecycle validator results from B3; decision recorded in `gate-decisions.md` as the B4.5 row; on refusal, HALT and do not proceed to B5 (further changes restart at B1 for the affected features)
- `B5 BUILD CLOSEOUT` — update `{BUILD_RUN_FOLDER}/README.md`, `action-context.md`, `artifact-trace.md`, and `gate-decisions.md` with the build-level summary; `gate-decisions.md` should carry a row per feature pointing to that feature's `pm-closeout.md`; run a final validation sweep `for F in BUILD_SCOPE: validate-feature-evidence.py --feature $F --stage closeout` and confirm every call exits 0

Stop immediately if any feature in `BUILD_SCOPE` fails G6 candidate validation and the cause is not addressable in this build, if tracker validation fails and cannot be auto-repaired, if a prior approved manifest cannot be patched to `superseded`, if two approved manifests are detected for the same feature post-B4, if `INSUFFICIENT_CONTEXT` occurs for any feature in scope, or if `validate.py` or `--check-drift` fails after one repair cycle.

Close the build by executing these in order, with every call exit 0:
- For each `FEATURE_ID` in `BUILD_SCOPE`: `python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} --stage closeout`
- `python3 agents/product-manager/scripts/validate-trackers.py`
- `python3 agents/product-manager/scripts/generate-story-index.py {PRODUCT_ROOT}/planning-mds/features/`
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-symbols`
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift`
- `python3 agents/scripts/validate_templates.py`

If this build does NOT close or archive any feature, still produce the base run evidence package at `{BUILD_RUN_FOLDER}` per §8 (the six base files). Do not produce a feature evidence package and do not call `validate-feature-evidence.py` — there is no feature scope. Tracker validation still runs as a sanity check.

Resolve conflicts like this:
- feature evidence package present but `STATUS.md` missing current signoff rows → halt; the feature is not closeout-ready
- `REGISTRY.md` says `Archived` but feature evidence package is missing or non-approved → halt; do not retroactively backfill (per §4 non-goal); fix `REGISTRY.md` instead
- per-feature manifest disagrees with `STATUS.md` current verdicts → fix the feature (re-run G5) before continuing the build
- build re-closing a feature that already has an approved package → produce a NEW `{RUN_ID}` for that feature, set `RERUN_OF` appropriately, and run `patch-prior-manifest.py` before writing the new `latest-run.json` at B4
