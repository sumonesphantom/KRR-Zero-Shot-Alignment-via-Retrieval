"""GET /api/styles — list and detail. Cached in memory."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.styles import StyleCardOut, StylesListResponse
from api.services import styles_service


router = APIRouter(prefix="/api/styles")


@router.get("", response_model=StylesListResponse)
def list_styles():
    cards = styles_service.load_cards()
    return StylesListResponse(styles=[StyleCardOut.model_validate(c) for c in cards])


@router.get("/{style_id}", response_model=StyleCardOut)
def get_style(style_id: str):
    card = styles_service.get_card(style_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Unknown style id: {style_id}")
    return StyleCardOut.model_validate(card)
