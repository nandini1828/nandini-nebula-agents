"""Phase 2b §23 closure additions.

Each test drives one of the 33 fixtures listed in §23 that were not
runnable until Phase 2b closeout. They are grouped by registry-level
rules, manifest schema rules, frontend-lane rules, artifact-reference
rules, and the cross-artifact reconciliation rules.
"""

from __future__ import annotations

import json
from pathlib import Path

from test_validate_feature_evidence import (
    RUN_ID,
    json_result,
    run_validator,
    write_manifest_run,
    write_registry,
)


# --------------------------------------------------------------------------- #
# Registry-level rules
# --------------------------------------------------------------------------- #


def test_reopened_historical_missing_evidence_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(
        product,
        archived="| F0001 | Reopened | 2026-03-10 | 2026-05-20 | `archive/F0001-reopened/` |",
    )
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "reopened_historical_missing_evidence_fails" in rules


def test_active_done_pre_contract_malformed_date_requires_evidence_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, active="| F0001 | Reopened | Done | MVP | `F0001-reopened/` |")
    feature_path = product / "planning-mds" / "features" / "F0001-reopened"
    feature_path.mkdir(parents=True)
    (feature_path / "STATUS.md").write_text(
        """# Status

**Overall Status:** Done

## Closeout Summary

| Field | Value |
|-------|-------|
| Closeout review date | not-a-date |
""",
        encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "active_done_pre_contract_malformed_date_requires_evidence_fails" in rules


# --------------------------------------------------------------------------- #
# Forced-role cross-checks
# --------------------------------------------------------------------------- #


def _override_required_roles(run_folder: Path, **overrides: object) -> None:
    """write_manifest_run auto-fills required_roles to keep positive tests
    correct; for negative tests we patch the manifest after the fact."""
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data.update(overrides)
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_deployment_changed_without_devops_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001")
    _override_required_roles(run_folder, deployment_config_changed=True, required_roles=["Quality Engineer", "Code Reviewer"])
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "deployment_changed_without_devops_fails" in rules


def test_security_true_without_security_role_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001")
    _override_required_roles(run_folder, security_sensitive_scope=True, required_roles=["Quality Engineer", "Code Reviewer"])
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "security_true_without_security_role_fails" in rules


# --------------------------------------------------------------------------- #
# PM-role-as-planning rule
# --------------------------------------------------------------------------- #


def test_pm_role_required_missing_report_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001")
    manifest_path = run_folder / "evidence-manifest.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    doc["role_results"]["Product Manager"] = {
        "required": True,
        "result": "APPROVED",
        "required_artifacts": ["pm-planning-review.md"],
        "verdict_artifact": "pm-planning-review.md",
    }
    manifest_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "pm_role_required_missing_report_fails" in rules


# --------------------------------------------------------------------------- #
# latest-run.json schema rules
# --------------------------------------------------------------------------- #


def test_latest_run_absolute_path_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", status="approved", latest=True, stage="closeout",
        manifest_updates={"status": "approved", "feature_state": "Archived", "feature_path_at_closeout": "planning-mds/features/archive/F0001-new"},
    )
    latest = run_folder.parent / "latest-run.json"
    data = json.loads(latest.read_text(encoding="utf-8"))
    data["run_path"] = "/abs/run/path"
    latest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "latest_run_absolute_path_fails" in rules


def test_latest_run_bad_status_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", status="approved", latest=True, stage="closeout",
        manifest_updates={"status": "approved", "feature_state": "Archived", "feature_path_at_closeout": "planning-mds/features/archive/F0001-new"},
    )
    latest = run_folder.parent / "latest-run.json"
    data = json.loads(latest.read_text(encoding="utf-8"))
    data["status"] = "draft"
    latest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "latest_run_bad_status_fails" in rules


# --------------------------------------------------------------------------- #
# manifest rerun_of rule
# --------------------------------------------------------------------------- #


def test_manifest_rerun_of_unknown_run_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product, "F0001-new", "F0001",
        manifest_updates={
            "rerun_of": "2025-01-01-00000000",
            "changed_paths": [],
            "scm": {"base_ref": "main", "head_ref": "feature/F0001", "diff_artifact": ""},
        },
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_rerun_of_unknown_run_fails" in rules


# --------------------------------------------------------------------------- #
# Frontend lane rules
# --------------------------------------------------------------------------- #


