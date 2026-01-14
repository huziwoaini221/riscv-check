"""Cross-compilation validator for RISC-V."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CompileResult:
    """Result of cross-compilation check."""
    success: bool
    errors: List[str]
    warnings: List[str]
    skipped: bool = False
    file_path: Optional[Path] = None


class CrossCompileValidator:
    """Validates C/C++ files using RISC-V cross-compiler."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.compiler = "riscv64-linux-gnu-gcc"

    def check_file(self, file_path: Path) -> CompileResult:
        """Check if file compiles with RISC-V cross-compiler.

        Args:
            file_path: Path to C/C++ source file

        Returns:
            CompileResult with success status and any errors/warnings
        """

        # Check if file is C/C++
        if file_path.suffix not in {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx", ".hh"}:
            return CompileResult(
                success=True,
                errors=[],
                warnings=[],
                skipped=True,
                file_path=file_path
            )

        # Check if compiler exists
        if not self._compiler_exists():
            return CompileResult(
                success=True,
                errors=[],
                warnings=[],
                skipped=True,
                file_path=file_path
            )

        # Try to compile
        try:
            if self.verbose:
                print(f"  Cross-compiling: {file_path}")

            # Use -w to suppress warnings for now, -Werror later
            result = subprocess.run(
                [
                    self.compiler,
                    "-c",
                    "-w",  # Suppress warnings for faster validation
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Success - check for warnings in stderr
                warnings = self._parse_warnings(result.stderr) if result.stderr else []

                return CompileResult(
                    success=True,
                    errors=[],
                    warnings=warnings,
                    skipped=False,
                    file_path=file_path
                )
            else:
                # Compilation failed
                errors = result.stderr.split('\n') if result.stderr else [result.stdout]

                # Filter out empty strings
                errors = [e for e in errors if e.strip()]

                return CompileResult(
                    success=False,
                    errors=errors,
                    warnings=[],
                    skipped=False,
                    file_path=file_path
                )

        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                errors=["Compilation timed out after 30 seconds"],
                warnings=[],
                skipped=False,
                file_path=file_path
            )
        except Exception as e:
            return CompileResult(
                success=False,
                errors=[f"Compilation error: {str(e)}"],
                warnings=[],
                skipped=False,
                file_path=file_path
            )

    def check_files(self, file_paths: List[Path]) -> List[CompileResult]:
        """Check multiple files.

        Args:
            file_paths: List of C/C++ source files

        Returns:
            List of CompileResult objects
        """
        results = []

        for file_path in file_paths:
            result = self.check_file(file_path)
            results.append(result)

        return results

    def _compiler_exists(self) -> bool:
        """Check if cross-compiler is installed."""
        try:
            result = subprocess.run(
                ["which", self.compiler],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _parse_warnings(self, output: str) -> List[str]:
        """Parse warnings from compiler output.

        Args:
            output: Compiler stderr output

        Returns:
            List of warning messages
        """
        warnings = []

        for line in output.split('\n'):
            line = line.strip()
            if 'warning:' in line:
                warnings.append(line)

        return warnings
