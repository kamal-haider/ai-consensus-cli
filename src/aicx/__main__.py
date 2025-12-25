"""CLI entrypoint for AI Consensus CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from aicx.config import load_config
from aicx.consensus.runner import run_consensus
from aicx.logging import configure_logging
from aicx.types import ConfigError, ExitCode


VERSION = "1.2.0"

EXAMPLES = """
Examples:
  aicx "Explain Rust ownership"
      Basic usage with default models

  aicx "Summarize this code" --models gpt,claude --rounds 2
      Use shorthand model names with fewer rounds

  aicx "Review this design" --models gpt-4o,claude-sonnet-4-20250514
      Use specific model IDs directly

  aicx "Review this design" --verbose
      Enable detailed audit logging to stderr

  aicx "Design an abstract class for API" --save-to ./docs/
      Save output to a file with auto-generated name

  aicx --setup
      Run interactive setup wizard to configure defaults

  aicx --status
      Show current configuration and API key status

  aicx --ask "How do I configure a new model?"
      Get quick help about the CLI

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
        nargs="?",
        default=None,
        help="The question or task to submit to the consensus loop",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    # Setup and status commands
    setup_group = parser.add_argument_group("Setup")
    setup_group.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive setup wizard to configure default models and mediator",
    )
    setup_group.add_argument(
        "--status",
        action="store_true",
        help="Show current configuration and API key status",
    )
    setup_group.add_argument(
        "--ask",
        metavar="QUESTION",
        help="Ask a question about how to use the CLI",
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

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--save-to",
        metavar="DIR",
        default=None,
        help="Save output to a file in DIR with auto-generated filename from prompt",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main entrypoint for the CLI.

    Args:
        argv: Command-line arguments, or None to use sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    # Load saved API keys from ~/.config/aicx/.env before anything else
    from aicx.user_config import load_saved_api_keys

    load_saved_api_keys()

    parser = build_parser()
    args = parser.parse_args(argv)

    # Handle setup command
    if args.setup:
        from aicx.setup import run_setup

        return run_setup()

    # Handle status command
    if args.status:
        from aicx.setup import run_status

        return run_status()

    # Handle ask command
    if args.ask:
        from aicx.assistant import run_help_assistant

        return run_help_assistant(args.ask)

    # Require prompt for normal operation
    if not args.prompt:
        parser.print_help()
        sys.stderr.write("\nError: prompt is required (or use --setup/--status)\n")
        return ExitCode.CONFIG_ERROR

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

    # Save to file if --save-to specified
    if args.save_to:
        from aicx.output import save_output

        file_path = save_output(result.output, args.save_to, args.prompt)
        sys.stdout.write(f"Saved to: {file_path}\n")
    else:
        # Write output to stdout
        sys.stdout.write(result.output)
        if not result.output.endswith("\n"):
            sys.stdout.write("\n")

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
