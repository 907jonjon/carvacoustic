"""Benchmark reports — markdown tables and comparison views."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runner import BenchmarkResult


def generate_report(results: list["BenchmarkResult"]) -> str:
    """Generate a markdown benchmark report table."""
    lines = [
        "# Nesting Benchmark Report\n",
        "| Dataset | Mode | Sheets | Util% | Runtime(ms) | Valid | Unplaced |",
        "|---------|------|--------|-------|-------------|-------|----------|",
    ]
    for r in results:
        valid_str = "yes" if r.valid else "NO"
        lines.append(
            f"| {r.dataset} | {r.mode} | {r.sheets_used} | "
            f"{r.utilization:.1%} | {r.runtime_ms:.0f} | "
            f"{valid_str} | {r.unplaced_count} |"
        )
    lines.append("")
    return "\n".join(lines)


def compare_reports(
    baseline: list["BenchmarkResult"],
    current: list["BenchmarkResult"],
) -> str:
    """
    Generate a comparison report showing deltas between baseline and current.
    Highlights regressions (more sheets or lower utilization).
    """
    # Index baseline by (dataset, mode)
    base_map = {(r.dataset, r.mode): r for r in baseline}

    lines = [
        "# Nesting Benchmark Comparison\n",
        "| Dataset | Mode | Sheets (Δ) | Util% (Δ) | Runtime (Δ) | Regressed? |",
        "|---------|------|------------|-----------|-------------|------------|",
    ]

    for r in current:
        key = (r.dataset, r.mode)
        b = base_map.get(key)
        if b is None:
            lines.append(
                f"| {r.dataset} | {r.mode} | {r.sheets_used} (new) | "
                f"{r.utilization:.1%} | {r.runtime_ms:.0f} | — |"
            )
            continue

        d_sheets = r.sheets_used - b.sheets_used
        d_util = r.utilization - b.utilization
        d_time = r.runtime_ms - b.runtime_ms

        regressed = d_sheets > 0 or d_util < -0.02
        flag = "**YES**" if regressed else "no"

        sheets_str = f"{r.sheets_used} ({d_sheets:+d})" if d_sheets != 0 else str(r.sheets_used)
        util_str = f"{r.utilization:.1%} ({d_util:+.1%})" if abs(d_util) > 0.001 else f"{r.utilization:.1%}"
        time_str = f"{r.runtime_ms:.0f} ({d_time:+.0f})" if abs(d_time) > 1 else f"{r.runtime_ms:.0f}"

        lines.append(
            f"| {r.dataset} | {r.mode} | {sheets_str} | "
            f"{util_str} | {time_str} | {flag} |"
        )

    lines.append("")
    return "\n".join(lines)
