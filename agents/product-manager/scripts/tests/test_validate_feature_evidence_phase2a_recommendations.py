"""Phase 2a residual tests: §15 recommendation structure, PM acceptance consumers,
and STATUS.md recommendation/story-breakdown rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from test_validate_feature_evidence import (
    REPO_ROOT,
    RUN_ID,
    ROLE_FILES,
    json_result,
    run_validator,
    write_manifest_run,
    write_registry,
)


def _write_role_report(
    run_folder: Path,
    filename: str,
    verdict: str,
    recommendations_block: str = "",
) -> None:
    """Replace a role report with content carrying the given verdict and recs."""
    content = f"# {filename}\n\n## Recommendations\n\n{recommendations_block}\n\nResult: {verdict}\n"
    (run_folder / filename).write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------- #
# §15 recommendation parser + structure
# --------------------------------------------------------------------------- #


def test_recommendation_missing_severity_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    _write_role_report(
        run_folder,
        "test-execution-report.md",
        "PASS WITH RECOMMENDATIONS",
        "- Speed up CI lane — owner: QE; follow-up: deferred-no-followup\n",
    )

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "recommendation_missing_severity_fails" in rules


def test_recommendation_missing_owner_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    _write_role_report(
        run_folder,
        "test-execution-report.md",
        "PASS WITH RECOMMENDATIONS",
        "- [low] Reduce flake rate\n",
    )

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "recommendation_missing_owner_fails" in rules
    assert "recommendation_ambiguous_fails" in rules


def test_recommendation_ambiguous_when_no_bullets(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    _write_role_report(
        run_folder,
        "test-execution-report.md",
        "PASS WITH RECOMMENDATIONS",
        "We recommend faster CI, but with no bullet structure.\n",
    )

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "recommendation_ambiguous_fails" in rules


def test_recommendation_with_disposition_passes_at_g2(tmp_path: Path) -> None:
    """A well-formed [low]/[medium] recommendation with disposition is fine pre-closeout."""
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    _write_role_report(
        run_folder,
        "test-execution-report.md",
        "PASS WITH RECOMMENDATIONS",
        "- [low] Reduce flake rate — owner: QE; follow-up: deferred-no-followup\n",
    )
    # Manifest role_results result must also be a passing value when WITH RECOMMENDATIONS used.
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["role_results"]["Quality Engineer"]["result"] = "PASS WITH RECOMMENDATIONS"
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "recommendation_missing_severity_fails" not in rules
    assert "recommendation_missing_owner_fails" not in rules
    assert "recommendation_ambiguous_fails" not in rules


def test_blocking_language_with_pass_fires_at_closeout(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
        },
    )
    _write_role_report(
        run_folder,
        "code-review-report.md",
        "APPROVED WITH RECOMMENDATIONS",
        "- [critical] SQL injection in raw query path — owner: BackendDev; follow-up: NEB-1234\n",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "blocking_language_with_pass_fails" in rules


def test_blocking_language_with_mitigation_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
        },
    )
    _write_role_report(
        run_folder,
        "code-review-report.md",
        "APPROVED WITH RECOMMENDATIONS",
        "- [high] Refactor permissions check — owner: BackendDev; follow-up: NEB-1234\n",
    )
    pm = run_folder / "pm-closeout.md"
    pm.write_text(
        ROLE_FILES["pm-closeout.md"]
        + "\n- Accepted: Refactor permissions check — mitigation: scoped to next release; tracked NEB-1234\n",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "blocking_language_with_pass_fails" not in rules


def test_recommendation_no_pm_acceptance_fires_at_closeout(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
        },
    )
    _write_role_report(
        run_folder,
        "test-execution-report.md",
        "PASS WITH RECOMMENDATIONS",
        "- [medium] Add accessibility tests for keyboard nav — owner: QE; follow-up: NEB-9000\n",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "recommendation_no_pm_acceptance_fails" in rules


def test_recommendation_with_pm_acceptance_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
        },
    )
    _write_role_report(
        run_folder,
        "test-execution-report.md",
        "PASS WITH RECOMMENDATIONS",
        "- [medium] Add accessibility tests for keyboard nav — owner: QE; follow-up: NEB-9000\n",
    )
    pm = run_folder / "pm-closeout.md"
    pm.write_text(
        ROLE_FILES["pm-closeout.md"]
        + "\n- Accepted: Add accessibility tests for keyboard nav — deferred to NEB-9000; 2026-05-19\n",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "recommendation_no_pm_acceptance_fails" not in rules
    assert "recommendation_ambiguous_fails" not in rules


# --------------------------------------------------------------------------- #
# Coverage waiver acceptance
# --------------------------------------------------------------------------- #


def test_coverage_waiver_missing_pm_acceptance_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "waivers": {"coverage": {"required": False, "reason": "doc-only", "owner": "QE", "approved_on": "2026-05-19", "follow_up": "None"}},
        },
    )
    # coverage-report.md must reference the waiver to avoid manifest_waiver_without_report_fails.
    (run_folder / "coverage-report.md").write_text(
        "# Coverage\n\nCoverage is waived for this feature.\n\nResult: PASS\n",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "coverage_waiver_missing_pm_acceptance_fails" in rules


def test_coverage_waiver_with_pm_acceptance_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "waivers": {"coverage": {"required": False, "reason": "doc-only", "owner": "QE", "approved_on": "2026-05-19", "follow_up": "None"}},
        },
    )
    (run_folder / "coverage-report.md").write_text(
        "# Coverage\n\nCoverage is waived for this feature.\n\nResult: PASS\n",
        encoding="utf-8",
    )
    pm = run_folder / "pm-closeout.md"
    pm.write_text(
        ROLE_FILES["pm-closeout.md"]
        + "\n- Accepted: coverage — Waived for documentation-only feature; 2026-05-19\n",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "coverage_waiver_missing_pm_acceptance_fails" not in rules


# --------------------------------------------------------------------------- #
# validator_defect waiver
# --------------------------------------------------------------------------- #


def test_validator_defect_waiver_missing_field_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "waivers": {
                "validator_defect": {
                    "defect_description": "False positive",
                    "affected_rule_ids": ["manifest_changed_path_traversal_fails"],
                    "approved_by": "PM",
                    "approved_on": "2026-05-19",
                    # follow_up_owner missing
                    "follow_up_target_date": "2026-06-15",
                }
            },
        },
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "validator_defect_waiver_missing_followup_fails" in rules


def test_validator_defect_waiver_missing_pm_mirror_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "waivers": {
                "validator_defect": {
                    "defect_description": "False positive",
                    "affected_rule_ids": ["manifest_changed_path_traversal_fails"],
                    "approved_by": "PM",
                    "approved_on": "2026-05-19",
                    "follow_up_owner": "framework-team",
                    "follow_up_target_date": "2026-06-15",
                }
            },
        },
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "validator_defect_waiver_missing_followup_fails" in rules


def test_validator_defect_waiver_target_before_recorded_on_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "recorded_on": "2026-05-19",
            "waivers": {
                "validator_defect": {
                    "defect_description": "False positive",
                    "affected_rule_ids": ["manifest_changed_path_traversal_fails"],
                    "approved_by": "PM",
                    "approved_on": "2026-05-19",
                    "follow_up_owner": "framework-team",
                    "follow_up_target_date": "2026-04-01",  # before recorded_on
                }
            },
        },
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "validator_defect_waiver_missing_followup_fails" in rules


def test_validator_defect_waiver_full_passes(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
            "waivers": {
                "validator_defect": {
                    "defect_description": "False positive on quoted path",
                    "affected_rule_ids": ["manifest_changed_path_traversal_fails"],
                    "approved_by": "PM",
                    "approved_on": "2026-05-19",
                    "follow_up_owner": "framework-team",
                    "follow_up_target_date": "2026-06-15",
                }
            },
        },
    )
    pm = run_folder / "pm-closeout.md"
    pm.write_text(
        ROLE_FILES["pm-closeout.md"]
        + "\n## Validator Defects\n\n- Accepted: manifest_changed_path_traversal_fails — defect: quoted-path FP; target: 2026-06-15\n",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "validator_defect_waiver_missing_followup_fails" not in rules


# --------------------------------------------------------------------------- #
# STATUS.md residuals
# --------------------------------------------------------------------------- #


def test_status_story_value_unknown_story_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
        },
    )
    # Add a local story file for F0001-S0001 but STATUS.md will reference F0001-S0099.
    feature_path = product / "planning-mds" / "features" / "archive" / "F0001-new"
    (feature_path / "F0001-S0001-real-story.md").write_text("# Real story\n", encoding="utf-8")
    status_path = feature_path / "STATUS.md"
    status_path.write_text(
        f"""# Status

## Required Role Matrix

| Role | Required |
|------|----------|
| Quality Engineer | Yes |
| Code Reviewer | Yes |

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|-------|------|----------|---------|----------|------|-------|
| F0001-S0099 | Quality Engineer | reviewer | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-19 | - |
| F0001-S0099 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_story_value_unknown_story_fails" in rules


def test_status_recommendation_without_acceptance_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="closeout",
        status="approved",
        latest=True,
        manifest_updates={
            "status": "approved",
            "feature_state": "Archived",
            "feature_path_at_closeout": "planning-mds/features/archive/F0001-new",
        },
    )
    feature_path = product / "planning-mds" / "features" / "archive" / "F0001-new"
    status_path = feature_path / "STATUS.md"
    status_path.write_text(
        f"""# Status

## Required Role Matrix

| Role | Required |
|------|----------|
| Quality Engineer | Yes |
| Code Reviewer | Yes |

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|-------|------|----------|---------|----------|------|-------|
| F0001-S0001 | Quality Engineer | reviewer | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-19 | - |
| F0001-S0001 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_recommendation_without_acceptance_fails" in rules
