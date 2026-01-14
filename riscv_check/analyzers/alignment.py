"""Alignment issue detection.

Detects misaligned pointer casts and packed struct member access.
"""

from pathlib import Path
from typing import Dict, Generator, List, Optional, Set

from clang.cindex import (
    CompilationDatabase,
    Config,
    CursorKind,
    Index,
    TypeKind,
    TranslationUnit,
)

from riscv_check.analyzers.base import BaseAnalyzer
from riscv_check.report.model import Issue, Severity


class AlignmentAnalyzer(BaseAnalyzer):
    """Analyzer for alignment-related issues.

    Detects:
    1. Misaligned pointer casts (e.g., char* -> int*)
    2. Packed struct member access
    """

    RULE_PTR_CAST = "ALIGN_PTR_CAST"
    RULE_PACKED_FIELD = "ALIGN_PACKED_FIELD"

    # Type alignment requirements (in bytes)
    ALIGNMENT_MAP: Dict[TypeKind, int] = {
        TypeKind.CHAR_S: 1,
        TypeKind.CHAR_U: 1,
        TypeKind.SHORT: 2,
        TypeKind.USHORT: 2,
        TypeKind.INT: 4,
        TypeKind.UINT: 4,
        TypeKind.LONG: 8,
        TypeKind.ULONG: 8,
        TypeKind.LONGLONG: 8,
        TypeKind.ULONGLONG: 8,
        TypeKind.FLOAT: 4,
        TypeKind.DOUBLE: 8,
        TypeKind.LONGDOUBLE: 16,
        TypeKind.POINTER: 8,  # Assuming 64-bit
    }

    def __init__(self, compile_db: Optional[CompilationDatabase] = None, verbose: bool = False):
        """Initialize the analyzer.

        Args:
            compile_db: Optional compilation database
            verbose: Enable verbose output for debugging
        """
        super().__init__(compile_db)
        self.packed_structs: Set[str] = set()
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
        # Reset packed struct tracking for this file
        self.packed_structs.clear()

        compile_args = self._get_compile_args(file)

        try:
            index = Index.create()
            tu = index.parse(
                str(file),
                args=compile_args,
                options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
            )

            # Traverse AST
            for node in tu.cursor.get_children():
                yield from self._visit_node(node)
        except Exception as e:
            # AST parsing failed - log if verbose
            if self.verbose:
                import sys
                print(f"[DEBUG] AST parsing failed for {file}: {e}", file=sys.stderr)
            # Continue silently to not break analysis

    def _visit_node(self, node) -> Generator[Issue, None, None]:
        """Recursively visit AST nodes.

        Args:
            node: AST node to visit

        Yields:
            Issues found at this node or its children
        """
        # Check for pointer casts
        if node.kind in {
            CursorKind.CSTYLE_CAST_EXPR,
            CursorKind.CXX_REINTERPRET_CAST_EXPR,
            CursorKind.CXX_STATIC_CAST_EXPR,
        }:
            issue = self._check_pointer_cast(node)
            if issue:
                yield issue

        # Track packed structs
        if node.kind == CursorKind.STRUCT_DECL:
            self._check_packed_struct(node)

        # Check for packed struct member access
        if node.kind == CursorKind.MEMBER_REF_EXPR:
            issue = self._check_packed_member_access(node)
            if issue:
                yield issue

        # Recursively visit children
        for child in node.get_children():
            yield from self._visit_node(child)

    def _check_pointer_cast(self, cast_expr) -> Optional[Issue]:
        """Check for dangerous pointer casts.

        Args:
            cast_expr: Cast expression node

        Returns:
            Issue if cast is dangerous, None otherwise
        """
        try:
            # Get the operand (first child of the cast expression)
            children = list(cast_expr.get_children())
            if not children:
                return None
            src_type = children[0].type
            dst_type = cast_expr.type
        except Exception:
            return None

        # Only check pointer-to-pointer casts
        if src_type.kind != TypeKind.POINTER or dst_type.kind != TypeKind.POINTER:
            return None

        # Get pointee types
        try:
            src_pointee = src_type.get_pointee()
            dst_pointee = dst_type.get_pointee()
        except Exception:
            return None

        # Get alignment requirements
        src_align = self.ALIGNMENT_MAP.get(src_pointee.kind, 1)
        dst_align = self.ALIGNMENT_MAP.get(dst_pointee.kind, 1)

        # Core rule: target alignment > source alignment is dangerous
        if dst_align > src_align:
            location = cast_expr.location
            if location.file:
                return Issue(
                    rule_id=self.RULE_PTR_CAST,
                    severity=Severity.ERROR,
                    file=str(location.file.name),
                    line=location.line,
                    column=location.column,
                    message=(
                        f"Casting pointer from {src_pointee.spelling} "
                        f"(align={src_align}) to {dst_pointee.spelling} "
                        f"(align={dst_align}) may cause misaligned access"
                    ),
                    suggestion=(
                        f"Use memcpy to copy data, or ensure alignment "
                        f"using __attribute__((aligned({dst_align})))"
                    ),
                    verification=(
                        "Compile with -fsanitize=alignment or run "
                        "under qemu-riscv64 to detect SIGBUS"
                    ),
                )

        return None

    def _check_packed_struct(self, struct_decl) -> None:
        """Check if struct is packed and record it.

        Args:
            struct_decl: Struct declaration node
        """
        # Check for packed attribute
        for child in struct_decl.get_children():
            if child.kind == CursorKind.PACKED_ATTR or (
                hasattr(child, 'spelling') and "packed" in child.spelling.lower()
            ):
                self.packed_structs.add(struct_decl.usr)

    def _check_packed_member_access(self, member_expr) -> Optional[Issue]:
        """Check for access to packed struct members.

        Args:
            member_expr: Member expression node

        Returns:
            Issue if accessing non-char member of packed struct, None otherwise
        """
        try:
            member_type = member_expr.type
        except Exception:
            return None

        # char types are safe (1-byte aligned)
        if member_type.kind in {TypeKind.CHAR_S, TypeKind.CHAR_U, TypeKind.UCHAR}:
            return None

        # Get parent struct declaration
        struct_decl = member_expr.semantic_parent
        if not struct_decl:
            return None

        # Check if it's a packed struct
        if struct_decl.usr in self.packed_structs:
            location = member_expr.location
            if location.file:
                return Issue(
                    rule_id=self.RULE_PACKED_FIELD,
                    severity=Severity.ERROR,
                    file=str(location.file.name),
                    line=location.line,
                    column=location.column,
                    message=(
                        f"Accessing member '{member_expr.spelling}' "
                        f"of packed struct may cause misaligned access"
                    ),
                    suggestion=(
                        f"Use memcpy or ensure natural alignment "
                        f"of struct instances"
                    ),
                    verification=(
                        "Access may trigger SIGBUS on RISC-V. "
                        "Test with qemu-riscv64."
                    ),
                )

        return None

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
            return [
                arg
                for arg in cmd.arguments
                if not arg.startswith("-o") and arg != "-c"
            ]

        # Fallback to default arguments
        return ["-I.", "-I/usr/include"]
