"""CLI entrypoint for AI Consensus CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from aicx.config import load_config
from aicx.consensus.runner import run_consensus
from aicx.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aicx", description="AI Consensus CLI")
    parser.add_argument("prompt", help="User prompt to submit to the consensus loop")
    parser.add_argument("--models", help="Comma-separated model names", default=None)
    parser.add_argument("--mediator", help="Mediator model name", default=None)
    parser.add_argument("--rounds", type=int, default=None, help="Max number of rounds")
    parser.add_argument("--approval-ratio", type=float, default=None)
    parser.add_argument("--change-threshold", type=float, default=None)
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--config", default=None, help="Path to config file")
    parser.add_argument("--share-mode", default=None, choices=["digest", "raw"])
    parser.add_argument("--no-consensus-summary", action="store_true", default=False)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(
        args.config,
        models=args.models,
        mediator=args.mediator,
        rounds=args.rounds,
        approval_ratio=args.approval_ratio,
        change_threshold=args.change_threshold,
        share_mode=args.share_mode,
        verbose=args.verbose,
    )

    configure_logging(config.verbose)

    result = run_consensus(
        prompt=args.prompt,
        config=config,
        no_consensus_summary=args.no_consensus_summary,
    )

    sys.stdout.write(result.output)
    if not result.output.endswith("\n"):
        sys.stdout.write("\n")

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
