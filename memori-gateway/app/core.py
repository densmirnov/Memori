from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from memori import Memori
from memori.integrations.openai_integration import (
    clear_active_memori_context,
    create_openai_client,
    set_active_memori_context,
)

from .config import settings

SYSTEM_PROMPT = (
    "You are Memori Gateway, a memory-aware assistant that stores context and "
    "reuses it across conversations."
)


@dataclass
class ChatRequestCore:
    """Shared input schema for gateway requests."""

    session_id: Optional[str]
    input: str
    model: Optional[str] = None
    temperature: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    debug: bool = False


@dataclass
class ChatResponseCore:
    """Shared response schema for FastAPI and MCP layers."""

    reply: str
    model: str
    session_id: str
    namespace: str
    usage: Dict[str, Any]
    debug: Optional[Dict[str, Any]] = None


def chat_with_memory(request: ChatRequestCore) -> ChatResponseCore:
    """Run a Memori-enabled OpenAI call and return a standard response."""

    resolved_session_id = request.session_id or str(uuid.uuid4())
    namespace = f"default:{resolved_session_id}"
    model = request.model or settings.memori_default_model

    memory_instance = Memori(
        database_connect=settings.memori_db_dsn,
        user_id=namespace,
        session_id=resolved_session_id,
        auto_ingest=settings.memori_auto_ingest,
        conscious_ingest=settings.memori_conscious_ingest,
        api_key=settings.openai_api_key,
        model=model,
    )
    memory_instance.enable()
    set_active_memori_context(memory_instance, request_id=str(uuid.uuid4()))

    try:
        client = create_openai_client(
            memory_instance,
            api_key=settings.openai_api_key,
        )

        completion_kwargs = {
            "model": model,
            "messages": _build_messages(request.input),
            "temperature": request.temperature,
        }
        if request.metadata:
            completion_kwargs["metadata"] = request.metadata

        response = client.chat.completions.create(**completion_kwargs)
        reply = _extract_reply(response)
        usage = _extract_usage(response)

        debug_payload = None
        if request.debug:
            debug_payload = {"retrieved_memories": _build_debug_memories(memory_instance)}

    finally:
        clear_active_memori_context()
        try:
            memory_instance.disable()
        except Exception:
            pass

    return ChatResponseCore(
        reply=reply,
        model=model,
        session_id=resolved_session_id,
        namespace=namespace,
        usage=usage,
        debug=debug_payload,
    )


def _build_messages(user_input: str) -> List[Dict[str, Any]]:
    """Return system + user messages for the LLM."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]


def _extract_reply(response) -> str:
    """Extract the assistant reply from the OpenAI response."""

    choices = getattr(response, "choices", [])
    if not choices:
        raise ValueError("OpenAI returned no choices")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message:
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()

    if hasattr(first_choice, "text") and first_choice.text:
        return first_choice.text.strip()

    return ""


def _extract_usage(response) -> Dict[str, Any]:
    """Normalize token usage values."""

    usage = {}
    usage_data = getattr(response, "usage", None)
    if usage_data:
        usage = {
            "prompt_tokens": getattr(usage_data, "prompt_tokens", 0),
            "completion_tokens": getattr(usage_data, "completion_tokens", 0),
            "total_tokens": getattr(usage_data, "total_tokens", 0),
        }
    return usage


def _build_debug_memories(memory_instance: Memori, limit: int = 3) -> List[Dict[str, Any]]:
    """Fetch the latest recorded memories for debugging."""

    history = memory_instance.db_manager.get_chat_history(
        user_id=memory_instance.user_id,
        session_id=memory_instance.session_id,
        limit=limit + 1,
    )
    entries = history[1:] if len(history) > 1 else []
    memories: List[Dict[str, Any]] = []
    for entry in entries[:limit]:
        memories.append(
            {
                "id": entry["chat_id"],
                "type": "long_term",
                "content": entry.get("ai_output") or entry.get("user_input", ""),
                "score": float(entry.get("tokens_used") or 0.0),
            }
        )
    return memories
