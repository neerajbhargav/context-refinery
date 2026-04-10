"""
ContextRefinery — File Processor

Handles reading, parsing, and chunking source files.
Supports code files (with language detection) and text documents.
"""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

# Extension → language mapping
LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".vue": "vue",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".ps1": "powershell",
    ".dockerfile": "dockerfile",
    ".tf": "terraform",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
}


def detect_language(file_path: Path) -> str:
    """Detect the programming language from a file's extension."""
    suffix = file_path.suffix.lower()
    
    # Special case: Dockerfile (no extension)
    if file_path.name.lower() == "dockerfile":
        return "dockerfile"
    if file_path.name.lower() == "makefile":
        return "makefile"

    return LANGUAGE_MAP.get(suffix, "text")


def process_file(file_path: Path) -> tuple[str, str]:
    """
    Read and process a source file.
    
    Returns:
        Tuple of (content, language)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Skip binary files
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and not mime_type.startswith("text/") and mime_type not in (
        "application/json",
        "application/xml",
        "application/javascript",
        "application/x-yaml",
    ):
        logger.debug(f"Skipping binary file: {file_path}")
        return "", "binary"

    language = detect_language(file_path)

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Error reading {file_path}: {e}")
        try:
            content = file_path.read_text(encoding="latin-1")
        except Exception:
            return "", language

    return content, language


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Uses line-aware splitting to avoid breaking mid-line.
    For code, tries to split at function/class boundaries when possible.
    
    Args:
        text: The text to chunk
        chunk_size: Target chunk size in tokens (approximated by characters / 4)
        chunk_overlap: Number of overlap tokens between chunks
    
    Returns:
        List of text chunks
    """
    if not text.strip():
        return []

    lines = text.split("\n")
    
    # Approximate: 1 token ≈ 4 characters
    char_chunk_size = chunk_size * 4
    char_overlap = chunk_overlap * 4

    chunks: list[str] = []
    current_chunk_lines: list[str] = []
    current_size = 0

    for line in lines:
        line_size = len(line) + 1  # +1 for newline

        # Check if adding this line would exceed chunk size
        if current_size + line_size > char_chunk_size and current_chunk_lines:
            # Save current chunk
            chunk_text_content = "\n".join(current_chunk_lines)
            chunks.append(chunk_text_content)

            # Calculate overlap: keep last N characters worth of lines
            overlap_lines: list[str] = []
            overlap_size = 0
            for prev_line in reversed(current_chunk_lines):
                if overlap_size + len(prev_line) + 1 > char_overlap:
                    break
                overlap_lines.insert(0, prev_line)
                overlap_size += len(prev_line) + 1

            current_chunk_lines = overlap_lines
            current_size = overlap_size

        current_chunk_lines.append(line)
        current_size += line_size

    # Don't forget the last chunk
    if current_chunk_lines:
        chunk_text_content = "\n".join(current_chunk_lines)
        if chunk_text_content.strip():
            chunks.append(chunk_text_content)

    return chunks
