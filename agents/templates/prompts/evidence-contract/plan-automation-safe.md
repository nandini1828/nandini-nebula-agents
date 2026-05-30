ACTION: agents/actions/plan.md
CONTRACT: feature-evidence-package-standardization-plan-v2.md (effective 2026-05-19)
CONTRACT SCOPE: Plan runs BEFORE the feature evidence package exists. It produces planning artifacts (feature-assembly-plan.md, PRD updates, ADRs, story breakdowns) inside {FEATURE_PATH}. It also produces a base run evidence package per §8 at the non-feature run path.

REQUIRED INPUTS (operator must set before SESSION_SETUP):
  FEATURE_ID:           {F####}
  PHASE:                {A | B | A+B}                          # A = PM requirements; B = Architect architecture; A+B = both
  FEATURE_MODE:         {new | existing}                       # new = reserved ID but folder absent; existing = folder already scaffolded

OPTIONAL INPUTS (defaults apply when omitted):
  PRODUCT_ROOT:         absolute product repo root             # default: sister-repo per agents/docs/AGENT-USE.md

AUTO-RESOLVED (do not set; SESSION_SETUP and the orchestrator compute these):
  FEATURE_SLUG          = kebab-case slug for {FEATURE_ID} from REGISTRY.md
  FEATURE_PATH          = {PRODUCT_ROOT}/planning-mds/features/{FEATURE_ID}-{FEATURE_SLUG}
  FEATURE_EVIDENCE_ROOT = {PRODUCT_ROOT}/planning-mds/operations/evidence/{FEATURE_ID}-{FEATURE_SLUG}
  PLAN_RUN_ID           = YYYY-MM-DD-{secrets.token_hex(4)} generated at SESSION_SETUP
  PLAN_RUN_FOLDER       = {PRODUCT_ROOT}/planning-mds/operations/evidence/{PLAN_RUN_ID}

SESSION_SETUP:
- Resolve {PRODUCT_ROOT} per agents/docs/AGENT-USE.md → Session Setup
- Echo the resolved absolute {PRODUCT_ROOT} path on the first turn before any shell command
- Generate {PLAN_RUN_ID} once at session start using the contract format:
    date  = local date in ISO YYYY-MM-DD
    suffix = `python3 -c "import secrets; print(secrets.token_hex(4))"`
    PLAN_RUN_ID = {date}-{suffix}
  DO NOT use uuid4. DO NOT regenerate {PLAN_RUN_ID} after session start.
- Create base run folder per §8 (non-feature profile):
    PLAN_RUN_FOLDER = {PRODUCT_ROOT}/planning-mds/operations/evidence/{PLAN_RUN_ID}/
    mkdir -p {PLAN_RUN_FOLDER}
- Initialize base run files from templates: README.md, action-context.md, artifact-trace.md, gate-decisions.md, commands.log (empty JSONL), lifecycle-gates.log (empty)
- Plan runs do NOT create a feature evidence package. The feature evidence root is created later by `agents/actions/feature.md` for the same FEATURE_ID.

PRECONDITIONS:
- {PLAN_RUN_FOLDER} created with base run files present
- Determine FEATURE_MODE upfront:
    new       = FEATURE_ID is reserved in REGISTRY.md (Planned (Reserved IDs)) but {FEATURE_PATH} does not exist
    existing  = {FEATURE_PATH} already exists with at least PRD.md and STATUS.md skeleton
- PHASE/FEATURE_MODE compatibility:
    PHASE=A, FEATURE_MODE=new       → plan creates {FEATURE_PATH} and scaffolds PRD/personas/stories/STATUS skeleton
    PHASE=A, FEATURE_MODE=existing  → plan updates the existing planning artifacts; STATUS.md story provenance rows are append-only (never mutated)
    PHASE=B, FEATURE_MODE=new       → REJECT: cannot run architecture before requirements exist; run PHASE=A or A+B instead
    PHASE=B, FEATURE_MODE=existing  → plan updates feature-assembly-plan.md and ontology bindings
    PHASE=A+B, FEATURE_MODE=new     → plan creates {FEATURE_PATH}, runs Phase A then Phase B
    PHASE=A+B, FEATURE_MODE=existing → plan updates planning artifacts then architecture
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py` exits 0 at start

CONTEXT LOADING ORDER:
1. agents/ROUTER.md
2. agents/agent-map.yaml
3. agents/docs/AGENT-USE.md
4. agents/actions/plan.md
5. {PRODUCT_ROOT}/planning-mds/features/REGISTRY.md (confirm FEATURE_ID is reserved or new)
6. {PRODUCT_ROOT}/planning-mds/features/ROADMAP.md
7. {PRODUCT_ROOT}/planning-mds/BLUEPRINT.md (domain context)
8. {PRODUCT_ROOT}/planning-mds/knowledge-graph/solution-ontology.yaml (architectural context)
9. {PRODUCT_ROOT}/planning-mds/knowledge-graph/canonical-nodes.yaml
10. {PRODUCT_ROOT}/planning-mds/knowledge-graph/feature-mappings.yaml
11. {PRODUCT_ROOT}/planning-mds/knowledge-graph/code-index.yaml
12. {PRODUCT_ROOT}/planning-mds/knowledge-graph/coverage-report.yaml
13. {PRODUCT_ROOT}/planning-mds/features/F{NNNN}-{slug}/** when the feature folder exists

ON-DEMAND PATHS (only when linked by lookup, required by the current gate, or required by drift repair):
- {PRODUCT_ROOT}/planning-mds/api/<openapi-spec>.yaml
- {PRODUCT_ROOT}/planning-mds/security/authorization-matrix.md
- {PRODUCT_ROOT}/planning-mds/security/policies/policy.csv
- agents/<role>/references/** only after a matching agents/ROUTER.md row

FORBIDDEN:
- Generating {PLAN_RUN_ID} with uuid4 or any non-contract format
- Writing or consuming `current-run.json` for any reason
- Producing role reports (g0-*, test-*, code-review-*, etc.) — those belong to the feature action's evidence package
- Creating a feature evidence package at {FEATURE_EVIDENCE_ROOT}/ during plan
- Skipping APPROVAL or ONTOLOGY SYNC gates
- Editing canonical-nodes.yaml or solution-ontology.yaml outside the Architect phase
- Treating lookup/KG mappings as authoritative over raw artifacts
- Climbing past max_auto_tier without recording a workstate.py escalate event

OWNERSHIP:
- product-manager owns Phase A: PRD.md, persona files, acceptance criteria, story breakdown, initial STATUS.md skeleton
- architect owns Phase B: feature-assembly-plan.md, ADRs, API contract updates, schema updates, canonical-nodes.yaml updates, solution-ontology.yaml updates, feature-mappings.yaml additions
- implementation agents do not run during plan; other roles flag drift but do not silently redefine canonical shared semantics

GATES:
- `G1 CLARIFICATION` — Step 1.5 Requirements Clarification (PM resolves open requirement questions before approval)
- `G2 TRACKER SYNC (A)` — Step 1.75 Mandatory tracker synchronization (REGISTRY.md / ROADMAP.md / BLUEPRINT.md / STORY-INDEX.md) before Phase A approval
- `G3 PHASE A APPROVAL` — Step 2 user reviews requirements; PM records decision in gate-decisions.md
- `G4 ONTOLOGY SYNC (B)` — Step 3.5 feature-mappings.yaml + canonical-nodes.yaml + solution-ontology.yaml aligned with the assembly plan; `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift` exit 0
- `G5 PHASE B APPROVAL` — Step 4 user reviews architecture; architect records decision in gate-decisions.md

EVIDENCE OUTPUTS (in {PLAN_RUN_FOLDER}):
- README.md (Run Summary, Status, Evidence Index, Validation Summary, Open Follow-ups)
- action-context.md (Run Identity, Inputs, Assumptions, Scope Boundaries, Lifecycle Stage = "Plan")
- artifact-trace.md (which planning files were created/updated; pointer to {FEATURE_PATH}/feature-assembly-plan.md and PRD.md)
- gate-decisions.md (one row per gate: A0, A1, B0, B1, B2)
- commands.log (JSONL per §13 schema)
- lifecycle-gates.log (validator results)

EVIDENCE OUTPUTS (in {FEATURE_PATH}):
- PRD.md (Phase A)
- persona files, acceptance-criteria-checklist.md (Phase A)
- story files under {FEATURE_PATH}/stories/ or per product convention (Phase A)
- STATUS.md skeleton with Required Role Matrix and empty Story Provenance table (Phase A)
- feature-assembly-plan.md (Phase B)
- ADRs under {FEATURE_PATH}/adrs/ as applicable (Phase B)
- README.md and GETTING-STARTED.md (Phase B)

STOP CONDITIONS:
- PRD approval refused by user
- Architecture approval refused by user
- Ontology sync gate fails and cannot be reconciled
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift` fails after one repair cycle
- Canonical node edit attempted outside Architect role

EXIT VALIDATION (run in order; all exit 0):
- `python3 agents/product-manager/scripts/validate-stories.py {FEATURE_PATH}`
- `python3 agents/product-manager/scripts/generate-story-index.py {PRODUCT_ROOT}/planning-mds/features/`
- `python3 agents/product-manager/scripts/validate-trackers.py` (with FEATURE_ID context if applicable)
- IF KG changed: `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --write-coverage-report`
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py`
- `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift`
- `python3 agents/scripts/validate_templates.py`
- NOTE: do NOT call validate-feature-evidence.py at plan — there is no feature evidence package yet

CONFLICT RESOLUTION:
- PRD vs architecture conflict → resolve in Phase B before architecture approval; do not silently change PRD
- existing assembly plan vs new architecture → log reconciliation in gate-decisions.md; never silently overwrite
- ontology binding conflict → halt; resolve in canonical-nodes.yaml first
