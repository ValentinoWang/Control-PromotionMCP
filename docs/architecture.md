# Architecture

`control-promotion-mcp` is split into deterministic core logic, a CLI, and a read-only MCP protocol layer.

## Core

The core package owns:

- control maturity ladder
- routing matrix
- failure-class fingerprinting
- proof obligations
- retirement policy
- adapter and catalog validation

Both CLI and MCP call the same core functions.

## CLI

The CLI is the CI-friendly entry point. It returns stable process exit codes for validators:

- `0` for valid adapter/catalog files
- `1` for validation failure
- `2` for command-line usage errors

## MCP

The MCP server exposes tools, resources, and prompts over JSON-RPC. It implements stdio directly and supports a minimal Streamable HTTP POST endpoint at `/mcp`.

The server is intentionally read-only in V1. Scaffold and write tools should be added only after path-scoped policy enforcement exists.
