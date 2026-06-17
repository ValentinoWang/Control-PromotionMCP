from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from control_promotion import __version__
from control_promotion.core.guard_spec import review_guard_quality, validate_guard_spec_data
from control_promotion.core.ladder import ladder_as_dict
from control_promotion.core.routing import route_control_destination
from control_promotion.io import load_data
from control_promotion.inspect import check_ssot_links, inspect_project
from control_promotion.prompts import PROMPTS, render_prompt
from control_promotion.reporting import render_smell_gate_report
from control_promotion.resources import list_resource_descriptors, read_resource
from control_promotion.review import evaluate_control_candidate
from control_promotion.validation import validate_project_adapter, validate_smell_catalog

PROTOCOL_VERSION = "2025-06-18"


class ControlPromotionMCP:
    def __init__(self, project_root: str | Path = ".", adapter: str | None = None) -> None:
        self.project_root = str(Path(project_root).resolve())
        self.adapter = adapter
        self.tools: dict[str, tuple[str, dict[str, Any], Callable[[dict[str, Any]], Any]]] = {
            "inspect_project": (
                "Inspect repository structure and detected governance controls.",
                _schema({"project_root": {"type": "string"}}, []),
                self._inspect_project,
            ),
            "evaluate_control_candidate": (
                "Evaluate a proposed rule, guard, skill, or remediation and decide its control maturity.",
                _schema(
                    {
                        "candidate_text": {"type": "string"},
                        "evidence": {"type": "object"},
                        "context": {"type": "object"},
                    },
                    ["candidate_text"],
                ),
                self._evaluate_control_candidate,
            ),
            "route_control_destination": (
                "Route a failure class to docs, Skill, quality guard, QA harness, or contract prevention.",
                _schema(
                    {
                        "failure_class": {"type": "string"},
                        "detectability": {"type": "string"},
                        "recurrence": {"type": "string"},
                        "harm": {"type": "string"},
                        "scope": {"type": "string"},
                    },
                    [],
                ),
                self._route_control_destination,
            ),
            "validate_smell_catalog": (
                "Validate a smell catalog file for required control-promotion fields.",
                _schema({"path": {"type": "string"}}, ["path"]),
                self._validate_smell_catalog,
            ),
            "validate_project_adapter": (
                "Validate a project adapter file.",
                _schema({"path": {"type": "string"}}, ["path"]),
                self._validate_project_adapter,
            ),
            "validate_guard_spec": (
                "Validate a GuardSpec file before a quality guard can be promoted.",
                _schema({"path": {"type": "string"}, "guard_spec": {"type": "object"}}, []),
                self._validate_guard_spec,
            ),
            "review_guard_quality": (
                "Review GuardSpec quality and promotion gate readiness.",
                _schema({"path": {"type": "string"}, "guard_spec": {"type": "object"}}, []),
                self._review_guard_quality,
            ),
            "render_smell_gate_report": (
                "Render a Markdown smell gate report from a candidate or review object.",
                _schema(
                    {
                        "candidate_text": {"type": "string"},
                        "review": {"type": "object"},
                        "evidence": {"type": "object"},
                        "context": {"type": "object"},
                    },
                    [],
                ),
                self._render_smell_gate_report,
            ),
            "check_ssot_links": (
                "Classify symlinked SSOT paths and recommend safe edit routing.",
                _schema({"paths": {"type": "array", "items": {"type": "string"}}}, ["paths"]),
                self._check_ssot_links,
            ),
        }

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        if message.get("jsonrpc") != "2.0":
            return self._error(message.get("id"), -32600, "invalid JSON-RPC version")
        method = message.get("method")
        if method is None:
            return self._error(message.get("id"), -32600, "missing method")
        if "id" not in message:
            self._handle_notification(method)
            return None
        try:
            result = self._dispatch(method, message.get("params") or {})
            return {"jsonrpc": "2.0", "id": message["id"], "result": result}
        except KeyError as exc:
            return self._error(message["id"], -32601, str(exc))
        except ValueError as exc:
            return self._error(message["id"], -32602, str(exc))
        except Exception as exc:  # pragma: no cover - defensive RPC boundary
            return self._error(message["id"], -32000, f"server error: {exc}")

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "control-promotion-mcp",
                    "title": "Control Promotion MCP",
                    "version": __version__,
                },
                "instructions": "Read-only governance control-promotion server. Write tools are intentionally absent.",
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": name,
                        "title": name.replace("_", " ").title(),
                        "description": description,
                        "inputSchema": schema,
                        "annotations": {"readOnlyHint": True, "destructiveHint": False},
                    }
                    for name, (description, schema, _) in self.tools.items()
                ]
            }
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name not in self.tools:
                raise KeyError(f"unknown tool: {name}")
            result = self.tools[name][2](arguments)
            return _tool_result(result)
        if method == "resources/list":
            return {"resources": list_resource_descriptors(self.project_root)}
        if method == "resources/read":
            uri = str(params.get("uri", ""))
            text, mime = read_resource(uri, self.project_root)
            return {"contents": [{"uri": uri, "mimeType": mime, "text": text}]}
        if method == "prompts/list":
            return {
                "prompts": [
                    {
                        "name": name,
                        "description": prompt["description"],
                        "arguments": prompt["arguments"],
                    }
                    for name, prompt in PROMPTS.items()
                ]
            }
        if method == "prompts/get":
            name = str(params.get("name", ""))
            if name not in PROMPTS:
                raise KeyError(f"unknown prompt: {name}")
            arguments = params.get("arguments") or {}
            return {
                "description": PROMPTS[name]["description"],
                "messages": [
                    {
                        "role": "user",
                        "content": {"type": "text", "text": render_prompt(name, arguments)},
                    }
                ],
            }
        raise KeyError(f"unknown method: {method}")

    def _handle_notification(self, method: str) -> None:
        if method != "notifications/initialized":
            print(f"ignored notification: {method}", file=sys.stderr)

    def _error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def _inspect_project(self, args: dict[str, Any]) -> dict[str, Any]:
        return inspect_project(args.get("project_root") or self.project_root)

    def _evaluate_control_candidate(self, args: dict[str, Any]) -> dict[str, Any]:
        return evaluate_control_candidate(
            str(args.get("candidate_text", "")),
            evidence=args.get("evidence") or {},
            context=args.get("context") or {},
        )

    def _route_control_destination(self, args: dict[str, Any]) -> dict[str, Any]:
        return route_control_destination(
            failure_class=str(args.get("failure_class", "")),
            detectability=str(args.get("detectability", "")),
            recurrence=str(args.get("recurrence", "")),
            harm=str(args.get("harm", "")),
            scope=str(args.get("scope", "")),
        ).to_dict()

    def _validate_smell_catalog(self, args: dict[str, Any]) -> dict[str, Any]:
        return validate_smell_catalog(_resolve_path(args["path"], self.project_root))

    def _validate_project_adapter(self, args: dict[str, Any]) -> dict[str, Any]:
        return validate_project_adapter(_resolve_path(args["path"], self.project_root))

    def _validate_guard_spec(self, args: dict[str, Any]) -> dict[str, Any]:
        return validate_guard_spec_data(self._guard_spec_from_args(args))

    def _review_guard_quality(self, args: dict[str, Any]) -> dict[str, Any]:
        return review_guard_quality(self._guard_spec_from_args(args))

    def _render_smell_gate_report(self, args: dict[str, Any]) -> dict[str, str]:
        review = args.get("review")
        if not isinstance(review, dict):
            review = evaluate_control_candidate(
                str(args.get("candidate_text", "")),
                evidence=args.get("evidence") or {},
                context=args.get("context") or {},
            )
        return {"markdown": render_smell_gate_report(review)}

    def _check_ssot_links(self, args: dict[str, Any]) -> dict[str, Any]:
        paths = args.get("paths")
        if not isinstance(paths, list):
            raise ValueError("paths must be a list")
        return check_ssot_links([str(path) for path in paths], self.project_root, self.adapter)

    def _guard_spec_from_args(self, args: dict[str, Any]) -> dict[str, Any]:
        guard_spec = args.get("guard_spec")
        if isinstance(guard_spec, dict):
            return guard_spec
        path = args.get("path")
        if isinstance(path, str):
            loaded = load_data(_resolve_path(path, self.project_root))
            if isinstance(loaded, dict):
                return loaded
        raise ValueError("provide either path or guard_spec")


