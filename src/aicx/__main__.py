"""CLI entrypoint for AI Consensus CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from aicx.config import load_config
from aicx.consensus.runner import run_consensus
from aicx.logging import configure_logging
from aicx.types import ConfigError, ExitCode


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="aicx",
        description="AI Consensus CLI - Send prompts to multiple AI models and reach consensus",
    )
    parser.add_argument("prompt", help="User prompt to submit to the consensus loop")

    # Model selection
    parser.add_argument(
        "--models",
        help="Comma-separated list of model names to use as participants",
        default=None,
    )
    parser.add_argument(
        "--mediator", help="Model name to use as mediator", default=None
    )

    # Consensus parameters
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Maximum number of consensus rounds (default: 3)",
    )
    parser.add_argument(
        "--approval-ratio",
        type=float,
        default=None,
        help="Fraction of participants required for consensus (default: 0.67)",
    )
    parser.add_argument(
        "--change-threshold",
        type=float,
        default=None,
        help="Minimum change threshold for early stopping (default: 0.10)",
    )

    # Context management
    parser.add_argument(
        "--max-context-tokens",
        type=int,
        default=None,
        help="Soft cap for total context tokens; triggers summarization",
    )

    # Behavior flags
    parser.add_argument(
        "--share-mode",
        default=None,
        choices=["digest", "raw"],
        help="How to share information between participants (default: digest)",
    )
    parser.add_argument(
        "--strict-json",
        action="store_true",
        default=None,
        help="Disable JSON recovery and fail on first parse error",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=None,
        help="Enable verbose audit trail output to stderr",
    )
    parser.add_argument(
        "--no-consensus-summary",
        action="store_true",
        default=False,
        help="Omit disagreement summary from output",
    )

    # Config file
    parser.add_argument(
        "--config", default=None, help="Path to TOML config file (default: config/config.toml)"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main entrypoint for the CLI.

    Args:
        argv: Command-line arguments, or None to use sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        # Load and validate configuration
        config = load_config(
            args.config,
            models=args.models,
            mediator=args.mediator,
            rounds=args.rounds,
            approval_ratio=args.approval_ratio,
            change_threshold=args.change_threshold,
            max_context_tokens=args.max_context_tokens,
            share_mode=args.share_mode,
            strict_json=args.strict_json,
            verbose=args.verbose,
        )
    except ConfigError as e:
        sys.stderr.write(f"Configuration error: {e}\n")
        return ExitCode.CONFIG_ERROR

    # Configure logging based on verbose flag
    configure_logging(config.verbose)

    # Run consensus loop
    result = run_consensus(
        prompt=args.prompt,
        config=config,
        no_consensus_summary=args.no_consensus_summary,
    )

    # Write output to stdout
    sys.stdout.write(result.output)
    if not result.output.endswith("\n"):
        sys.stdout.write("\n")

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
