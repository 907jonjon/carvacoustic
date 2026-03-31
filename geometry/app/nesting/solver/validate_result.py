"""Public validation API — validates NestResult independently from solve."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..geometry.validate import validate_solution
from ..models import NestJob, NestResult


@dataclass
class ValidationReport:
    """Structured validation report for a nesting result."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_parts_placed: int = 0
    sheets_used: int = 0
    avg_utilization: float = 0.0


def validate_nest(job: NestJob, result: NestResult) -> ValidationReport:
    """
    Validate a nesting result independently from the solver.
    Use this to check imported or manually edited placements.

    Returns a ValidationReport with structured errors, warnings, and stats.
    """
    errors = validate_solution(job, result, job.parts)
    warnings: list[str] = []

    # Add warnings for low utilization or unplaced parts
    if result.unplaced:
        warnings.append(f"{len(result.unplaced)} part(s) could not be placed")
    if result.utilization < 0.1 and result.placements:
        warnings.append(f"Low utilization: {result.utilization:.1%}")

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        total_parts_placed=len(result.placements),
        sheets_used=result.sheets_used,
        avg_utilization=result.utilization,
    )
