from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .artifacts import default_output_directory, write_artifacts
from .pipeline import run_demo
from .reporting import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m heos.demo",
        description="Run the deterministic HomeEnergyOS Glass Box Demonstrator.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output_directory(),
        help="Artifact output directory (default: ~/.heos/demo/latest).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final result as JSON instead of the human report.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Write artifacts without printing the report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run = run_demo()
    paths = write_artifacts(run, args.output)
    if not args.quiet:
        if args.json:
            print(json.dumps(run.result.to_dict(), indent=2, sort_keys=True))
        else:
            print(render_report(run.result), end="")
            print(f"Artifacts: {paths[0].parent}")
    return 0 if run.result.success else 1
