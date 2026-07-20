"""Pytest bootstrap and Motion Engine certification console report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    """Print a clean pass/fail certification matrix for test_system checks."""
    # Local import avoids circular import during early collection.
    try:
        from tests.test_system import CERTIFICATION_CHECKS
    except Exception:
        try:
            from test_system import CERTIFICATION_CHECKS  # type: ignore
        except Exception:
            return

    reported = terminalreporter.stats
    outcomes: dict[str, str] = {}
    for outcome, reports in reported.items():
        if outcome not in {"passed", "failed", "error", "skipped", "xfailed", "xpassed"}:
            continue
        for report in reports:
            # report.nodeid like tests/test_system.py::TestMotionEngineSystem::test_01_...
            nodeid = getattr(report, "nodeid", "")
            name = nodeid.split("::")[-1] if nodeid else ""
            if name.startswith("test_"):
                outcomes[name] = outcome

    # Only emit the certification board when system tests were collected/run.
    relevant = [name for name, _ in CERTIFICATION_CHECKS if name in outcomes]
    if not relevant:
        return

    width = 72
    terminalreporter.write_sep("=", "Motion Engine Foundation Certification")
    terminalreporter.write_line("")
    terminalreporter.write_line(f"{'#':<4} {'RESULT':<8} CHECK")
    terminalreporter.write_line("-" * width)

    passed = failed = skipped = other = 0
    for index, (test_name, description) in enumerate(CERTIFICATION_CHECKS, start=1):
        result = outcomes.get(test_name, "not_run")
        if result == "passed":
            label = "PASS"
            passed += 1
        elif result in {"failed", "error"}:
            label = "FAIL"
            failed += 1
        elif result == "skipped":
            label = "SKIP"
            skipped += 1
        else:
            label = result.upper()[:8]
            other += 1
        terminalreporter.write_line(
            f"{index:<4} {label:<8} {description}"
        )

    terminalreporter.write_line("-" * width)
    terminalreporter.write_line(
        f"Summary: {passed} passed, {failed} failed, "
        f"{skipped} skipped, {other} other / {len(CERTIFICATION_CHECKS)} checks"
    )
    if failed == 0 and passed == len(CERTIFICATION_CHECKS):
        terminalreporter.write_line(
            "STATUS: CERTIFIED - Motion Engine foundation is ready for "
            "Skeleton Builder / visualization work."
        )
    elif failed == 0:
        terminalreporter.write_line(
            "STATUS: PARTIAL - no failures, but not all certification checks ran."
        )
    else:
        terminalreporter.write_line(
            "STATUS: NOT CERTIFIED - fix failing checks before Skeleton Builder work."
        )
    terminalreporter.write_line("")
