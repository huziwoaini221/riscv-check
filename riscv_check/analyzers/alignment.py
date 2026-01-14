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

    # Standard library functions that return properly aligned pointers
    # Note: Project-specific functions (like xRealloc) should be detected
    # via __attribute__((malloc)) instead of hardcoding
    SAFE_ALLOC_FUNCTIONS = {
        "malloc",
        "calloc",
        "realloc",
        "aligned_alloc",
    }

    def __init__(self, compile_db: Optional[CompilationDatabase] = None, verbose: bool = False):
        """Initialize the analyzer.

        Args:
            compile_db: Optional compilation database
            verbose: Enable verbose output for debugging
        """
        super().__init__(compile_db)
        self.packed_structs: Set[str] = set()
        self.malloc_functions: Set[str] = set()  # Functions with malloc attribute
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
        # Reset tracking sets for this file
        self.packed_structs.clear()
        self.malloc_functions.clear()

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
        # Track functions with malloc attribute
        if node.kind == CursorKind.FUNCTION_DECL:
            self._check_malloc_attribute(node)

        # Check for explicit pointer casts
        if node.kind in {
            CursorKind.CSTYLE_CAST_EXPR,
            CursorKind.CXX_REINTERPRET_CAST_EXPR,
            CursorKind.CXX_STATIC_CAST_EXPR,
        }:
            issue = self._check_pointer_cast(node)
            if issue:
                yield issue

        # Check for implicit pointer casts (assignments)
        if node.kind == CursorKind.ASSIGNMENT_OPERATOR:
            issue = self._check_implicit_cast(node)
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

    def _check_malloc_attribute(self, func_decl) -> None:
        """Check if a function has the malloc attribute.

        Functions with __attribute__((malloc)) return pointers that don't
        alias with any other pointers and are typically aligned.

        Args:
            func_decl: Function declaration node
        """
        try:
            # Check for malloc attribute in the function's attributes
            for attr in func_decl.get_children():
                if attr.kind == CursorKind.ANNOTATE_ATTR:
                    # Check if this is __attribute__((malloc))
                    attr_text = attr.spelling
                    if "malloc" in attr_text.lower():
                        self.malloc_functions.add(func_decl.spelling)
                        if self.verbose:
                            import sys
                            print(
                                f"[DEBUG] Found malloc attribute on {func_decl.spelling}()",
                                file=sys.stderr
                            )
                        break
        except Exception:
            pass

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
            operand = children[0]
            src_type = operand.type
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

        # Core rule: target alignment > source alignment is potentially dangerous
        if dst_align > src_align:
            # NEW: Check if the operand is from a safe memory allocation function
            if self._is_safe_aligned_pointer(operand):
                # This cast is safe - the pointer comes from an aligned allocator
                return None

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

    def _is_safe_aligned_pointer(self, node) -> bool:
        """Check if a node represents a pointer from a safe aligned allocator.

        This reduces false positives by ignoring casts from:
        - Standard library functions (malloc, calloc, realloc, aligned_alloc)
        - Functions with __attribute__((malloc)) (dynamically detected)
        - Compiler-guaranteed aligned allocators

        Args:
            node: AST node to check

        Returns:
            True if the pointer is from a safe allocator, False otherwise
        """
        # Case 1: Direct function call (e.g., (char**)malloc(...))
        if node.kind == CursorKind.CALL_EXPR:
            # Get the function being called
            try:
                children = list(node.get_children())
                if children and children[0].kind == CursorKind.DECL_REF_EXPR:
                    func_name = children[0].spelling

                    # Check standard library functions
                    if func_name in self.SAFE_ALLOC_FUNCTIONS:
                        if self.verbose:
                            import sys
                            print(
                                f"[DEBUG] Skipping cast from {func_name}() - "
                                f"standard allocator returns aligned pointer",
                                file=sys.stderr
                            )
                        return True

                    # Check functions with malloc attribute (dynamically detected)
                    if func_name in self.malloc_functions:
                        if self.verbose:
                            import sys
                            print(
                                f"[DEBUG] Skipping cast from {func_name}() - "
                                f"has __attribute__((malloc))",
                                file=sys.stderr
                            )
                        return True
            except Exception:
                pass

        # Case 2: UnaryOperator on function result (e.g., *(char**)malloc(...))
        # This is rare but possible
        try:
            if node.kind == CursorKind.UNARY_OPERATOR:
                children = list(node.get_children())
                if children and children[0].kind == CursorKind.CALL_EXPR:
                    return self._is_safe_aligned_pointer(children[0])
        except Exception:
            pass

        # Case 3: ParenExpr wrapping a safe expression
        try:
            if node.kind == CursorKind.PAREN_EXPR:
                children = list(node.get_children())
                if children:
                    return self._is_safe_aligned_pointer(children[0])
        except Exception:
            pass

        return False

    def _check_implicit_cast(self, assign_expr) -> Optional[Issue]:
        """Check for dangerous implicit pointer casts in assignments.

        This detects cases like:
            char** out;
            out = xRealloc(...);  // void* → char** implicit cast

        Args:
            assign_expr: Assignment expression node

        Returns:
            Issue if implicit cast is dangerous, None otherwise
        """
        try:
            # Get left and right operands of assignment
            children = list(assign_expr.get_children())
            if len(children) < 2:
                return None

            left_operand = children[0]
            right_operand = children[1]

            # Get types
            left_type = left_operand.type
            right_type = right_operand.type
        except Exception:
            return None

        # Only check pointer-to-pointer assignments
        try:
            if left_type.kind != TypeKind.POINTER or right_type.kind != TypeKind.POINTER:
                return None

            left_pointee = left_type.get_pointee()
            right_pointee = right_type.get_pointee()
        except Exception:
            return None

        # Get alignment requirements
        left_align = self.ALIGNMENT_MAP.get(left_pointee.kind, 1)
        right_align = self.ALIGNMENT_MAP.get(right_pointee.kind, 1)

        # Core rule: target alignment > source alignment is potentially dangerous
        if left_align > right_align:
            # Check if the right operand is from a safe memory allocation function
            if self._is_safe_aligned_pointer(right_operand):
                # This cast is safe - the pointer comes from an aligned allocator
                return None

            location = assign_expr.location
            if location.file:
                return Issue(
                    rule_id=self.RULE_PTR_CAST,
                    severity=Severity.ERROR,
                    file=str(location.file.name),
                    line=location.line,
                    column=location.column,
                    message=(
                        f"Implicit cast from {right_pointee.spelling} "
                        f"(align={right_align}) to {left_pointee.spelling} "
                        f"(align={left_align}) may cause misaligned access"
                    ),
                    suggestion=(
                        f"Use explicit cast with memcpy, or ensure alignment "
                        f"using __attribute__((aligned({left_align})))"
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