def test_frontend_global_ref_missing_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product, "F0001-new", "F0001",
        manifest_updates={
            "global_evidence_refs": {
                "frontend_quality": "planning-mds/operations/evidence/frontend-quality/latest-run.json",
            },
        },
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "frontend_global_ref_missing_fails" in rules


def test_frontend_quality_bad_latest_run_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    fq_path = product / "planning-mds" / "operations" / "evidence" / "frontend-quality" / "latest-run.json"
    fq_path.parent.mkdir(parents=True, exist_ok=True)
    fq_path.write_text(json.dumps({"schema_version": 1, "status": "draft"}), encoding="utf-8")
    write_manifest_run(
        product, "F0001-new", "F0001",
        manifest_updates={
            "global_evidence_refs": {
                "frontend_quality": "planning-mds/operations/evidence/frontend-quality/latest-run.json",
            },
        },
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "frontend_quality_bad_latest_run_fails" in rules


def test_frontend_ux_ref_missing_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product, "F0001-new", "F0001",
        manifest_updates={
            "global_evidence_refs": {
                "frontend_ux": ["planning-mds/operations/evidence/frontend-ux/ux-audit-2026-05-19.md"],
            },
        },
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "frontend_ux_ref_missing_fails" in rules


def test_frontend_true_without_feature_test_notes_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", stage="G2",
        manifest_updates={"frontend_in_scope": True, "changed_paths": ["experience/src/feature.tsx"]},
    )
    (run_folder / "test-execution-report.md").write_text("# Test Execution\n\nResult: PASS\n", encoding="utf-8")
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "frontend_true_without_feature_test_notes_fails" in rules


def test_frontend_global_substituted_for_feature_report_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", stage="G2",
        manifest_updates={"frontend_in_scope": True, "changed_paths": ["experience/src/feature.tsx"]},
    )
    (run_folder / "test-execution-report.md").write_text(
        "See frontend-quality lane: planning-mds/operations/evidence/frontend-quality/latest-run.json\n",
        encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "frontend_global_substituted_for_feature_report_fails" in rules


# --------------------------------------------------------------------------- #
# Tracker-results-at-G8 rule
# --------------------------------------------------------------------------- #


def test_stage_g8_requires_tracker_results_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", status="approved", latest=True, stage="closeout",
        manifest_updates={"status": "approved", "feature_state": "Archived", "feature_path_at_closeout": "planning-mds/features/archive/F0001-new"},
    )
    # Blank out the lifecycle log so no tracker-sync line exists.
    (run_folder / "lifecycle-gates.log").write_text("# Lifecycle Gate Run\n\n## Command\n\n## Stage\n\n## Exit Code\n\n## Result\n\n## Output References\n\n## Skipped Gates\n", encoding="utf-8")
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "stage_g8_requires_tracker_results_fails" in rules


# --------------------------------------------------------------------------- #
# Artifact-reference rules
# --------------------------------------------------------------------------- #


def test_coverage_claim_without_artifact_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    (run_folder / "coverage-report.md").write_text(
        "# Coverage\n\nResult: PASS\n\nRaw artifact: artifacts/coverage/cov.lcov\n", encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "coverage_claim_without_artifact_fails" in rules


def test_test_results_reference_missing_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    (run_folder / "test-execution-report.md").write_text(
        "# Test Execution\n\nResult: PASS\n\nArtifacts: artifacts/test-results/pnpm-test.log\n", encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "test_results_reference_missing_fails" in rules


def test_security_scan_reference_missing_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", stage="G3",
        manifest_updates={"security_sensitive_scope": True, "required_roles": ["Quality Engineer", "Code Reviewer", "Security Reviewer"]},
    )
    (run_folder / "security-review-report.md").write_text(
        "# Security Review\n\nResult: PASS\n\nScan output: artifacts/security/trivy.txt\n", encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G3", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "security_scan_reference_missing_fails" in rules


def test_screenshot_reference_missing_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    (run_folder / "test-execution-report.md").write_text(
        "# Test Execution\n\nResult: PASS\n\nScreenshot: artifacts/screenshots/landing.png\n", encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "screenshot_reference_missing_fails" in rules


# --------------------------------------------------------------------------- #
# Cross-artifact aliases
# --------------------------------------------------------------------------- #


def test_required_artifact_omitted_alias_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", stage="closeout", status="approved", latest=True,
        manifest_updates={"status": "approved", "feature_state": "Archived", "feature_path_at_closeout": "planning-mds/features/archive/F0001-new"},
    )
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["omissions"] = [{"artifact": "test-plan.md", "reason": "n/a", "approved_by": "PM", "approved_on": "2026-05-19"}]
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "required_artifact_omitted_fails" in rules
    assert "manifest_required_artifact_omitted_fails" in rules


def test_required_roles_mismatch_alias_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001")
    _override_required_roles(run_folder, deployment_config_changed=True, required_roles=["Quality Engineer", "Code Reviewer"])
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "required_roles_mismatch_fails" in rules


# --------------------------------------------------------------------------- #
# Signoff ledger disagree
# --------------------------------------------------------------------------- #


def test_signoff_ledger_disagrees_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", status="approved", latest=True, stage="closeout",
        manifest_updates={"status": "approved", "feature_state": "Archived", "feature_path_at_closeout": "planning-mds/features/archive/F0001-new"},
    )
    # Replace the signoff-ledger.md with empty content so STATUS.md current rows
    # are missing from the ledger.
    (run_folder / "signoff-ledger.md").write_text(
        "# Signoff\n\n## Required Role Matrix\n\n## Current Signoff State\n\n## Recommendation Acceptances\n\n## Waivers And Omissions\n\nResult: PASS\n",
        encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "signoff_ledger_disagrees_fails" in rules


# --------------------------------------------------------------------------- #
# changed_paths_mismatch
# --------------------------------------------------------------------------- #


def test_changed_paths_mismatch_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", stage="closeout", status="approved", latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "changed_paths": ["planning-mds/features/F0001-new"],
        },
    )
    (run_folder / "code-review-report.md").write_text(
        "# Code Review\n\nResult: APPROVED\n\nReviewed: engine/src/feature-handler.cs\n", encoding="utf-8",
    )
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "changed_paths_mismatch_fails" in rules


