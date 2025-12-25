"""Tests for output file handling."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from aicx.output import generate_filename, save_output


class TestGenerateFilename:
    """Tests for filename generation from prompts."""

    def test_basic_prompt(self):
        """Test basic prompt generates reasonable filename."""
        prompt = "Create an abstract class for fetching racers from the API"
        filename = generate_filename(prompt)
        assert filename.endswith(".md")
        assert "abstract" in filename
        assert "class" in filename
        assert "racers" in filename or "fetching" in filename

    def test_removes_stop_words(self):
        """Test that common stop words are removed."""
        prompt = "What is the best way to implement a factory pattern"
        filename = generate_filename(prompt)
        assert "what" not in filename
        assert "the" not in filename
        assert "factory" in filename
        assert "pattern" in filename

    def test_handles_special_characters(self):
        """Test that special characters are handled."""
        prompt = "Design a REST API for user/auth endpoints!"
        filename = generate_filename(prompt)
        assert "/" not in filename
        assert "!" not in filename
        assert "rest" in filename or "api" in filename

    def test_custom_extension(self):
        """Test custom file extension."""
        prompt = "Write Python code for data processing"
        filename = generate_filename(prompt, extension=".py")
        assert filename.endswith(".py")

    def test_max_length(self):
        """Test filename doesn't exceed max length."""
        prompt = " ".join(["word"] * 50)  # Very long prompt
        filename = generate_filename(prompt)
        # 50 chars max + extension
        assert len(filename) <= 54

    def test_empty_after_filtering(self):
        """Test fallback when all words are filtered."""
        prompt = "The a an is are"
        filename = generate_filename(prompt)
        assert filename == "output.md"

    def test_short_words_filtered(self):
        """Test that very short words are filtered."""
        prompt = "Go do it now"
        filename = generate_filename(prompt)
        # "go", "do", "it" are 2 chars, "now" is 3 chars
        assert "now" in filename or filename == "output.md"

    def test_hyphenated_output(self):
        """Test that words are joined with hyphens."""
        prompt = "Design a singleton pattern implementation"
        filename = generate_filename(prompt)
        assert "-" in filename

    def test_lowercase_output(self):
        """Test that filename is lowercase."""
        prompt = "Create a REST API with OAuth"
        filename = generate_filename(prompt)
        assert filename == filename.lower()


class TestSaveOutput:
    """Tests for saving output to files."""

    def test_save_creates_file(self):
        """Test that save_output creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "# Test Content\n\nThis is a test."
            prompt = "Create a test document"

            file_path = save_output(content, tmpdir, prompt)

            assert file_path.exists()
            assert file_path.read_text() == content

    def test_save_creates_directory(self):
        """Test that save_output creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "docs"
            content = "Test content"
            prompt = "Test document"

            file_path = save_output(content, str(nested_dir), prompt)

            assert nested_dir.exists()
            assert file_path.exists()

    def test_save_handles_existing_file(self):
        """Test that save_output handles existing files by adding suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content1 = "First content"
            content2 = "Second content"
            prompt = "Same prompt for both"

            path1 = save_output(content1, tmpdir, prompt)
            path2 = save_output(content2, tmpdir, prompt)

            assert path1 != path2
            assert path1.exists()
            assert path2.exists()
            assert path1.read_text() == content1
            assert path2.read_text() == content2
            # Second file should have -1 suffix
            assert "-1" in path2.stem

    def test_save_returns_absolute_path(self):
        """Test that save_output returns absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "Test"
            prompt = "Test prompt"

            file_path = save_output(content, tmpdir, prompt)

            assert file_path.is_absolute()

    def test_save_with_relative_directory(self):
        """Test save_output with relative directory."""
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                content = "Test content"
                prompt = "Test document"

                file_path = save_output(content, "./output", prompt)

                assert file_path.exists()
                assert (Path(tmpdir) / "output").exists()
            finally:
                os.chdir(original_dir)

    def test_filename_from_prompt(self):
        """Test that filename is derived from prompt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "Content"
            prompt = "Design abstract class for racing API"

            file_path = save_output(content, tmpdir, prompt)

            assert "abstract" in file_path.stem or "racing" in file_path.stem
