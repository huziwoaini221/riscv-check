# Quick Start Guide

This guide will help you get started with riscv-check in 5 minutes.

## Installation

### Option 1: Using pip (Recommended)

```bash
pip install riscv-check
```

### Option 2: From source

```bash
git clone https://github.com/yourusername/riscv-check.git
cd riscv-check
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## System Requirements

- Python 3.10+
- clang + libclang
- (Optional) riscv64-linux-gnu-gcc for cross-compilation validation

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y clang llvm libclang-dev
sudo apt install -y gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
```

### macOS

```bash
brew install llvm
brew install riscv-tools
```

## Basic Usage

### 1. Analyze a project

```bash
riscv-check /path/to/project
```

This will:
- Scan all C/C++ files
- Detect alignment issues
- Find architecture-specific code
- Generate a terminal report

### 2. Generate Markdown report

```bash
riscv-check /path/to/project --output report.md
```

### 3. Ignore specific rules

```bash
riscv-check /path/to/project --ignore ARCH_ASM --ignore ARCH_MACRO
```

## Example Output

```
$ riscv-check my-project/

Scanning project... [████████████████████] 100% (1247 files)

RISC-V Migration Risk Report
=============================

Project: my-project/
Files scanned: 1247
Risk Score: 58/100 ⚠️  (NOT RECOMMENDED)

Summary:
  🔴 ERROR: 15 issues
  🟡 WARN:  42 issues
  🔵 INFO:  8 issues

Critical Issues (must fix):
  1. src/network.c:128 [ERROR] ALIGN_PACKED_FIELD
     → Accessing packed struct member 'value' may cause SIGBUS

  2. src/crypto.c:256 [ERROR] ALIGN_PTR_CAST
     → Casting char* to int* without alignment guarantee

Recommendation:
  ❌ DO NOT migrate until critical ERRORs are fixed
  ℹ️  Estimated fix time: 2-3 days
```

## Understanding the Issues

### ALIGN_PTR_CAST (ERROR)

**Problem**: Casting pointer to stricter alignment

```c
char *p = get_buffer();
p++;
int *i = (int*)p;  // 💥 Will crash on RISC-V
```

**Fix**: Use memcpy or ensure alignment

```c
int value;
memcpy(&value, p, sizeof(int));
```

---

### ALIGN_PACKED_FIELD (ERROR)

**Problem**: Accessing non-char member of packed struct

```c
struct __attribute__((packed)) Packet {
    char type;
    int value;  // Misaligned
};

int x = packet->value;  // 💥 May crash on RISC-V
```

**Fix**: Use memcpy

```c
int value;
memcpy(&value, &packet->value, sizeof(int));
```

---

### ARCH_ASM (ERROR)

**Problem**: Inline assembly is not portable

```c
__asm__ volatile("mov %eax, %ebx");  // x86 only
```

**Fix**: Use C or intrinsics

```c
// Portable C code
int result = a + b;
```

---

### ARCH_MACRO (WARNING)

**Problem**: Architecture-specific conditional compilation

```c
#ifdef __x86_64__
    // x86-only code
#endif
```

**Fix**: Add RISC-V support

```c
#ifdef __x86_64__
    // x86 implementation
#elif defined(__riscv)
    // RISC-V implementation
#else
    #error "Unsupported architecture"
#endif
```

## Next Steps

1. **Read the full documentation**: [README.md](../README.md)
2. **Check example reports**: Look at `tests/fixtures/`
3. **Run tests**: `pytest tests/ -v`
4. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Troubleshooting

### "libclang not found"

Set the library path manually:

```python
from clang import cindex
cindex.Config.set_library_file("/usr/lib/x86_64-linux-gnu/libclang-14.so.1")
```

Or add to your `~/.bashrc`:

```bash
export LIBCLANG_PATH=/usr/lib/x86_64-linux-gnu/
```

### "No C/C++ files found"

Make sure:
- Project has `.c`, `.cpp`, `.cc`, `.h`, etc. files
- Files are not in ignored directories (`build/`, `dist/`, etc.)

### "High false positive rate"

This is expected for MVP. Focus on ERROR-level issues first.
Report false positives to help improve accuracy!

## Getting Help

- 📖 [Documentation](../README.md)
- 🐛 [Report bugs](https://github.com/yourusername/riscv-check/issues)
- 💡 [Feature requests](https://github.com/yourusername/riscv-check/discussions)
- 📧 Email: your.email@example.com

---

**Happy RISC-V porting! 🚀**
