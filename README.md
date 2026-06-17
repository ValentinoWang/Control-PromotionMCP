# control-promotion-mcp

Portable governance control-promotion CLI and MCP server.

This repository turns recurring engineering experience into a structured control lifecycle:

```text
raw evidence
  -> reusable observation
  -> docs / Skill / scoped AGENTS
  -> static guard / QA harness
  -> type, schema, or contract prevention
  -> retired guard
```

The package has three layers:

```text
control_promotion        # deterministic core and CLI
control_promotion_mcp    # read-only MCP server
.control-promotion.yaml  # project adapter
```

## Why MCP

MCP lets a server expose callable tools, readable resources, and reusable prompts over JSON-RPC. The 2025-06-18 specification defines stdio and Streamable HTTP transports; stdio messages are newline-delimited JSON-RPC, and Streamable HTTP uses POST requests to a single MCP endpoint. This server follows that model for a read-only governance control plane.

References:

- https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle
- https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- https://modelcontextprotocol.io/specification/2025-06-18/server/resources
- https://modelcontextprotocol.io/specification/2025-06-18/server/prompts

## Install

```bash
pip install control-promotion-mcp
```

For local development:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## CLI

```bash
control-promotion inspect --project-root .
control-promotion validate-adapter .control-promotion.yaml
control-promotion validate-catalog references/smell-catalog.yaml
control-promotion route \
  --failure-class frontend_semantic_metric_without_source \
  --detectability static \
  --recurrence repeated \
  --harm high
control-promotion review --candidate candidate.yaml --format markdown
```

Candidate file:

```yaml
candidate_text: |
  frontend-metric-source-guard prevents hard-coded semantic KPI literals.
evidence:
  paths:
    - scripts/quality/check_frontend_metric_source_guard.py
  commands:
    - bash scripts/quality/run_frontend_metric_source_guard.sh --mode ci
context:
  recurrence: repeated
  harm: high
```

## MCP stdio

```json
{
  "mcpServers": {
    "control-promotion": {
      "command": "control-promotion-mcp",
      "args": [
        "--project-root",
        ".",
        "--adapter",
        ".control-promotion.yaml",
        "--mode",
        "stdio"
      ]
    }
  }
}
```

## MCP HTTP

```bash
control-promotion-mcp \
  --project-root . \
  --adapter .control-promotion.yaml \
  --mode http \
  --host 127.0.0.1 \
  --port 8765
```

The V1 HTTP server exposes `POST /mcp` and returns one JSON response. It binds to localhost by default and rejects non-local `Origin` headers. It intentionally does not expose write tools.

## Exposed MCP Tools

- `inspect_project`
- `evaluate_control_candidate`
- `route_control_destination`
- `validate_smell_catalog`
- `validate_project_adapter`
- `render_smell_gate_report`
- `check_ssot_links`

`evaluate_control_candidate` also returns an `abstraction_review` block. This block flags guard-quality issues that routing alone cannot catch, including incident-string denylist overfit, fixed current-file allowlists, missing positive/negative fixtures, missing canonical contracts, missing scoped surface discovery, and missing exception policies.

Example high-risk result:

```yaml
decision: refactor_before_promote
control_level: L5_static_quality_guard
abstraction_review:
  specificity_risk: high
  overfit_signals:
    - literal_incident_phrase_denylist
    - fixed_current_file_allowlist
    - missing_targeted_fixtures
    - missing_canonical_contract
  missing_abstraction:
    - canonical_contract
    - deprecated_alias_set
    - scoped_surface_discovery
    - exception_policy
  recommendation: refactor_before_promote
```

## Exposed MCP Resources

- `control://ladder`
- `control://routing-matrix`
- `control://smell-rubric`
- `control://proof-obligations`
- `control://retirement-policy`
- `catalog://base`
- `catalog://project`
- `adapter://project`
- `template://smell-gate-report`

## Exposed MCP Prompts

- `review-control-candidate`
- `promote-experience`
- `retire-guard`

## Project Adapter

Every consuming repository should keep project-specific paths and policies in `.control-promotion.yaml` instead of forking this server. The adapter expresses:

- project type
- AGENTS, Skill, docs, quality, QA, and generated paths
- SSOT links
- baseline quality commands
- routing overrides
- generated artifact and write-tool policies

## Safety Model

V1 is read-only. It can inspect files, validate catalogs/adapters, classify candidates, and render reports. It does not write repository files, run arbitrary project commands, or mutate governance rules through MCP.

Future write tools should remain disabled by default, require explicit path scopes, forbid generated and secret paths, and return diffs plus verification commands before applying changes.

## Development

```bash
python -m unittest discover -s tests
PYTHONPATH=src python -m control_promotion.cli validate-adapter .control-promotion.yaml
PYTHONPATH=src python -m control_promotion.cli validate-catalog references/smell-catalog.yaml
```
