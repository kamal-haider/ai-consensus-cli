"""AI Query Tool - Simple CLI for querying AI models."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from aicx.providers import ProviderError, get_provider, list_models


VERSION = "2.0.0"

EXAMPLES = """
Examples:
  aicx query "Explain Rust ownership" --model gpt-4o
      Query GPT-4o with a prompt

  aicx query "Summarize this code" --model claude-sonnet
      Query Claude Sonnet

  aicx query "What is Python?" --model gemini -v
      Query Gemini with verbose output

  aicx query "Write a haiku" -s "You are a poet"
      Include a system prompt

  aicx models
      List available models

Exit Codes:
  0  Success
  1  Configuration error (invalid model, missing API key)
  2  Provider error (API failures, network errors)
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="aicx",
        description="AI Query Tool - Query AI models and get responses.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query a model",
        description="Send a prompt to an AI model and get a response.",
    )
    query_parser.add_argument(
        "prompt",
        help="The prompt to send to the model",
    )
    query_parser.add_argument(
        "-m", "--model",
        default="gpt-4o",
        help="Model to query (default: gpt-4o). Use 'aicx models' to list options.",
    )
    query_parser.add_argument(
        "-s", "--system",
        metavar="PROMPT",
        help="System prompt to set context/behavior",
    )
    query_parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature 0.0-2.0 (default: 0.7)",
    )
    query_parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum response tokens (default: 4096)",
    )
    query_parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Request timeout in seconds (default: 60)",
    )
    query_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print status messages to stderr",
    )

    # Models command
    subparsers.add_parser(
        "models",
        help="List available models",
        description="Show all supported model aliases.",
    )

    return parser


def run_query(args: argparse.Namespace) -> int:
    """Run a query against a model."""
    try:
        if args.verbose:
            print(f"Querying {args.model}...", file=sys.stderr)

        provider = get_provider(args.model)
        response = provider.query(
            args.prompt,
            system_prompt=args.system,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )

        print(response)
        return 0

    except ProviderError as e:
        print(f"Error: {e}", file=sys.stderr)
        if e.code == "auth":
            return 1  # Config error
        return 2  # Provider error


def run_models() -> int:
    """List available models."""
    print("Available models:\n")
    models = list_models()
    for model in models:
        print(f"  {model}")
    print(f"\nUse: aicx query \"your prompt\" --model <model>")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "models":
        return run_models()

    if args.command == "query":
        return run_query(args)

    # No command - show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
