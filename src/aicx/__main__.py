"""CLI entrypoint for AI Consensus CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from aicx.config import load_config
from aicx.consensus.runner import run_consensus
from aicx.logging import configure_logging
from aicx.types import ConfigError, ExitCode


VERSION = "0.1.0"

EXAMPLES = """
Examples:
  aicx "Explain Rust ownership"
      Basic usage with default models (gpt-4o, claude-3-5, gemini-2)

  aicx "Summarize this code" --models gpt-4o,claude-3-5 --rounds 2
      Use specific models with fewer rounds

  aicx "Review this design" --verbose
      Enable detailed audit logging to stderr

  aicx "Complex analysis" --max-context-tokens 8000
      Limit context size (triggers truncation of older rounds)

  aicx "Quick check" --approval-ratio 0.5
      Lower consensus threshold (majority instead of 2/3)

Exit Codes:
  0  Success (consensus reached or best-effort answer)
  1  Configuration error (invalid config file or flags)
  2  Provider error (API failures, zero successful responses)
  3  Quorum failure (some responses, but below threshold)
  4  Internal error (unexpected exception)
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="aicx",
        description="AI Consensus CLI - Send prompts to multiple AI models and reach consensus.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "prompt",
        help="The question or task to submit to the consensus loop",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    # Model selection
    model_group = parser.add_argument_group("Model Selection")
    model_group.add_argument(
        "--models",
        metavar="LIST",
        help="Comma-separated model names to use as participants (e.g., gpt-4o,claude-3-5)",
        default=None,
    )
    model_group.add_argument(
        "--mediator",
        metavar="NAME",
        help="Model name to use as mediator for synthesis (must differ from participants)",
        default=None,
    )

    # Consensus parameters
    consensus_group = parser.add_argument_group("Consensus Parameters")
    consensus_group.add_argument(
        "--rounds",
        type=int,
        metavar="N",
        default=None,
        help="Maximum consensus rounds before stopping (default: 3)",
    )
    consensus_group.add_argument(
        "--approval-ratio",
        type=float,
        metavar="RATIO",
        default=None,
        help="Fraction of approvals needed for consensus, 0.0-1.0 (default: 0.67)",
    )
    consensus_group.add_argument(
        "--change-threshold",
        type=float,
        metavar="RATIO",
        default=None,
        help="Minimum change ratio to continue iterating (default: 0.10)",
    )

    # Context management
    context_group = parser.add_argument_group("Context Management")
    context_group.add_argument(
        "--max-context-tokens",
        type=int,
        metavar="N",
        default=None,
        help="Token budget for context; older rounds are truncated when exceeded",
    )

    # Behavior flags
    behavior_group = parser.add_argument_group("Behavior")
    behavior_group.add_argument(
        "--share-mode",
        default=None,
        choices=["digest", "raw"],
        help="How responses are shared: 'digest' (summarized) or 'raw' (full text)",
    )
    behavior_group.add_argument(
        "--strict-json",
        action="store_true",
        default=None,
        help="Fail immediately on JSON parse errors (no recovery attempts)",
    )
    behavior_group.add_argument(
        "--verbose",
        action="store_true",
        default=None,
        help="Write detailed JSONL audit log to stderr",
    )
    behavior_group.add_argument(
        "--no-consensus-summary",
        action="store_true",
        default=False,
        help="Suppress disagreement summary when consensus is not reached",
    )

    # Config file
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="Path to TOML config file (default: config/config.toml)",
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
