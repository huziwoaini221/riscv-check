# riscv-check

[English](README.md) | [简体中文](README_zh.md)

**Static analysis tool for detecting potential RISC-V migration issues in C/C++ projects**

[![PyPI version](https://badge.fury.io/py/riscv-check.svg)](https://pypi.org/project/riscv-check/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

`riscv-check` scans C/C++ codebases and detects patterns that **may** cause issues on architectures with strict alignment requirements:

- Potential misaligned memory access
- Architecture-specific inline assembly
- Missing RISC-V code paths
- Unaligned pointer casts

## Why This Tool Matters

### The Problem

This code **may work** on x86_64 but **can result in undefined behavior** on architectures with strict alignment requirements:

```c
char *p = malloc(10);
p++;
int *i = (int*)p;  // Potentially misaligned address
*i = 42;  // May result in alignment fault
```

**Why**: x86_64 tolerates misalignment in many cases. RISC-V requires strict alignment for types like int (typically 4-byte).

### The Solution

`riscv-check` detects these patterns **before** migration through static analysis:

```bash
$ riscv-check /path/to/project

[ERROR] src/network.c:128 ALIGN_PTR_CAST
  Casting char* to int* without alignment verification
```

**Note**: This is a static analysis tool. Findings require human verification.

## Quick Start

### Installation

```bash
pip install riscv-check
```

### Basic Usage

```bash
# Scan a project
riscv-check /path/to/project

# Generate maintainer-style report (one screen, no emojis)
riscv-check /path/to/project --output report.md --report-style maintainer

# Skip cross-compilation validation
riscv-check /path/to/project --no-compile
```

### Report Modes

- `--report-style maintainer` (default): One-screen professional format
- `--report-style concise`: Standard < 2 screen reports
- `--report-style minimal`: Bug report only, < 1 screen
- `--report-style verbose`: Detailed multi-page reports

### Language Control

- `--language en`: English only (no mixed languages)
- `--language zh`: Chinese only

## What It Detects

### 1. Misaligned Pointer Casts

**Pattern**: Casting pointers to stricter alignment requirements

```c
// Potential issue on strict-alignment architectures
char *p = get_buffer();
p++;  // May become misaligned
int *i = (int*)p;  // Requires 4-byte alignment
*i = 42;  // Undefined behavior if misaligned
```

**Detection**: AST-based static analysis tracking pointer sources and cast targets.

---

### 2. Packed Struct Access

**Pattern**: Accessing non-char members of packed structs

```c
struct __attribute__((packed)) Packet {
    char type;
    int value;  // Misaligned field
};

int x = packet->value;  // May result in alignment fault
```

**Detection**: Packed struct field access patterns.

---

### 3. Inline Assembly

**Pattern**: Architecture-specific assembly code

```c
// Not portable across architectures
__asm__ volatile("movq %rax, %rbx");
```

**Detection**: Inline asm blocks, architecture-specific instructions.

---

### 4. Architecture Macros

**Pattern**: Code only compiled on specific architectures

```c
#ifdef __x86_64__
    // Missing RISC-V implementation
#endif
```

**Detection**: Unbalanced architecture-specific code paths.

## Risk Assessment

**Risk Score**: 0-100 (heuristic, non-authoritative)

The score provides a rough indication of migration readiness based on detected patterns. It is **not** a correctness guarantee.

| Score | Status | Recommendation |
|-------|--------|----------------|
| 80-100 | LOW RISK | Fewer patterns detected |
| 50-79 | MEDIUM RISK | Some ERROR-level patterns found |
| 0-49 | HIGH RISK | Many ERROR-level patterns found |

**Scoring Method (heuristic)**:
- Base score: 100
- Each ERROR: -20 points
- Each WARNING: -8 points
- Build failure: -30 points

**Important**: This is a heuristic scoring system. Actual migration readiness requires human review.

## Architecture

```
Input: C/C++ project
  │
  ├─> 1. Project Scanner
  │     - Parse compile_commands.json
  │     - Collect source files
  │
  ├─> 2. Static Analysis (libclang)
  │     - AST traversal
  │     - Pattern matching
  │     - Type checking
  │
  ├─> 3. Cross-compilation Validation (optional)
  │     - riscv64-linux-gnu-gcc
  │     - Build error extraction
  │
  └─> 4. Report Generation
        - Console output (Rich)
        - Markdown file
        - Maintainer format (one screen)
```

## Requirements

### Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | Supported | Primary development platform |
| macOS | Supported | Tested and verified |
| Windows + WSL 2 | Supported | Recommended for Windows |
| Windows Native | Experimental | Complex setup |

### System Requirements

- Python 3.10+
- clang + libclang (for AST parsing)
- riscv64-linux-gnu-gcc (optional, for cross-compilation validation)

### Installation

**Ubuntu/Debian**:
```bash
sudo apt install clang llvm libclang-dev
sudo apt install gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
```

**macOS**:
```bash
brew install llvm
brew install riscv-tools
```

## Documentation

- [Installation Guide](docs/INSTALL.md)
- [Windows Installation](docs/INSTALL_WINDOWS.md)
- [User Guide](docs/USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](docs/CONTRIBUTING.md)

## Development Notes

### Learning Experience: False Positive Case Study (2025-01)

**Note**: This section describes a learning experience from tool development.

#### Background

During early development, this tool was tested on a medium-sized, well-maintained C codebase to understand real-world RISC-V migration patterns.

#### Analysis Details

- **Codebase**: ~40K lines of C code
- **Analysis time**: ~5 minutes
- **Result**: 1 alignment issue detected (later confirmed as false positive)

#### Tool Improvement Journey

**Initial Finding**:
- Tool generated verbose report with emojis
- Flagged a custom allocator function as potential issue
- Issue submitted to project maintainers

**Maintainer Feedback**:
Project maintainers provided professional feedback:
- **Report quality**: Too verbose, overly formatted
- **Technical accuracy**: Suggested using compiler attributes instead of hardcoded function lists
- **Detection consistency**: Noted inconsistent handling of explicit vs implicit casts

**Improvements Made**:
- Implemented dynamic `__attribute__((malloc))` detection
- Added implicit cast detection for consistency
- Complete report format overhaul:
  - Maintainer-style one-screen reports
  - Removed formatting decorations
  - Added evidence levels (E0/E1/E2)
  - Single language enforcement

#### Lessons Learned

1. **False Positives**: The flagged case was NOT a real issue because the allocator internally uses standard functions that return aligned memory per the C standard.

2. **Tool Maturity**: Early versions had hardcoded assumptions about project-specific functions. Now uses compiler-standard attributes for portability.

3. **Report Quality**: Maintainer-friendly reports require:
   - Conciseness
   - Minimal formatting
   - Evidence-based reasoning
   - Professional technical writing

**Note**: The submitted issue was closed as a false positive. The analyzed project had no actual alignment issues. This experience drove significant tool improvements.

## Contributing

Contributions welcome. See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

```bash
# Development setup
git clone https://github.com/huziwoaini221/riscv-check
cd riscv-check
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
black riscv_check/
mypy riscv_check/
```

## Roadmap

### v0.1.0 (Current - MVP)
- [x] Misaligned pointer cast detection
- [x] Packed struct access detection
- [x] Inline assembly detection
- [x] Architecture-specific macros
- [x] Cross-compilation validation
- [x] Maintainer-style reports
- [x] Evidence level classification

### v0.2.0 (Planned)
- [ ] QEMU dynamic validation
- [ ] Integration with CI/CD pipelines
- [ ] Additional detection rules (atomics, cache coherence)

### v0.3.0 (Future)
- [ ] Web UI for report viewing
- [ ] Team collaboration features

## FAQ

**Q: How accurate is the detection?**

A: The tool aims for high precision on ERROR-level findings, but false positives are expected, especially in early versions. All findings require human verification. Uses:
- Pointer source tracking
- `__attribute__((malloc))` detection
- Cross-compilation validation

**Q: Can it handle large projects?**

A: Tested on projects with 10,000+ files. Scales linearly with project size.

**Q: Does it modify code?**

A: No. Read-only analysis and reporting.

**Q: What if compile_commands.json is missing?**

A: Tool works without it but with reduced accuracy. Generate with:
```bash
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## Acknowledgments

I would like to thank contributors from an open source project for their technical feedback on alignment assumptions, allocator semantics, and report quality standards.

Their comments helped identify incorrect assumptions and guided significant improvements to this tool's detection methodology and reporting format.

Any remaining mistakes are my own.

### Dependencies

- [clang](https://clang.llvm.org/) - C/C++ parsing and AST traversal
- [click](https://click.palletsprojects.com/) - CLI framework
- [rich](https://rich.readthedocs.io/) - Terminal output formatting
- [RISC-V International](https://riscv.org/) - Architecture specifications

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- [Report bugs](https://github.com/huziwoaini221/riscv-check/issues)
- [Feature requests](https://github.com/huziwoaini221/riscv-check/discussions)
- Email: thelazypig321@qq.com

---

**Static analysis for RISC-V migration**

If you find this tool useful, please consider starring the repo!
