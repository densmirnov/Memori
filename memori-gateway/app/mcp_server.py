from __future__ import annotations

import json
import sys
from typing import Any, Dict

from .core import ChatRequestCore, chat_with_memory

JSONRPC_VERSION = "2.0"

CHAT_TOOL = {
    "name": "chat_with_memory",
    "description": "Send a message through Memori Gateway and get an LLM response with memory context.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session identifier to continue prior context.",
            },
            "input": {
                "type": "string",
                "description": "User message to send.",
            },
            "model": {
                "type": "string",
                "description": "Override the default model.",
            },
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 2.0,
                "default": 0.0,
            },
            "debug": {
                "type": "boolean",
                "default": False,
            },
        },
        "required": ["input"],
    },
    "outputSchema": {
        "type": "object",
        "properties": {
            "reply": {"type": "string"},
            "session_id": {"type": "string"},
            "model": {"type": "string"},
        },
        "required": ["reply", "session_id", "model"],
    },
}


class MCPServer:
    """Minimal MCP JSON-RPC server over stdio."""

    def serve(self) -> None:
        """Main loop handling stdio JSON-RPC messages."""

        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                self._write_error(None, code=-32700, message="Parse error")
                continue

            response = self._dispatch(request)
            if response is not None:
                self._write(response)

    def _dispatch(self, request: Dict[str, Any]) -> Dict[str, Any] | None:
        method = request.get("method")
        request_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-10-07",
                    "capabilities": {"tools": {}},
                },
            }

        if method == "ping":
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": {},
            }

        if method == "tools/list":
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": {"tools": [CHAT_TOOL]},
            }

        if method == "tools/call":
            return self._handle_tool_call(request)

        return self._error_response(request_id, code=-32601, message="Method not found")

    def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        request_id = request.get("id")
        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}

        if name != CHAT_TOOL["name"]:
            return self._error_response(request_id, code=-32602, message="Unknown tool")

        if "input" not in arguments:
            return self._error_response(
                request_id, code=-32602, message="'input' is required"
            )

        core_request = ChatRequestCore(
            session_id=arguments.get("session_id"),
            input=arguments["input"],
            model=arguments.get("model"),
            temperature=float(arguments.get("temperature") or 0.0),
            metadata=None,
            debug=bool(arguments.get("debug", False)),
        )

        try:
            response = chat_with_memory(core_request)
            payload = {
                "reply": response.reply,
                "session_id": response.session_id,
                "model": response.model,
            }
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": payload,
            }
        except Exception as exc:  # pragma: no cover - errors surfaced to tool caller
            return self._error_response(
                request_id, code=-32603, message=f"chat_with_memory failed: {exc}"
            )

    def _error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": {"code": code, "message": message}}

    def _write(self, payload: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()


def serve() -> None:
    """Entry point used by __main__."""

    server = MCPServer()
    server.serve()
