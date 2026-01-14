"""Project scanning and compilation database parsing."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CompileCommand:
    """A single compile command from compile_commands.json.

    Attributes:
        directory: Directory where the command was run
        file: Source file path
        command: Full command string
        arguments: Command arguments as a list
    """

    directory: str
    file: str
    command: str
    arguments: List[str]

    @classmethod
    def from_dict(cls, entry: dict) -> "CompileCommand":
        """Create from compile_commands.json entry.

        Args:
            entry: Dictionary from compile_commands.json

        Returns:
            CompileCommand instance
        """
        return cls(
            directory=entry["directory"],
            file=entry["file"],
            command=entry.get("command", ""),
            arguments=entry.get("arguments", entry.get("command", "").split()),
        )


@dataclass
class Project:
    """Information about a scanned project.

    Attributes:
        root: Project root directory
        files: List of source files found
        compile_db: Dictionary mapping file paths to compile commands
        language: Project language (C or C++)
    """

    root: Path
    files: List[Path]
    compile_db: Dict[str, CompileCommand]
    language: str = "C++"


class ProjectScanner:
    """Scanner for C/C++ projects."""

    # Default file extensions to scan
    DEFAULT_EXTENSIONS = {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx", ".hh"}

    # Directories to ignore
    DEFAULT_IGNORE_PATTERNS = {
        "build",
        "out",
        "dist",
        "target",
        "node_modules",
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "third_party",
        "third-party",
        "external",
    }

    @classmethod
    def scan(cls, root: Path) -> Project:
        """Scan a project directory.

        Args:
            root: Project root path

        Returns:
            Project object with files and compile database
        """
        root = root.resolve()

        # Try to load compile_commands.json
        compile_db_entries = cls._load_compile_db(root)
        compile_db = (
            {
                entry["file"]: CompileCommand.from_dict(entry)
                for entry in compile_db_entries
            }
            if compile_db_entries
            else {}
        )

        # Collect source files
        if compile_db:
            # Use files from compile database
            files = [Path(entry["file"]) for entry in compile_db_entries]
        else:
            # Fallback to directory scan
            files = cls._collect_files(root)

        # Filter files
        files = cls._filter_files(files, root)

        # Detect language
        language = cls._detect_language(files)

        return Project(root=root, files=files, compile_db=compile_db, language=language)

    @staticmethod
    def _load_compile_db(root: Path) -> Optional[List[dict]]:
        """Load compile_commands.json.

        Args:
            root: Project root directory

        Returns:
            List of compile command entries, or None if not found
        """
        # Common locations
        db_paths = [
            root / "compile_commands.json",
            root / "build" / "compile_commands.json",
            root / "builddir" / "compile_commands.json",
            root / ".build" / "compile_commands.json",
        ]

        for db_path in db_paths:
            if db_path.exists():
                try:
                    with open(db_path) as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    continue

        return None

    @staticmethod
    def _collect_files(root: Path) -> List[Path]:
        """Recursively collect source files.

        Args:
            root: Root directory to scan

        Returns:
            List of file paths
        """
        files = []
        for ext in ProjectScanner.DEFAULT_EXTENSIONS:
            files.extend(root.rglob(f"*{ext}"))
        return files

    @staticmethod
    def _filter_files(files: List[Path], root: Path) -> List[Path]:
        """Filter out unwanted files.

        Args:
            files: List of all found files
            root: Project root directory

        Returns:
            Filtered list of files
        """
        filtered = []
        ignore_patterns = ProjectScanner.DEFAULT_IGNORE_PATTERNS

        for file in files:
            try:
                # Check if file is in ignored directory
                relative = file.relative_to(root)
                if any(part in ignore_patterns for part in relative.parts):
                    continue

                # Check if file exists
                if not file.exists():
                    continue

                filtered.append(file)
            except ValueError:
                # File not relative to root, skip
                continue

        return filtered

    @staticmethod
    def _detect_language(files: List[Path]) -> str:
        """Detect if project is C or C++.

        Args:
            files: List of source files

        Returns:
            "C++" if any .cpp/.cc/.cxx files, "C" otherwise
        """
        cpp_extensions = {".cpp", ".cc", ".cxx", ".hpp", ".hxx"}
        for file in files:
            if file.suffix in cpp_extensions:
                return "C++"
        return "C"
