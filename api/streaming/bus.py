"""Thread-to-async bridge for the synchronous Orchestrator.run() loop.

The orchestrator is blocking. FastAPI handlers are async. We run the loop on a
worker thread (via asyncio.to_thread) and marshall events back to the event
loop via loop.call_soon_threadsafe so the SSE handler can yield them.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable


SENTINEL_DONE = object()


async def run_with_event_stream(
    blocking_fn: Callable[[Callable[[dict], None]], Any],
    *,
    queue_maxsize: int = 0,
) -> AsyncIterator[dict]:
    """Run `blocking_fn(on_event)` in a thread; yield each event as it arrives.

    Pushes a terminal `{"type": "final", ...}` or `{"type": "error", ...}` event
    before returning — callers don't need to track the stream end separately.
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=queue_maxsize)

    def on_event(ev: dict):
        loop.call_soon_threadsafe(queue.put_nowait, ev)

    async def _runner():
        try:
            await asyncio.to_thread(blocking_fn, on_event)
        except Exception as e:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"type": "error", "code": "ORCHESTRATOR_EXCEPTION", "message": str(e)},
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, SENTINEL_DONE)

    task = asyncio.create_task(_runner())

    try:
        while True:
            ev = await queue.get()
            if ev is SENTINEL_DONE:
                break
            yield ev
            if ev.get("type") in ("final", "error"):
                # Drain until task completes so we don't leak it.
                continue
    finally:
        if not task.done():
            # If the consumer disconnected early, the Orchestrator thread is
            # still running; we can't interrupt it, but we don't want to block
            # shutdown either. Detach.
            task.add_done_callback(lambda _t: None)
