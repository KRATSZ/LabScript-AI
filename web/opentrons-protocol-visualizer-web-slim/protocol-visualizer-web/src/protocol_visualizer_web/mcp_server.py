"""Optional MCP (Model Context Protocol) stdio server for agent tools.

Install: ``uv sync --extra mcp`` (from this directory), then run:
``uv run protocol-visualizer-mcp``

Tools call the same analyzer as the HTTP API (local Opentrons ``api`` venv recommended).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise SystemExit(
            "MCP extra not installed. Run: uv sync --extra mcp"
        ) from e

    from protocol_visualizer_web.analyze import run_analyze

    mcp = FastMCP("opentrons-protocol-visualizer")

    @mcp.tool()
    def analyze_opentrons_protocol(
        protocol_source: str,
        filename: str = "protocol.py",
    ) -> str:
        """
        Analyze Opentrons protocol source code. Returns analyzer JSON as a string
        (same schema as ``opentrons.cli analyze --json-output``).

        Use a ``.py`` or ``.json`` filename matching the protocol type.
        For RTP protocols, use the HTTP API with ``rtp_values``, ``rtp_files_map``,
        and ``rtp_csv`` file uploads instead.
        """
        suffix = Path(filename).suffix.lower()
        if suffix not in (".py", ".json"):
            return json.dumps(
                {"error": "filename must end with .py or .json"},
            )

        tmp = Path(tempfile.mkdtemp(prefix="pv-mcp-"))
        try:
            path = tmp / Path(filename).name
            path.write_text(protocol_source, encoding="utf-8")
            result = run_analyze(path, [], check=False)
            return json.dumps(result)
        except Exception as exc:
            return json.dumps({"error": str(exc)})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    mcp.run()


if __name__ == "__main__":
    main()
