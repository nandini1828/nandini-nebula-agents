ACTION: agents/actions/validate.md
CONTRACT: feature-evidence-package-standardization-plan-v2.md (effective 2026-05-19)
CONTRACT SCOPE: Validate is a parallel-agent validation action. Product Manager validates requirements and Architect validates architecture; when implementation is in scope, they additionally invoke the framework validators (validate-feature-evidence.py, validate-trackers.py, kg/validate.py, generate-story-index.py, validate_templates.py) as tools. The action produces a base run evidence package per §8 with per-agent validation reports; it does NOT write into any feature evidence package.

REQUIRED INPUTS (operator must set before SESSION_SETUP):
  VALIDATION_SCOPE:     {requirements | architecture | implementation | all}

OPTIONAL INPUTS (defaults apply when omitted):
  FEATURE_ID:           {F####}                              # narrows implementation validation to a single feature
  STAGE:                {G0|G1|G2|G3|G5|G6|G8|closeout}  # default: closeout (only meaningful when FEATURE_ID is set)
  RUN_ID:               {YYYY-MM-DD-[a-z0-9]{8}}             # parent feature run ID; required when STAGE is G0..G5
  EFFECTIVE_DATE:       {YYYY-MM-DD}                         # default: 2026-05-19 (framework default); earlier values rejected per §22
  PRODUCT_ROOT:         absolute product repo root           # default: sister-repo per agents/docs/AGENT-USE.md

AUTO-RESOLVED (do not set; SESSION_SETUP and the orchestrator compute these):
  VALIDATE_RUN_ID       = YYYY-MM-DD-{secrets.token_hex(4)} generated at SESSION_SETUP
  VALIDATE_RUN_FOLDER   = {PRODUCT_ROOT}/planning-mds/operations/evidence/{VALIDATE_RUN_ID}
  FEATURE_SLUG          = kebab-case slug for {FEATURE_ID} from REGISTRY.md (only when FEATURE_ID is set)
  EVIDENCE_ROOT         = {PRODUCT_ROOT}/planning-mds/operations/evidence/{FEATURE_ID}-{FEATURE_SLUG} (only when FEATURE_ID is set)

SESSION_SETUP:
- Resolve {PRODUCT_ROOT} per agents/docs/AGENT-USE.md → Session Setup
- Echo resolved absolute {PRODUCT_ROOT}
- Generate {VALIDATE_RUN_ID} once at session start using contract format YYYY-MM-DD-[a-z0-9]{8} (suffix from `secrets.token_hex(4)`). DO NOT use uuid4.
- Create base run folder per §8:
    VALIDATE_RUN_FOLDER = {PRODUCT_ROOT}/planning-mds/operations/evidence/{VALIDATE_RUN_ID}/
    mkdir -p {VALIDATE_RUN_FOLDER}/artifacts
- Initialize base run files from templates: README.md, action-context.md, artifact-trace.md, gate-decisions.md, commands.log (empty JSONL), lifecycle-gates.log (empty)

PRECONDITIONS:
- {VALIDATE_RUN_FOLDER} created with base run files
- For VALIDATION_SCOPE in {requirements, all}: BLUEPRINT.md, REGISTRY.md, ROADMAP.md exist
- For VALIDATION_SCOPE in {architecture, all}: solution-ontology.yaml, canonical-nodes.yaml, feature-mappings.yaml exist
- For VALIDATION_SCOPE in {implementation, all}: at least one completed terminal feature in REGISTRY.md OR FEATURE_ID is set
- When implementation validation targets an in-progress feature with STAGE in {G0..G5}: --run-id is mandatory
- When implementation validation targets an approved feature at STAGE in {G8|closeout}: {EVIDENCE_ROOT}/latest-run.json must exist

CONTEXT LOADING ORDER:
1. agents/ROUTER.md
2. agents/agent-map.yaml
3. agents/docs/AGENT-USE.md
4. agents/actions/validate.md
5. agents/product-manager/SKILL.md (requirements validation mode)
6. agents/architect/SKILL.md (architecture validation mode)
7. agents/product-manager/scripts/README.md (validator commands and exit codes — only when VALIDATION_SCOPE includes implementation)

FORBIDDEN:
- Generating {VALIDATE_RUN_ID} with uuid4
- Writing into any feature evidence package (validate is read-only with respect to feature packages)
- Treating validator script output as a substitute for the PM/Architect agent-level validation work
- Passing --evidence-effective-date earlier than the framework default
- Calling --stage G8 or --stage closeout when invoked transitively from validate-trackers.py context (per §17 step 2: tracker integration uses --stage G6 only)
- Producing validation summaries that hide errors as warnings
- Skipping the SELF-REVIEW gate per agent
- Bypassing the APPROVAL gate before reporting results upstream

OWNERSHIP:
- product-manager (requirements validation) owns: requirements validation report in {VALIDATE_RUN_FOLDER}/pm-validation-report.md
- architect (architecture validation) owns: architecture validation report in {VALIDATE_RUN_FOLDER}/architect-validation-report.md
- implementation validation (run by either or both agents based on scope) owns: validator script invocation, output capture, and findings in {VALIDATE_RUN_FOLDER}/implementation-validation-report.md

GATES (mirror agents/actions/validate.md):

V0  SCOPE LOCK
    - Record VALIDATION_SCOPE, FEATURE_ID, STAGE in action-context.md
    - Decide which agent(s) run in parallel based on scope

V1  PARALLEL VALIDATION (PM + Architect)
    1a. PRODUCT MANAGER (Requirements Validation) — when VALIDATION_SCOPE in {requirements, all}
        - Read context per agents/actions/validate.md Step 1a
        - Execute requirements completeness, vision/non-goals, persona, feature traceability, story testability, and acceptance criteria checks listed in validate.md
        - Produce {VALIDATE_RUN_FOLDER}/pm-validation-report.md with sections: Completeness, Vision & Non-Goals, Personas, Feature Traceability, Story Testability, Acceptance Criteria, Findings (severity-ranked), Result
    1b. ARCHITECT (Architecture Validation) — when VALIDATION_SCOPE in {architecture, all}
        - Read context per agents/actions/validate.md Step 1b
        - Execute solution-ontology, canonical-nodes, feature-mappings, API contract, schema, authorization, and assembly-plan consistency checks listed in validate.md
        - Produce {VALIDATE_RUN_FOLDER}/architect-validation-report.md with sections: Ontology Integrity, Canonical Nodes, Feature Mappings, API Contracts, Schemas, Authorization, Assembly-Plan Alignment, Findings (severity-ranked), Result
    1c. IMPLEMENTATION VALIDATION (script-driven) — when VALIDATION_SCOPE in {implementation, all}
        - Owner is PM unless FEATURE_ID narrows to a feature in active development, in which case the feature's orchestrator/PM
        - Run the following commands; capture stdout/stderr and exit code per command; append every command to {VALIDATE_RUN_FOLDER}/commands.log per §13 JSONL schema:
          For FEATURE_ID unset (registry-wide):
            i.   `python3 agents/product-manager/scripts/validate-trackers.py`
            ii.  `python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --json` → capture to {VALIDATE_RUN_FOLDER}/artifacts/feature-evidence-validation.json
            iii. `python3 agents/product-manager/scripts/generate-story-index.py {PRODUCT_ROOT}/planning-mds/features/`
            iv.  `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-symbols`
            v.   `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift`
            vi.  `python3 agents/scripts/validate_templates.py`
          For FEATURE_ID set:
            i.   `python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {PRODUCT_ROOT} --feature {FEATURE_ID} [--run-id {RUN_ID}] --stage {STAGE} --json` → capture to {VALIDATE_RUN_FOLDER}/artifacts/feature-evidence-validation.json
            ii.  `python3 agents/product-manager/scripts/validate-trackers.py --feature {FEATURE_ID} [--run-id {RUN_ID}]`
            iii. `python3 {PRODUCT_ROOT}/scripts/kg/validate.py --check-drift`
            iv.  `python3 agents/scripts/validate_templates.py`
        - Produce {VALIDATE_RUN_FOLDER}/implementation-validation-report.md with: commands executed, exit codes, errors/warnings/info from validator output, KG drift status, template alignment status, Findings (cross-referenced to rule IDs from §22), Result

V2  SELF-REVIEW GATE
    - Each producing agent reviews its own report for completeness and accuracy
    - PM: confirms every Step-1a check is recorded and findings cite specific files
    - Architect: confirms every Step-1b check is recorded and findings cite specific files
    - Implementation: confirms every required validator command was run, exit codes are recorded, and any rule-ID findings include feature/run path

V3  APPROVAL GATE
    - User reviews all produced reports and decides next steps
    - Decision recorded in {VALIDATE_RUN_FOLDER}/gate-decisions.md

EVIDENCE OUTPUTS (in {VALIDATE_RUN_FOLDER}):
- README.md (Run Summary, Status, Evidence Index listing the per-agent reports, Validation Summary aggregating verdicts, Open Follow-ups)
- action-context.md (Run Identity, Inputs = VALIDATION_SCOPE/FEATURE_ID/STAGE, Assumptions, Scope Boundaries = "Validation review; not feature evidence", Lifecycle Stage = "Validate")
- artifact-trace.md (every report and JSON output produced; references to the source artifacts each agent read)
- gate-decisions.md (V0..V3 rows)
- commands.log (validator and KG commands when implementation validation ran)
- lifecycle-gates.log (validator exit codes and summaries)
- pm-validation-report.md (when in scope)
- architect-validation-report.md (when in scope)
- implementation-validation-report.md (when in scope)
- artifacts/feature-evidence-validation.json (when implementation validation ran)

STOP CONDITIONS:
- Any validator returns exit code 2 (validator invocation error) — escalate to user
- Any error-severity rule fires on a governed completed terminal feature and the operator does not authorize the validator-defect waiver path per §28
- KG drift detected and not auto-repairable
- Effective-date override attempted with earlier-than-default value
- Two approved manifests detected for the same feature (rule two_approved_runs_without_supersession_fails) — escalate to PM
- Either agent's SELF-REVIEW finds its own report materially incomplete
- User refuses APPROVAL GATE

EXIT VALIDATION:
- All scope-applicable commands listed under V1 exit 0 (or exit 2 escalated to user)
- All required per-agent reports present and reviewed at V2
- README.md Validation Summary section populated with per-agent verdicts and per-validator results
- gate-decisions.md records V0..V3

CONFLICT RESOLUTION:
- PM findings disagree with Architect findings on the same artifact → escalate to user at V3; do not silently reconcile
- validate-trackers.py reports a rule that validate-feature-evidence.py owns → defer to the feature evidence validator (single source of truth per §22)
- validate-feature-evidence.py reports an error the operator believes is a validator defect → DO NOT bypass via --evidence-effective-date; route to the Phase 5 validator-defect fallback (record waivers.validator_defect in the affected feature manifest with follow-up; for in-progress features, log the defect as a mid-stage follow-up and create the waiver entry only when that feature reaches G8)
- registry-wide scan reports a pre-contract archived feature requiring evidence → check Evidence Reentry Date on that archived row; absence means no reentry claimed, so the requirement is the bug