def run_stdio(server: ControlPromotionMCP) -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = server.handle(message)
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def run_http(server: ControlPromotionMCP, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/mcp":
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            if origin and not origin.startswith(("http://127.0.0.1", "http://localhost")):
                self.send_error(403, "forbidden origin")
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                body = self.rfile.read(length).decode("utf-8")
                response = server.handle(json.loads(body))
            except json.JSONDecodeError as exc:
                response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
            if response is None:
                self.send_response(202)
                self.end_headers()
                return
            payload = json.dumps(response, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            self.send_error(405, "SSE stream is not supported by this V1 server")

        def log_message(self, format: str, *args: Any) -> None:
            print(format % args, file=sys.stderr)

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"control-promotion-mcp listening on http://{host}:{port}/mcp", file=sys.stderr)
    httpd.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="control-promotion-mcp")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--adapter")
    parser.add_argument("--mode", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    server = ControlPromotionMCP(args.project_root, args.adapter)
    if args.mode == "http":
        run_http(server, args.host, args.port)
    else:
        run_stdio(server)
    return 0


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": True}


def _resolve_path(path: str, project_root: str) -> str:
    raw = Path(path)
    return str(raw if raw.is_absolute() else Path(project_root) / raw)


def _tool_result(result: Any) -> dict[str, Any]:
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": result if isinstance(result, dict) else {"result": result},
        "isError": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
