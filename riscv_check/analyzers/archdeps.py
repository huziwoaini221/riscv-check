"""Architecture-specific dependency detection.

Detects inline assembly, architecture-specific macros, and builtins.
"""

import re
from pathlib import Path
from typing import Generator, List, Optional

from clang.cindex import CompilationDatabase, Config, CursorKind, Index, TranslationUnit

from riscv_check.analyzers.base import BaseAnalyzer
from riscv_check.report.model import Issue, Severity


class ArchDepAnalyzer(BaseAnalyzer):
    """Analyzer for architecture-specific code.

    Detects:
    1. Inline assembly (not portable)
    2. Architecture-specific macros (#ifdef __x86_64__)
    3. Architecture-specific builtins (__builtin_ia32_*)
    """

    RULE_ASM = "ARCH_ASM"
    RULE_MACRO = "ARCH_MACRO"
    RULE_BUILTIN = "ARCH_BUILTIN"

    # Architecture-specific macro patterns
    ARCH_MACROS: List[str] = [
        r"#ifdef\s+__x86_64__",
        r"#if\s+defined\(__x86_64__\)",
        r"#ifdef\s+_M_X64",
        r"#ifdef\s+__i386__",
        r"#if\s+defined\(__i386__\)",
        r"#ifdef\s+__arm__",
        r"#ifdef\s+__aarch64__",
        r"#if\s+defined\(__arm__\)",
        r"#if\s+defined\(__aarch64__\)",
    ]

    # Architecture-specific builtin patterns
    ARCH_BUILTINS: List[str] = [
        r"__builtin_ia32_\w+",
        r"__builtin_ms_",
        r"__builtin_arm_",
        r"_mm_\w+",  # SSE/AVX intrinsics
    ]

    def __init__(self, compile_db: Optional[CompilationDatabase] = None, verbose: bool = False):
        """Initialize the analyzer.

        Args:
            compile_db: Optional compilation database
            verbose: Enable verbose output for debugging
        """
        super().__init__(compile_db)
        self.verbose = verbose

        # Ensure libclang is configured
        self._configure_libclang()

    def _configure_libclang(self) -> None:
        """Configure libclang path if not already set."""
        try:
            Config.get_cindex_library()
        except Exception:
            # Try common locations
            libclang_paths = [
                "/usr/lib/x86_64-linux-gnu/libclang-18.so.18",
                "/usr/lib/llvm-18/lib/libclang.so.18",
                "/usr/lib/llvm-18/lib/libclang.so.1",
            ]
            for libclang_path in libclang_paths:
                if Path(libclang_path).exists():
                    Config.set_library_file(libclang_path)
                    break

    def analyze_file(self, file: Path) -> Generator[Issue, None, None]:
        """Analyze a single file.

        Args:
            file: Path to the file to analyze

        Yields:
            Issue objects found in the file
        """
        # Try AST analysis for inline assembly
        try:
            yield from self._analyze_asm_ast(file)
        except Exception:
            # AST parsing failed, skip to next analysis
            pass

        # Text-based analysis for macros and builtins
        yield from self._analyze_macros_text(file)
        yield from self._analyze_builtins_text(file)

    def _analyze_asm_ast(self, file: Path) -> Generator[Issue, None, None]:
        """Detect inline assembly using AST analysis.

        Args:
            file: Path to the file

        Yields:
            Issues for inline assembly
        """
        compile_args = self._get_compile_args(file)

        try:
            index = Index.create()
            tu = index.parse(
                str(file),
                args=compile_args,
                options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
            )

            # Traverse AST to find asm statements
            for node in tu.cursor.walk_preorder():
                if node.kind == CursorKind.ASM_STMT:
                    # Get location
                    location = node.location
                    if not location.file:
                        continue

                    yield Issue(
                        rule_id=self.RULE_ASM,
                        severity=Severity.ERROR,
                        file=str(location.file.name),
                        line=location.line,
                        column=location.column,
                        message="Inline assembly is not portable to RISC-V",
                        suggestion=(
                            "Replace with C implementation or RISC-V intrinsics. "
                            "Consider using compiler intrinsics for common operations."
                        ),
                        verification="Cross-compilation with riscv64-linux-gnu-gcc will fail",
                    )
        except Exception as e:
            # AST parsing failed - log if verbose
            if self.verbose:
                import sys
                print(f"[DEBUG] AST parsing failed for {file}: {e}", file=sys.stderr)
            # Continue silently to not break analysis

    def _analyze_macros_text(self, file: Path) -> Generator[Issue, None, None]:
        """Detect architecture-specific macros using text matching.

        Args:
            file: Path to the file

        Yields:
            Issues for architecture-specific macros
        """
        try:
            content = file.read_text()
        except Exception:
            return

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check each pattern
            for pattern in self.ARCH_MACROS:
                if re.search(pattern, line):
                    # Extract the macro name for better message
                    macro_match = re.search(r"__(\w+)__", line)
                    macro_name = macro_match.group(0) if macro_match else "architecture-specific"

                    yield Issue(
                        rule_id=self.RULE_MACRO,
                        severity=Severity.WARNING,
                        file=str(file),
                        line=line_num,
                        column=line.find("#") + 1 if "#" in line else 1,
                        message=f"Architecture-specific macro detected: {macro_name}",
                        suggestion=(
                            "Replace with RISC-V compatible macros or "
                            "use feature detection (#ifdef __riscv)"
                        ),
                        verification="Check if code is compiled on RISC-V",
                    )
                    break  # Only report once per line

    def _analyze_builtins_text(self, file: Path) -> Generator[Issue, None, None]:
        """Detect architecture-specific builtins using text matching.

        Args:
            file: Path to the file

        Yields:
            Issues for architecture-specific builtins
        """
        try:
            content = file.read_text()
        except Exception:
            return

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check each pattern
            for pattern in self.ARCH_BUILTINS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    yield Issue(
                        rule_id=self.RULE_BUILTIN,
                        severity=Severity.WARNING,
                        file=str(file),
                        line=line_num,
                        column=match.start() + 1,
                        message=f"Architecture-specific builtin: {match.group()}",
                        suggestion=(
                            "Replace with portable alternatives or RISC-V intrinsics"
                        ),
                        verification="Cross-compilation may fail",
                    )

    def _get_compile_args(self, file: Path) -> List[str]:
        """Get compile arguments for a file.

        Args:
            file: Path to the file

        Returns:
            List of compile arguments
        """
        file_str = str(file)

        if self.compile_db and file_str in self.compile_db:
            cmd = self.compile_db[file_str]
            # Filter out output arguments
            return [arg for arg in cmd.arguments if not arg.startswith("-o") and arg != "-c"]

        # Fallback to default arguments
        return ["-I.", "-I/usr/include"]
