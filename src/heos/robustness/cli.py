from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from heos.demo.scenarios import sunny_surplus_scenario

from .artifacts import default_output_directory, write_artifacts
from .engine import RobustnessEngine
from .models import RobustnessPolicy
from .reporting import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m heos.robustness",
        description="Stress-test a HEOS strategy across bounded deterministic uncertainty.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output_directory(),
        help="Artifact output directory (default: ~/.heos/robustness/latest).",
    )
    parser.add_argument("--quick", action="store_true", help="Run a compact nine-variant grid.")
    parser.add_argument("--json", action="store_true", help="Print the certificate as JSON.")
    parser.add_argument("--quiet", action="store_true", help="Write artifacts without output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    scenario = sunny_surplus_scenario()
    policy = RobustnessPolicy.quick() if args.quick else RobustnessPolicy()
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=policy,
    )
    run = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    paths = write_artifacts(run, args.output)
    if not args.quiet:
        if args.json:
            print(json.dumps(run.certificate.to_dict(), indent=2, sort_keys=True))
        else:
            print(render_report(run), end="")
            print(f"Artifacts: {paths[0].parent}")
    return 0 if run.certificate.robust else 2
