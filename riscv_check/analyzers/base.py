"""Base class for all analyzers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Optional

from clang.cindex import CompilationDatabase

from riscv_check.report.model import Issue


class BaseAnalyzer(ABC):
    """Base class for all static analyzers.

    All analyzers should inherit from this class and implement the
    analyze_file method.
    """

    def __init__(self, compile_db: Optional[CompilationDatabase] = None):
        """Initialize the analyzer.

        Args:
            compile_db: Optional compilation database for accurate parsing
        """
        self.compile_db = compile_db

    @abstractmethod
    def analyze_file(self, file: Path) -> Generator[Issue, None, None]:
        """Analyze a single file.

        Args:
            file: Path to the file to analyze

        Yields:
            Issue objects found in the file
        """
        raise NotImplementedError("Subclasses must implement analyze_file")
