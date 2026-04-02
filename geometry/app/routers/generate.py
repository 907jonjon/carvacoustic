"""
POST /generate — full geometry pipeline for Milestone B.
POST /generate-stream — same pipeline with SSE progress events.
"""

import asyncio
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..auth import require_api_key
from ..geometry.pipeline import run_pipeline
from ..models import GenerateRequest, GenerateResult

router = APIRouter(prefix="/generate", tags=["generate"])

STEP_PERCENTS = {1: 5, 2: 15, 3: 30, 4: 38, 5: 42, 6: 52, 7: 62, 8: 100}


@router.post("", response_model=GenerateResult, dependencies=[Depends(require_api_key)])
async def generate(request: GenerateRequest) -> GenerateResult:
    """
    Run the geometry pipeline (steps 1–9 of spec 02-geometry-spec.md).
    Returns SVG preview string and validation report.
    Layout (step 10) and export bundle assembly (step 11) are separate endpoints.
    """
    return run_pipeline(request.config)


@router.post("-stream", dependencies=[Depends(require_api_key)])
async def generate_stream(request: GenerateRequest):
    """Run the geometry pipeline with SSE progress events."""
    queue: Queue = Queue()

    def progress_callback(step: int, total: int, name: str) -> None:
        queue.put(("progress", {
            "step": step,
            "totalSteps": total,
            "name": name,
            "percent": STEP_PERCENTS.get(step, 0),
        }))

    async def event_generator():
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        future = loop.run_in_executor(
            executor, run_pipeline, request.config, progress_callback
        )

        while not future.done():
            try:
                while True:
                    event_type, data = queue.get_nowait()
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            except Empty:
                pass
            await asyncio.sleep(0.1)

        # Drain remaining progress events
        try:
            while True:
                event_type, data = queue.get_nowait()
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        except Empty:
            pass

        try:
            result = future.result()
            yield f"event: result\ndata: {result.model_dump_json()}\n\n"
        except Exception as exc:
            tb = traceback.format_exc()
            yield f"event: error\ndata: {json.dumps({'code': 'pipeline_error', 'message': str(exc), 'traceback': tb})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
