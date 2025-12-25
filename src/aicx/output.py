"""Output file handling for saving consensus results."""

from __future__ import annotations

import re
from pathlib import Path


# Common words to exclude from filenames
STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "can", "this", "that",
    "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "whom", "how", "when", "where", "why",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again",
    "further", "then", "once", "here", "there", "any", "me", "my",
    "create", "make", "write", "generate", "build", "design", "develop",
    "implement", "add", "get", "set", "use", "using", "please", "help",
    "need", "want", "like", "give", "show", "explain", "describe",
    "document", "documentation", "doc", "docs", "file", "files",
})


def generate_filename(prompt: str, extension: str = ".md") -> str:
    """Generate a filename from a prompt.

    Extracts key words from the prompt, removes stop words,
    and creates a slugified filename.

    Args:
        prompt: The user's prompt text.
        extension: File extension to use (default: .md).

    Returns:
        A slugified filename like "abstract-class-racer-api.md".
    """
    # Convert to lowercase and extract words
    text = prompt.lower()

    # Remove punctuation and special characters, keep alphanumeric and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Split into words
    words = text.split()

    # Filter out stop words and short words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]

    # Take first 5-7 keywords for reasonable filename length
    keywords = keywords[:6]

    if not keywords:
        # Fallback if no keywords extracted
        keywords = ["output"]

    # Join with hyphens
    filename = "-".join(keywords)

    # Ensure filename isn't too long (max 50 chars before extension)
    if len(filename) > 50:
        filename = filename[:50].rsplit("-", 1)[0]

    return filename + extension


def save_output(content: str, directory: str, prompt: str) -> Path:
    """Save content to a file in the specified directory.

    Args:
        content: The content to save.
        directory: The directory to save to (relative or absolute).
        prompt: The prompt used to generate the filename.

    Returns:
        The path to the saved file.
    """
    # Resolve directory path
    dir_path = Path(directory).resolve()

    # Create directory if it doesn't exist
    dir_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = generate_filename(prompt)
    file_path = dir_path / filename

    # Handle existing files by adding a number suffix
    if file_path.exists():
        base = file_path.stem
        ext = file_path.suffix
        counter = 1
        while file_path.exists():
            file_path = dir_path / f"{base}-{counter}{ext}"
            counter += 1

    # Write content
    file_path.write_text(content)

    return file_path
