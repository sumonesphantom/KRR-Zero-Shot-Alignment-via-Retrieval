"""GET /api/traces — list and detail; verbatim eval-report passthroughs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.schemas.traces import (
    EvaluationsAvailable,
    PipelineTraceOut,
    TraceListResponse,
    TraceSummary,
)
from api.services import traces_service


router = APIRouter(prefix="/api/traces")


def _transform_trace(data: dict) -> dict:
    """Backend dataclass snake_case → Pydantic camelCase expects aliases, and
    the Pydantic model sets `populate_by_name=True`, so snake_case keys flow
    through. The nested revisions[].verdict dict also already matches.
    """
    # Flatten retrieval entries that may not have `card` populated on older traces.
    retrieval = []
    for r in data.get("retrieval", []):
        retrieval.append({
            "rank": r.get("rank", 0),
            "style_id": r.get("style_id", ""),
            "score": r.get("score", 0.0),
            "weight": r.get("weight", 0.0),
            "card": r.get("card"),
        })
    return {
        "query": data.get("query", ""),
        "preference": data.get("preference", ""),
        "retrieval": retrieval,
        "draft": data.get("draft", ""),
        "revisions": data.get("revisions", []),
        "final_style_id": data.get("final_style_id", ""),
        "final_output": data.get("final_output", ""),
        "final_verdict": data.get("final_verdict"),
    }


@router.get("", response_model=TraceListResponse)
def list_traces():
    items = [TraceSummary.model_validate(t) for t in traces_service.list_traces()]
    avail = traces_service.evaluations_available()
    return TraceListResponse(
        traces=items,
        evaluations_available=EvaluationsAvailable(**avail),
    )


@router.get("/evaluation/{kind}")
def get_evaluation(kind: str):
    if kind != "judge":
        raise HTTPException(status_code=400, detail="kind must be 'judge'")
    data = traces_service.get_evaluation(kind)
    if data is None:
        raise HTTPException(status_code=404, detail=f"evaluation_results_{kind}.json not found")
    return JSONResponse(data)


@router.get("/{trace_id}", response_model=PipelineTraceOut)
def get_trace(trace_id: str):
    data = traces_service.get_trace(trace_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
    return PipelineTraceOut.model_validate(_transform_trace(data))