# --------------------------------------------------------------------------- #
# deferred_blocker_passes_fails
# --------------------------------------------------------------------------- #


def test_deferred_blocker_passes_fails(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product, "F0001-new", "F0001", stage="closeout", status="approved", latest=True,
        manifest_updates={"status": "approved", "feature_state": "Archived", "feature_path_at_closeout": "planning-mds/features/archive/F0001-new"},
    )
    (run_folder / "code-review-report.md").write_text(
        "# Code Review\n\nResult: APPROVED WITH RECOMMENDATIONS\n\n- [critical] SQL injection in raw query path — owner: BackendDev; follow-up: deferred-to-next-release\n",
        encoding="utf-8",
    )
    # pm-closeout has no mitigation acceptance for this critical recommendation.
    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "deferred_blocker_passes_fails" in rules


# --------------------------------------------------------------------------- #
# Retired-skip positive fixtures (count classification)
# --------------------------------------------------------------------------- #


def test_retired_abandoned_skipped_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(
        product,
        retired="| F0001 | Old Feature | Abandoned |  | 2026-03-01 | `archive/F0001-old/` | discontinued |",
    )
    result = run_validator(product, "--json")
    payload = json_result(result)
    assert result.returncode == 0
    assert payload["features_skipped_retired_abandoned"] == 1


def test_retired_superseded_skipped_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(
        product,
        retired="| F0001 | Old Feature | Superseded | F0002 | 2026-03-01 | `archive/F0001-old/` | replaced |",
    )
    result = run_validator(product, "--json")
    payload = json_result(result)
    assert result.returncode == 0
    assert payload["features_skipped_retired_superseded"] == 1


# --------------------------------------------------------------------------- #
# Path-class union and case-sensitivity positives
# --------------------------------------------------------------------------- #


def test_path_class_union_match_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    # engine/**/Migrations/** matches both the engine row and the migrations row;
    # union forces runtime_bearing AND deployment_config_changed.
    write_manifest_run(
        product, "F0001-new", "F0001",
        manifest_updates={
            "changed_paths": ["engine/src/Db/Migrations/0042_init.cs"],
            "runtime_bearing": True,
            "deployment_config_changed": True,
            "required_roles": ["Quality Engineer", "Code Reviewer", "DevOps"],
        },
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "scope_boolean_false_with_changed_paths_fails" not in rules


def test_path_class_case_sensitive_no_match_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    # `engine/auth/...` should NOT match `**/Auth*/**` because the validator
    # is case-sensitive. security_sensitive_scope stays false safely.
    write_manifest_run(
        product, "F0001-new", "F0001",
        manifest_updates={
            "changed_paths": ["engine/auth/foo.cs"],
            "runtime_bearing": True,
        },
    )
    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G0", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "scope_boolean_false_with_changed_paths_fails" not in rules
