# Windows Installation Guide

## Platform Support

| Platform | Support Status | Notes |
|----------|---------------|-------|
| Linux | ✅ Fully Supported | Primary development platform |
| macOS | ✅ Fully Supported | Tested and verified |
| Windows + WSL 2 | ✅ Recommended | Best Windows experience |
| Windows Native | ⚠️ Experimental | Complex setup, not recommended |

---

## Windows Users

### Recommended: Use WSL 2 (⭐⭐⭐⭐⭐)

**WSL 2 provides a complete Linux environment and is the best choice for Windows users.**

#### Why WSL 2?

- ✅ **Full Linux compatibility**: All features work perfectly
- ✅ **Easy installation**: One command to set up
- ✅ **Excellent performance**: Near-native speed
- ✅ **Seamless integration**: Access Windows files from `/mnt/c/`

#### Installation Steps

**1. Install WSL 2**

Open PowerShell as Administrator and run:

```powershell
wsl --install
```

This will install WSL 2 with Ubuntu by default.

**2. Restart your computer**

**3. Install riscv-check in WSL**

```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y clang llvm libclang-dev
sudo apt install -y gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
sudo apt install -y python3 python3-pip

# Install riscv-check
pip3 install riscv-check
```

**4. Use riscv-check**

```bash
# Analyze a project in your Windows C: drive
riscv-check /mnt/c/path/to/your/project

# Example
riscv-check /mnt/c/Users/YourName/code/my-project
```

**5. Access Windows files**

WSL 2 automatically mounts Windows drives:
- `C:\` → `/mnt/c/`
- `D:\` → `/mnt/d/`
- Your home folder → `/mnt/c/Users/YourName/`

---

### Alternative: Native Windows (⚠️ Not Recommended)

**Native Windows support is theoretically possible but requires complex configuration.**

#### Limitations

- ⚠️ **Complex libclang setup**: Must manually configure paths
- ⚠️ **No cross-compilation**: `riscv64-linux-gnu-gcc` not available
- ⚠️ **Reduced functionality**: Must skip compile validation
- ⚠️ **Higher chance of issues**: Less tested

#### Installation Steps (Advanced Users Only)

**1. Install LLVM**

Download and install LLVM from: https://llvm.org/builds/

- Choose the "Pre-built binaries" for Windows
- Install to default location (e.g., `C:\Program Files\LLVM`)

**2. Install Python**

- Download Python 3.10+ from https://www.python.org/
- During installation, check "Add Python to PATH"

**3. Find libclang.dll**

Locate your libclang.dll path (examples):
```
C:\Program Files\LLVM\bin\libclang.dll
C:\LLVM\bin\libclang.dll
```

**4. Set environment variable**

Add to System Environment Variables:
```
LIBCLANG_PATH=C:\Program Files\LLVM\bin\libclang.dll
```

Or set it in PowerShell:
```powershell
$env:LIBCLANG_PATH = "C:\Program Files\LLVM\bin\libclang.dll"
```

**5. Install riscv-check**

```powershell
pip install riscv-check
```

**6. Use riscv-check (with limitations)**

```powershell
# Must skip cross-compilation validation
riscv-check C:\path\to\project --no-compile
```

#### Troubleshooting

**Error: `libclang.dll not found`**

Solution: Set `LIBCLANG_PATH` environment variable correctly.

**Error: `File not found`**

Solution: Use Windows path format: `C:\path\to\project`

**Error: Cross-compiler not found**

Solution: Use `--no-compile` flag to skip validation.

---

## Comparison

| Feature | WSL 2 | Native Windows |
|---------|-------|----------------|
| **Setup difficulty** | ⭐ Easy | ⭐⭐⭐⭐⭐ Complex |
| **All features** | ✅ Yes | ⚠️ Partial |
| **Performance** | ✅ Excellent | ✅ Good |
| **Maintenance** | ✅ Low | ⚠️ High |
| **Recommendation** | ✅ **Recommended** | ⚠️ Advanced only |

---

## FAQ

**Q: Can I use riscv-check without WSL?**

A: Yes, but it requires complex manual configuration. WSL 2 is strongly recommended.

**Q: Does WSL 2 slow down analysis?**

A: No, WSL 2 has near-native performance. File I/O is very fast.

**Q: Can I analyze projects on D: drive?**

A: Yes, access via `/mnt/d/path/to/project`.

**Q: Do I need to reinstall WSL for each project?**

A: No, install once and use for all projects.

---

## Quick Start (WSL 2)

```bash
# One-time setup
wsl --install
# (restart computer)

# In WSL terminal
sudo apt update && sudo apt install -y clang llvm libclang-dev python3-pip
pip3 install riscv-check

# Analyze a Windows project
riscv-check /mnt/c/Users/YourName/code/project
```

---

**Need help?** Open an issue on [GitHub](https://github.com/huziwoaini221/riscv-check/issues)
