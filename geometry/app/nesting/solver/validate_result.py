"""Public validation wrapper — validates NestResult independently from solve."""

from __future__ import annotations

from ..geometry.validate import validate_solution
from ..models import NestJob, NestResult, PartSpec


def validate_nest_result(
    job: NestJob,
    result: NestResult,
) -> list[str]:
    """
    Validate a NestResult independently from the solver.
    Returns list of error strings; empty = valid.
    """
    return validate_solution(job, result, job.parts)
