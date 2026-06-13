from __future__ import annotations

import argparse
import sys
from pathlib import Path

from control_promotion.inspect import check_ssot_links, inspect_project
from control_promotion.io import dump_data, load_data
from control_promotion.reporting import render_smell_gate_report
from control_promotion.review import evaluate_control_candidate
from control_promotion.core.routing import route_control_destination
from control_promotion.validation import validate_project_adapter, validate_smell_catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="control-promotion")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--project-root", default=".")
    inspect_parser.add_argument("--format", choices=("yaml", "json"), default="yaml")

    adapter_parser = sub.add_parser("validate-adapter")
    adapter_parser.add_argument("path")
    adapter_parser.add_argument("--format", choices=("yaml", "json"), default="yaml")

    catalog_parser = sub.add_parser("validate-catalog")
    catalog_parser.add_argument("path")
    catalog_parser.add_argument("--format", choices=("yaml", "json"), default="yaml")

    route_parser = sub.add_parser("route")
    route_parser.add_argument("--failure-class", default="")
    route_parser.add_argument("--detectability", default="")
    route_parser.add_argument("--recurrence", default="")
    route_parser.add_argument("--harm", default="")
    route_parser.add_argument("--scope", default="")
    route_parser.add_argument("--format", choices=("yaml", "json"), default="yaml")

    review_parser = sub.add_parser("review")
    review_parser.add_argument("--candidate", required=True, help="YAML/JSON file or raw candidate text")
    review_parser.add_argument("--format", choices=("yaml", "json", "markdown"), default="yaml")

    report_parser = sub.add_parser("render-report")
    report_parser.add_argument("--candidate", required=True, help="YAML/JSON file or raw candidate text")

    ssot_parser = sub.add_parser("check-ssot-links")
    ssot_parser.add_argument("paths", nargs="+")
    ssot_parser.add_argument("--project-root", default=".")
    ssot_parser.add_argument("--adapter")
    ssot_parser.add_argument("--format", choices=("yaml", "json"), default="yaml")

    args = parser.parse_args(argv)

    if args.command == "inspect":
        return _print(inspect_project(args.project_root), args.format)
    if args.command == "validate-adapter":
        result = validate_project_adapter(args.path)
        _print(result, args.format)
        return 0 if result["valid"] else 1
    if args.command == "validate-catalog":
        result = validate_smell_catalog(args.path)
        _print(result, args.format)
        return 0 if result["valid"] else 1
    if args.command == "route":
        result = route_control_destination(
            failure_class=args.failure_class,
            detectability=args.detectability,
            recurrence=args.recurrence,
            harm=args.harm,
            scope=args.scope,
        ).to_dict()
        return _print(result, args.format)
    if args.command == "review":
        result = _review_from_arg(args.candidate)
        if args.format == "markdown":
            print(render_smell_gate_report(result))
            return 0
        return _print(result, args.format)
    if args.command == "render-report":
        print(render_smell_gate_report(_review_from_arg(args.candidate)))
        return 0
    if args.command == "check-ssot-links":
        result = check_ssot_links(args.paths, args.project_root, args.adapter)
        return _print(result, args.format)

    parser.error(f"unsupported command {args.command}")
    return 2


def _review_from_arg(candidate: str) -> dict:
    path = Path(candidate)
    if path.exists():
        data = load_data(path)
        if not isinstance(data, dict):
            raise SystemExit("candidate file must contain an object")
        return evaluate_control_candidate(
            str(data.get("candidate_text", "")),
            evidence=data.get("evidence", {}),
            context=data.get("context", {}),
        )
    return evaluate_control_candidate(candidate)


def _print(data: dict, fmt: str) -> int:
    sys.stdout.write(dump_data(data, fmt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
