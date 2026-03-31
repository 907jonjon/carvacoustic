"""Benchmark runner — run solver across datasets and collect metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..models import NestJob
from ..solver.solve import solve_nest
from ..solver.validate_result import validate_nest
from .datasets import load_all_fixtures, generate_synthetic_dataset
from .reports import generate_report


@dataclass
class BenchmarkResult:
    dataset: str
    mode: str
    seed: int
    sheets_used: int
    utilization: float
    runtime_ms: float
    unplaced_count: int
    valid: bool
    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_benchmark(
    job: NestJob,
    dataset_name: str,
    mode: str = "balanced",
    seed: int = 42,
) -> BenchmarkResult:
    """Run the solver on a single job and collect metrics."""
    t0 = time.monotonic()
    result = solve_nest(job, mode=mode, seed=seed)
    elapsed = (time.monotonic() - t0) * 1000

    report = validate_nest(job, result)

    return BenchmarkResult(
        dataset=dataset_name,
        mode=mode,
        seed=seed,
        sheets_used=result.sheets_used,
        utilization=result.utilization,
        runtime_ms=elapsed,
        unplaced_count=len(result.unplaced),
        valid=report.valid,
        validation_errors=report.errors,
        warnings=result.warnings,
    )


def run_all_benchmarks(
    modes: list[str] | None = None,
    seed: int = 42,
) -> list[BenchmarkResult]:
    """Run all internal datasets across all modes."""
    if modes is None:
        modes = ["fast", "balanced", "max_yield"]

    results: list[BenchmarkResult] = []

    # Load fixture-based datasets
    fixtures = load_all_fixtures()
    for name, job in fixtures.items():
        for mode in modes:
            result = run_benchmark(job, name, mode=mode, seed=seed)
            results.append(result)

    # Synthetic datasets
    for complexity in ["simple", "medium", "complex"]:
        n_parts = {"simple": 10, "medium": 15, "complex": 8}[complexity]
        job = generate_synthetic_dataset(n_parts, complexity=complexity, seed=seed)
        for mode in modes:
            result = run_benchmark(job, f"synthetic_{complexity}", mode=mode, seed=seed)
            results.append(result)

    return results


if __name__ == "__main__":
    print("Running nesting benchmarks...\n")
    results = run_all_benchmarks()
    report = generate_report(results)
    print(report)
