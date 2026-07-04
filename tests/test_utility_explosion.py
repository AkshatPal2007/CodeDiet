"""Tests for the Utility Explosion detector.

The detector is a file-path-level heuristic: it fires when three or more
utility-named modules (utils.py, helpers.py, common.py, etc.) are found in
the scanned project.

Key invariants:
  - Threshold is 3 by default.
  - Fewer than threshold → no findings.
  - Exactly at threshold → fires.
  - Findings are REVIEW class, never FACT.
  - Each matched file gets its own Finding (so CI output is granular).
  - The message uses "Review Utility Growth" wording (per CLAUDE.md §7.6).
  - No forbidden words (score, risk, delete, remove, etc.) in any output.
"""


from codediet.detectors.utility_explosion import detect, _DEFAULT_THRESHOLD
from codediet.models import FindingClass


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _paths(*basenames: str) -> list[str]:
    """Build a list of display_paths from plain basenames."""
    return list(basenames)


def _prefixed(*basenames: str, prefix: str = "src/") -> list[str]:
    """Build a list of display_paths with a directory prefix."""
    return [prefix + b for b in basenames]


# ═══════════════════════════════════════════════════════════════════════════
# POSITIVE CASES
# ═══════════════════════════════════════════════════════════════════════════


class TestPositiveThreshold:
    """Verify the detector fires exactly at and above the default threshold."""

    def test_exactly_at_threshold(self):
        paths = _paths("utils.py", "helpers.py", "common.py")
        assert len(paths) == _DEFAULT_THRESHOLD
        findings = detect(paths)
        assert len(findings) == _DEFAULT_THRESHOLD

    def test_above_threshold(self):
        paths = _paths("utils.py", "helpers.py", "common.py", "misc.py")
        findings = detect(paths)
        assert len(findings) == 4

    def test_all_known_utility_names(self):
        paths = _paths(
            "utils.py", "util.py", "helpers.py", "helper.py",
            "common.py", "shared.py", "misc.py", "utilities.py",
            "tools.py", "funcs.py",
        )
        findings = detect(paths)
        assert len(findings) == len(paths)


class TestPositiveDirectoryPaths:
    """Detector matches on basename only — directory prefix is ignored."""

    def test_nested_paths_match(self):
        paths = _prefixed("utils.py", "helpers.py", "common.py")
        findings = detect(paths)
        assert len(findings) == 3

    def test_deeply_nested_paths_match(self):
        paths = [
            "myproject/core/utils.py",
            "myproject/api/helpers.py",
            "myproject/db/common.py",
        ]
        findings = detect(paths)
        assert len(findings) == 3

    def test_mixed_depth_paths(self):
        paths = [
            "utils.py",
            "src/helpers.py",
            "src/core/common.py",
            "main.py",
            "app.py",
        ]
        findings = detect(paths)
        assert len(findings) == 3


class TestPositiveFindingStructure:
    """Verify the Finding objects have the correct schema."""

    def test_finding_fields(self):
        paths = _paths("utils.py", "helpers.py", "common.py")
        findings = detect(paths)
        for f in findings:
            assert f.detector == "utility_explosion"
            assert f.classification == FindingClass.REVIEW
            assert f.line == 1
            assert isinstance(f.file, str)
            assert isinstance(f.message, str)
            assert isinstance(f.evidence, dict)

    def test_evidence_schema(self):
        paths = _paths("utils.py", "helpers.py", "common.py")
        findings = detect(paths)
        ev = findings[0].evidence
        assert "utility_files" in ev
        assert "count" in ev
        assert "threshold" in ev
        assert ev["count"] == 3
        assert ev["threshold"] == _DEFAULT_THRESHOLD
        assert set(ev["utility_files"]) == {"utils.py", "helpers.py", "common.py"}

    def test_message_wording(self):
        """CLAUDE.md §7.6: message must contain 'Review Utility Growth'."""
        paths = _paths("utils.py", "helpers.py", "common.py")
        findings = detect(paths)
        for f in findings:
            assert "Review Utility Growth" in f.message

    def test_message_contains_count(self):
        paths = _paths("utils.py", "helpers.py", "common.py", "misc.py")
        findings = detect(paths)
        for f in findings:
            assert "4" in f.message

    def test_no_forbidden_words_in_message(self):
        """Per CLAUDE.md §6.4: forbidden words must not appear in review messages."""
        paths = _paths("utils.py", "helpers.py", "common.py")
        findings = detect(paths)
        for f in findings:
            msg = f.message.lower()
            for word in ["delete", "remove", "dead", "unused", "duplicate",
                         "unsafe", "fix", "score", "risk", "%", "percent"]:
                assert word not in msg, (
                    f"Forbidden word '{word}' found in message: {f.message}"
                )

    def test_each_file_gets_own_finding(self):
        """Each matched utility file must produce its own Finding."""
        paths = _paths("utils.py", "helpers.py", "common.py")
        findings = detect(paths)
        finding_files = {f.file for f in findings}
        assert finding_files == {"utils.py", "helpers.py", "common.py"}


class TestPositiveCustomThreshold:
    """The threshold parameter is respected."""

    def test_threshold_of_2(self):
        paths = _paths("utils.py", "helpers.py")
        findings = detect(paths, threshold=2)
        assert len(findings) == 2

    def test_threshold_of_5(self):
        paths = _paths("utils.py", "helpers.py", "common.py", "misc.py")
        # Only 4 files — below threshold of 5
        assert len(detect(paths, threshold=5)) == 0

    def test_threshold_of_1_fires_on_single_file(self):
        """Threshold=1 effectively fires on any utility module found."""
        paths = _paths("utils.py", "main.py", "app.py")
        findings = detect(paths, threshold=1)
        assert len(findings) == 1
        assert findings[0].file == "utils.py"


# ═══════════════════════════════════════════════════════════════════════════
# NEGATIVE CASES — must NOT fire
# ═══════════════════════════════════════════════════════════════════════════


class TestNegativeBelowThreshold:
    """No findings below the default threshold of 3."""

    def test_zero_utility_files(self):
        paths = _paths("main.py", "app.py", "models.py")
        assert len(detect(paths)) == 0

    def test_one_utility_file(self):
        """A single utils.py is normal; should not fire."""
        paths = _paths("utils.py", "main.py", "app.py", "models.py")
        assert len(detect(paths)) == 0

    def test_two_utility_files(self):
        paths = _paths("utils.py", "helpers.py", "main.py")
        assert len(detect(paths)) == 0

    def test_empty_path_list(self):
        assert len(detect([])) == 0


class TestNegativeNonUtilityNames:
    """Files with utility-adjacent names that are NOT in the known set."""

    def test_similar_but_unlisted_names(self):
        paths = _paths("utility.py", "helper_funcs.py", "utils_v2.py")
        # None of these exactly match the known set
        assert len(detect(paths)) == 0

    def test_subdirectory_named_utils(self):
        """A path like 'utils/core.py' — basename is 'core.py', not 'utils.py'."""
        paths = [
            "utils/core.py",
            "helpers/base.py",
            "common/db.py",
            "main.py",
        ]
        assert len(detect(paths)) == 0

    def test_case_sensitive_matching(self):
        """Filenames are case-sensitive on most filesystems — 'Utils.py' != 'utils.py'."""
        paths = _paths("Utils.py", "Helpers.py", "Common.py")
        assert len(detect(paths)) == 0
