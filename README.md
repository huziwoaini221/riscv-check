# riscv-check

[English](README.md) | [简体中文](README_zh.md)

**Static analysis tool for detecting RISC-V migration issues in C/C++ projects**

[![PyPI version](https://badge.fury.io/py/riscv-check.svg)](https://pypi.org/project/riscv-check/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

`riscv-check` scans C/C++ codebases and detects patterns that cause issues on RISC-V architecture:

- Misaligned memory access (SIGBUS on RISC-V)
- Architecture-specific inline assembly
- Missing RISC-V code paths
- Unaligned pointer casts

## Why This Tool Matters

### The Problem

This code works on x86_64 but crashes on RISC-V:

```c
char *p = malloc(10);
p++;
int *i = (int*)p;  // Misaligned address
*i = 42;  // SIGBUS on RISC-V
```

**Why**: x86_64 tolerates misalignment. RISC-V requires strict alignment for int (4-byte).

### The Solution

`riscv-check` detects these issues **before** migration through static analysis:

```bash
$ riscv-check /path/to/project

[ERROR] src/network.c:128 ALIGN_PTR_CAST
  Casting char* to int* without alignment verification
```

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

**Issue**: Casting pointers to stricter alignment requirements

```c
// ERROR: Will crash on RISC-V
char *p = get_buffer();
p++;  // May become misaligned
int *i = (int*)p;  // Requires 4-byte alignment
*i = 42;  // SIGBUS if misaligned
```

**Detection**: AST-based static analysis tracking pointer sources and cast targets.

---

### 2. Packed Struct Access

**Issue**: Accessing non-char members of packed structs

```c
struct __attribute__((packed)) Packet {
    char type;
    int value;  // Misaligned field
};

int x = packet->value;  // SIGBUS on RISC-V
```

**Detection**: Packed struct field access patterns.

---

### 3. Inline Assembly

**Issue**: Architecture-specific assembly code

```c
// ERROR: x86-specific
__asm__ volatile("movq %rax, %rbx");
```

**Detection**: Inline asm blocks, architecture-specific instructions.

---

### 4. Architecture Macros

**Issue**: Code only compiled on specific architectures

```c
#ifdef __x86_64__
    // Missing RISC-V implementation
#endif
```

**Detection**: Unbalanced architecture-specific code paths.

## Risk Scoring

**Risk Score**: 0-100 (higher is better)

| Score | Status | Recommendation |
|-------|--------|----------------|
| 80-100 | RECOMMENDED | Ready to migrate |
| 50-79 | NEEDS FIXES | Fix ERRORs first |
| 0-49 | NOT RECOMMENDED | High risk of crashes |

**Scoring Method**:
- Base score: 100
- Each ERROR: -20 points
- Each WARNING: -8 points
- Build failure: -30 points

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

## Learning Project: htop (2025-01)

**Note**: This section describes a learning experience, not a production deployment.

### Background

As an MVP-stage tool, riscv-check was tested on [htop](https://github.com/htop-dev/htop) - a well-maintained C project - to understand RISC-V migration challenges in real-world codebases.

### Analysis Details

**Project**: htop - Interactive process viewer
- **Codebase**: 127 C files, 44,524 lines
- **Analysis time**: ~5 minutes
- **Result**: 1 alignment issue detected (later confirmed as false positive)

### Tool Improvement Journey

**Initial Issue**:
- Tool generated verbose report with emojis
- Flagged `xRealloc()` function as potential issue
- Issue submitted: [htop#1858](https://github.com/htop-dev/htop/issues/1858)

**Maintainer Feedback**:
BenBE and Explorer09 provided professional feedback:
- **Report quality**: "too verbose", "lots of emoji", "reads like AI generated"
- **Technical accuracy**: Suggested using `__attribute__((malloc))` instead of hardcoding functions
- **Detection consistency**: Pointed out missing implicit cast detection

**Improvements Made**:
- Commit `b9c209d`: Implemented dynamic `__attribute__((malloc))` detection
- Commit `5a5cde9`: Added implicit cast detection for consistency
- Commit `e91e889`: Complete report format overhaul
  - Maintainer-style one-screen reports
  - Removed all emojis
  - Added evidence levels (E0/E1/E2)
  - Single language enforcement

### Lessons Learned

1. **False Positives**: The `xRealloc()` case was NOT a real issue because it internally calls `realloc()` which returns aligned memory per C standard.

2. **Tool Maturity**: Early versions had hardcoded project-specific functions. Now uses compiler-standard attributes for portability.

3. **Report Quality**: Maintainer-friendly reports require:
   - Conciseness (one screen)
   - No emojis or marketing language
   - Evidence-based reasoning
   - Professional technical writing

### Acknowledgments

Special thanks to htop maintainers:
- **BenBE** - Professional critique of report quality and format standards
- **Explorer09** - Technical suggestions for detection accuracy

Their feedback significantly improved this tool. See detailed response in [docs/htop_issue_reply.md](docs/htop_issue_reply.md).

**Note**: The issue was closed as a false positive. The htop project had no actual alignment issues.

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

A: MVP targets >90% precision on ERROR level. False positives still occur. Tool uses:
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

### Maintainer Feedback

This tool benefited significantly from feedback by open source maintainers:

- **BenBE** (htop) - Report quality standards and maintainer expectations
- **Explorer09** (htop) - Technical accuracy and detection methodology

Their professional feedback drove major improvements in report format and detection accuracy.

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
