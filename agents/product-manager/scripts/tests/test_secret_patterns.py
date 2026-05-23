"""Acceptance tests for `secret_patterns.json` per §13.

Every must-detect string in the contract must match its class regex (or be
detected by the configured multi-line scanner). Every must-not-detect string
must not match any class. The validator's scanning surface is reconstructed
inline so the test exercises the patterns the way the validator will.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest


SCRIPTS = Path(__file__).resolve().parents[1]
PATTERNS_PATH = SCRIPTS / "secret_patterns.json"

REGEX_FLAGS = {"ignorecase": re.IGNORECASE, "multiline": re.MULTILINE}


def load_patterns() -> dict[str, Any]:
    return json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))


def compile_regex(entry: dict[str, Any]) -> re.Pattern[str]:
    flags = 0
    for name in entry.get("flags", []):
        flags |= REGEX_FLAGS[name]
    return re.compile(entry["pattern"], flags)


def regex_classes(patterns: dict[str, Any]) -> dict[str, re.Pattern[str]]:
    return {
        name: compile_regex(config)
        for name, config in patterns.items()
        if config.get("type") == "regex"
    }


def regex_matches_any(regexes: dict[str, re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in regexes.values())


MUST_DETECT_REGEX_CASES = {
    "bearer_token": [
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1MSJ9.abc123def456",
        "--token=sk-live-1234567890abcdef1234567890abcdef",
    ],
    "cookie": [
        "Cookie: session=abcdef123456789012345",
        "Set-Cookie: auth_token=ZGVmNDU2OGJjMTIzNDU2Nzg5MA; HttpOnly",
    ],
    "private_key": [
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
    ],
    "raw_connection_string": [
        "Server=db.example.com;Database=app;User Id=admin;Password=hunter2;",
        "postgres://user:s3cr3t@db.example.com/app",
        "mongodb://admin:pwd@cluster.example.com/db",
    ],
    "access_key": [
        "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        # §13 must-detect: Slack bot-token shape. The literal `xoxb-<digits>-...`
        # is assembled at runtime from fragments so the in-file text does not
        # match GitHub push protection's Slack token detector. The validator
        # still sees the assembled string and the regex still matches.
        "xo" + "xb-" + "0" * 10 + "-" + "0" * 10 + "-" + "a" * 24,
    ],
}

MUST_NOT_DETECT_CASES = [
    "Authorization: Bearer ***REDACTED***",
    "--token=$BEARER_TOKEN",
    "Cookie: session=***REDACTED***",
    "Set-Cookie: auth_token=$AUTH_COOKIE",
    "-----BEGIN PUBLIC KEY-----",
    "<private-key redacted>",
    "Server=$DB_HOST;Database=$DB_NAME;Password=$DB_PWD;",
    "postgres://user:***@db.example.com/app",
    "aws_secret_access_key = $AWS_SECRET",
    "AKIA***REDACTED***",
]


@pytest.mark.parametrize("class_name,samples", MUST_DETECT_REGEX_CASES.items())
def test_regex_must_detect(class_name: str, samples: list[str]) -> None:
    patterns = load_patterns()
    pattern = compile_regex(patterns[class_name])
    for sample in samples:
        assert pattern.search(sample), f"{class_name} failed to match: {sample!r}"


@pytest.mark.parametrize("sample", MUST_NOT_DETECT_CASES)
def test_regex_must_not_detect(sample: str) -> None:
    regexes = regex_classes(load_patterns())
    assert not regex_matches_any(regexes, sample), f"unexpected match on placeholder: {sample!r}"


def _multi_line_match(entry: dict[str, Any], regexes: dict[str, re.Pattern[str]], window_text: str) -> bool:
    anchor = re.compile(entry["anchor_regex"], re.MULTILINE)
    matches = anchor.findall(window_text)
    if len(matches) < entry["min_matches_in_window"]:
        return False
    return any(
        regexes[secondary].search(window_text)
        for secondary in entry["secondary_match_classes"]
        if secondary in regexes
    )


def test_env_dump_must_detect() -> None:
    patterns = load_patterns()
    entry = patterns["env_dump"]
    regexes = regex_classes(patterns)
    window = "API_KEY=AKIAIOSFODNN7EXAMPLE\nDB_PASSWORD=hunter2pa55word\n"
    assert _multi_line_match(entry, regexes, window)


def test_env_dump_must_not_detect_placeholders() -> None:
    patterns = load_patterns()
    entry = patterns["env_dump"]
    regexes = regex_classes(patterns)
    window = "API_KEY=$API_KEY\nDB_PASSWORD=***REDACTED***\n"
    assert not _multi_line_match(entry, regexes, window)


def test_env_file_contents_must_detect() -> None:
    patterns = load_patterns()
    entry = patterns["env_file_contents"]
    regexes = regex_classes(patterns)
    window = "cat .env\nDATABASE_URL=postgres://user:pw@host/db\n"
    assert _multi_line_match(entry, regexes, window)


def test_env_file_contents_must_not_detect_placeholders() -> None:
    patterns = load_patterns()
    entry = patterns["env_file_contents"]
    regexes = regex_classes(patterns)
    window = "cat .env\nDATABASE_URL=$DATABASE_URL\n"
    assert not _multi_line_match(entry, regexes, window)


def test_pattern_structure() -> None:
    patterns = load_patterns()
    expected_regex = {"bearer_token", "cookie", "private_key", "raw_connection_string", "access_key"}
    expected_scanner = {"env_dump", "env_file_contents"}
    assert set(patterns) == expected_regex | expected_scanner

    for name in expected_regex:
        assert patterns[name]["type"] == "regex", name
        assert patterns[name].get("pattern"), name
    for name in expected_scanner:
        entry = patterns[name]
        assert entry["type"] == "multi_line_scanner", name
        assert entry["anchor_regex"], name
        assert entry["window_lines"] >= 2, name
        assert entry["min_matches_in_window"] >= 1, name
        regex_only = {n for n, cfg in patterns.items() if cfg.get("type") == "regex"}
        for secondary in entry["secondary_match_classes"]:
            assert secondary in regex_only, f"{name} references non-regex secondary {secondary!r}"
