"""
riscv-check - RISC-V migration risk detector for C/C++ projects

This package provides static analysis tools to detect issues that may cause
problems when migrating C/C++ projects from x86/ARM to RISC-V architecture.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Auto-configure libclang path
import os
from pathlib import Path

try:
    from clang.cindex import Config, LibclangError

    # Only set if not already configured
    try:
        Config.get_cindex_library()
    except LibclangError:
        # Find libclang in common locations
        libclang_paths = [
            "/usr/lib/x86_64-linux-gnu/libclang-18.so.18",
            "/usr/lib/x86_64-linux-gnu/libclang-17.so.1",
            "/usr/lib/x86_64-linux-gnu/libclang.so",
            "/usr/lib/llvm-18/lib/libclang.so.18",
            "/usr/lib/llvm-17/lib/libclang.so.17",
        ]

        for libclang_path in libclang_paths:
            if Path(libclang_path).exists():
                Config.set_library_file(libclang_path)
                break
except Exception:
    # clang not available, skip configuration
    pass

from riscv_check.report.model import Issue, Severity, Report

__all__ = [
    "__version__",
    "Issue",
    "Severity",
    "Report",
]
