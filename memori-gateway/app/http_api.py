from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from .config import settings
from .core import ChatRequestCore, chat_with_memory

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None)
    input: str
    model: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.0)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    debug: bool = Field(default=False)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str
    namespace: str
    usage: Dict[str, Any]
    debug: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="Memori Gateway", version="0.1.0", docs_url=None, redoc_url=None)


def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    """Simple header-based API key validation."""

    if not settings.gateway_api_key:
        logger.error("Gateway API key is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gateway API key not configured.",
        )

    if x_api_key != settings.gateway_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    _: None = Depends(verify_api_key),
) -> ChatResponse:
    """Primary chat endpoint delegating to the shared core."""

    try:
        core_request = ChatRequestCore(
            session_id=request.session_id,
            input=request.input,
            model=request.model,
            temperature=request.temperature,
            metadata=request.metadata,
            debug=request.debug,
        )
        response = chat_with_memory(core_request)
        return ChatResponse(**asdict(response))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - FastAPI handles logging
        logger.exception("chat_endpoint failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request.",
        ) from exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Simple readiness probe."""

    return HealthResponse(status="ok")
