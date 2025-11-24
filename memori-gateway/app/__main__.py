from __future__ import annotations

import argparse
import os

import uvicorn


def run_http() -> None:
    """Start the FastAPI server via uvicorn."""

    from .http_api import app

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


def run_mcp() -> None:
    """Launch the MCP stdio server."""

    from .mcp_server import serve

    serve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Memori Gateway launcher")
    parser.add_argument(
        "mode",
        choices=("http", "mcp"),
        nargs="?",
        default="http",
        help="Which gateway mode to run (default: http)",
    )
    args = parser.parse_args()

    if args.mode == "mcp":
        run_mcp()
    else:
        run_http()


if __name__ == "__main__":
    main()
