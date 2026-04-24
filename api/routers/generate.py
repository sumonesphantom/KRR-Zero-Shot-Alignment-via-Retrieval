"""POST /api/generate/judge — SSE stream of the 3-LLM (Knowledge / Style / Judge) loop."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from api.schemas.generate import GenerateRequest
from api.services import judge_service
from api.settings import get_settings
from api.streaming.bus import run_with_event_stream


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generate")


_judge_semaphore = asyncio.Semaphore(get_settings().MAX_CONCURRENT_JUDGE_RUNS)


@router.post("/judge")
async def judge_generate(req: GenerateRequest, request: Request):
    """SSE stream. Events: retrieval, draft, style_attempt_start, style_attempt,
    judge_verdict, final, error. Terminal events: final | error.
    """
    async def event_source():
        async with _judge_semaphore:
            try:
                orch = await judge_service.get_orchestrator()
            except FileNotFoundError as e:
                yield _sse_error("INDEX_MISSING", str(e))
                return
            except Exception as e:
                logger.exception("Failed to build Orchestrator")
                yield _sse_error("ORCHESTRATOR_INIT", f"{type(e).__name__}: {e}")
                return

            def blocking_run(on_event):
                orch.run(
                    query=req.query,
                    preference=req.preference,
                    top_k=req.top_k,
                    on_event=on_event,
                )

            try:
                async for ev in run_with_event_stream(blocking_run):
                    if await request.is_disconnected():
                        logger.info("SSE client disconnected; detaching stream")
                        break
                    yield {
                        "event": ev.get("type", "message"),
                        "data": json.dumps(ev),
                    }
            except Exception as e:
                logger.exception("SSE stream failed")
                yield _sse_error("STREAM_FAILURE", f"{type(e).__name__}: {e}")

    return EventSourceResponse(
        event_source(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _sse_error(code: str, message: str) -> dict:
    return {
        "event": "error",
        "data": json.dumps({"type": "error", "code": code, "message": message}),
    }
