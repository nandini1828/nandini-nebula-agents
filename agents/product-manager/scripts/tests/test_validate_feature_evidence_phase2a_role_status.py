"""Phase 2a tests for §11 role/gate verdicts and §16 STATUS.md."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from test_validate_feature_evidence import (
    RUN_ID,
    ROLE_FILES,
    json_result,
    run_validator,
    write_manifest_run,
    write_registry,
    write_status_md,
)


# --------------------------------------------------------------------------- #
# §11 role / gate verdict checks
# --------------------------------------------------------------------------- #


def test_manifest_missing_gate_results_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="G2",
        manifest_updates={"gate_results": {}},
    )
    # Re-empty gate_results post default-fill by writing back.
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["gate_results"] = {}
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_missing_gate_results_fails" in rules


def test_gate_verdict_mismatch_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["gate_results"]["self_review"]["result"] = "FAIL"
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "gate_verdict_mismatch_fails" in rules


def test_manifest_role_results_mismatch_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["role_results"]["Quality Engineer"]["required_artifacts"] = ["test-plan.md"]  # missing the others
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_role_results_mismatch_fails" in rules


def test_role_verdict_mismatch_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["role_results"]["Quality Engineer"]["result"] = "FAIL"
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "role_verdict_mismatch_fails" in rules


def test_manifest_required_roles_mismatch_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="G3",
        manifest_updates={"security_sensitive_scope": True, "required_roles": ["Quality Engineer", "Code Reviewer"]},
    )
    # Drop Security Reviewer from declared required_roles even though scope forces it.
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["required_roles"] = ["Quality Engineer", "Code Reviewer"]
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G3", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_required_roles_mismatch_fails" in rules


def test_manifest_required_artifact_omitted_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["omissions"] = [{
        "artifact": "test-plan.md",
        "reason": "n/a",
        "approved_by": "PM",
        "approved_on": "2026-05-19",
    }]
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_required_artifact_omitted_fails" in rules


def test_manifest_global_ref_missing_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["global_evidence_refs"] = {"frontend_quality": "planning-mds/operations/evidence/frontend-quality/latest-run.json"}
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_global_ref_missing_fails" in rules


def test_manifest_file_path_missing_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(product, "F0001-new", "F0001", stage="G2")
    manifest_path = run_folder / "evidence-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["files"] = {"phantom": "nonexistent-file.md"}
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_file_path_missing_fails" in rules


def test_manifest_waiver_without_report_fires(tmp_path: Path) -> None:
    product = tmp_path / "product"
    write_registry(product, archived="| F0001 | New Feature | 2026-05-19 |  | `archive/F0001-new/` |")
    run_folder = write_manifest_run(
        product,
        "F0001-new",
        "F0001",
        stage="G2",
        manifest_updates={
            "waivers": {
                "coverage": {"required": True, "reason": "no impl coverage", "owner": "QE", "approved_on": "2026-05-19", "follow_up": "None"}
            },
        },
    )
    # coverage-report.md was written without the word "waive" in the default template,
    # so the manifest waiver isn't mirrored.

    result = run_validator(product, "--feature", "F0001", "--run-id", RUN_ID, "--stage", "G2", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "manifest_waiver_without_report_fails" in rules


# --------------------------------------------------------------------------- #
# §16 STATUS.md
# --------------------------------------------------------------------------- #


def test_status_missing_baseline_role_fires(tmp_path: Path) -> None:
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
    # Overwrite STATUS.md with only Code Reviewer required (missing baseline QE).
    feature_path = product / "planning-mds" / "features" / "archive" / "F0001-new"
    write_status_md(feature_path, "F0001", f"planning-mds/operations/evidence/F0001-new/{RUN_ID}", ["Code Reviewer"], stage="closeout")

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_missing_baseline_role_fails" in rules


def test_status_missing_forced_role_fires(tmp_path: Path) -> None:
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
            "security_sensitive_scope": True,
        },
    )
    # STATUS.md without Security Reviewer in Required Role Matrix.
    feature_path = product / "planning-mds" / "features" / "archive" / "F0001-new"
    write_status_md(feature_path, "F0001", f"planning-mds/operations/evidence/F0001-new/{RUN_ID}", ["Quality Engineer", "Code Reviewer"], stage="closeout")

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_missing_forced_role_fails" in rules


def test_status_bad_date_fires(tmp_path: Path) -> None:
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
| F0001-S0001 | Quality Engineer | reviewer | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | not-a-date | - |
| F0001-S0001 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_bad_date_fails" in rules


def test_status_missing_reviewer_fires(tmp_path: Path) -> None:
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
| F0001-S0001 | Quality Engineer |  | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-19 | - |
| F0001-S0001 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_missing_reviewer_fails" in rules


def test_status_story_value_bad_format_fires(tmp_path: Path) -> None:
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
| story-one | Quality Engineer | reviewer | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-19 | - |
| F0001-S0001 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_story_value_bad_format_fails" in rules


def test_status_evidence_missing_file_fires(tmp_path: Path) -> None:
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
| F0001-S0001 | Quality Engineer | reviewer | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/no-such-file.md | 2026-05-19 | - |
| F0001-S0001 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_evidence_missing_file_fails" in rules


def test_status_story_missing_role_fires(tmp_path: Path) -> None:
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
    # Write STATUS.md with only QE row — Code Reviewer is missing for the story.
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
| F0001-S0001 | Quality Engineer | reviewer | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_story_missing_role_fails" in rules


def test_status_stale_pass_followed_by_fail_fires(tmp_path: Path) -> None:
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
| F0001-S0001 | Quality Engineer | reviewer | PASS | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-19 | - |
| F0001-S0001 | Quality Engineer | reviewer | FAIL | planning-mds/operations/evidence/F0001-new/{RUN_ID}/test-execution-report.md | 2026-05-20 | regression |
| F0001-S0001 | Code Reviewer | reviewer | APPROVED | planning-mds/operations/evidence/F0001-new/{RUN_ID}/code-review-report.md | 2026-05-19 | - |
""",
        encoding="utf-8",
    )

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    rules = {entry["rule_id"] for entry in json_result(result)["errors"]}
    assert "status_stale_pass_followed_by_fail_fails" in rules


def test_status_complete_closeout_passes(tmp_path: Path) -> None:
    """Smoke test — a fully populated STATUS.md should not fire any §16 rule."""
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

    result = run_validator(product, "--feature", "F0001", "--stage", "closeout", "--json")
    assert result.returncode == 0, result.stdout
