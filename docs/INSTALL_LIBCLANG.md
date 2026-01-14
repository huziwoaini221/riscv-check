# 安装 libclang 并测试完整功能

## 📋 情况说明

由于系统安全限制，我无法直接使用 `sudo` 安装系统包。需要你**手动执行**以下步骤。

---

## 🚀 快速安装（推荐）

### 方法 1：使用安装脚本（最简单）

```bash
cd riscv-check
bash scripts/install_libclang.sh
```

这个脚本会：
1. 自动检测操作系统
2. 安装 clang、llvm、libclang-dev
3. 验证安装是否成功
4. 显示下一步操作

---

## 📦 手动安装

### Ubuntu/Debian/Linux Mint

```bash
# 1. 更新软件包列表
sudo apt-get update

# 2. 安装 clang、llvm 和 libclang-dev
sudo apt-get install -y \
    clang \
    llvm \
    libclang-dev \
    clang-tools-extra

# 3. 验证安装
which clang
clang --version

# 4. 查找 libclang 库
find /usr -name "libclang*.so*" 2>/dev/null
```

### macOS

```bash
# 1. 使用 Homebrew 安装 llvm
brew install llvm

# 2. 设置环境变量（如果需要）
export LIBCLANG_PATH=$(brew --prefix llvm)/lib
```

---

## ✅ 验证安装

安装完成后，运行以下命令验证：

```bash
# 1. 检查 clang
which clang
clang --version

# 2. 查找 libclang 库
find /usr -name "libclang*.so*" 2>/dev/null | head -3

# 3. 测试 Python clang 绑定
cd riscv-check
source .venv/bin/activate
python3 -c "from clang.cindex import Index; print('✓ clang 绑定工作正常')"
```

**预期输出**:
```
✓ clang 绑定工作正常
```

---

## 🧪 测试完整功能

安装 libclang 后，测试完整的分析功能：

### 1. 设置环境变量（如果 libclang 未自动找到）

```bash
# 常见位置
export LIBCLANG_PATH=/usr/lib/x86_64-linux-gnu/

# 或者
export LIBCLANG_PATH=/usr/lib/llvm-14/lib/
```

### 2. 运行详细分析

```bash
cd riscv-check
source .venv/bin/activate

# 测试架构依赖检测
riscv-check tests/fixtures/arch_cases/ -v

# 测试对齐问题检测
riscv-check tests/fixtures/alignment_cases/ -v

# 生成完整报告
riscv-check tests/fixtures/ --output /tmp/test-report.md
cat /tmp/test-report.md
```

### 预期结果

**arch_cases** 应该检测到：
- 🔴 ARCH_ASM（内联汇编）
- 🟡 ARCH_MACRO（架构宏）

**alignment_cases** 应该检测到：
- 🔴 ALIGN_PTR_CAST（危险指针转换）

---

## 🔧 如果 libclang 找不到

### 方法 1: 在代码中设置路径

编辑 `riscv_check/cli.py`，在开头添加：

```python
from clang import cindex
import os

# 设置 libclang 路径
libclang_path = "/usr/lib/x86_64-linux-gnu/libclang-14.so.1"
if os.path.exists(libclang_path):
    cindex.Config.set_library_file(libclang_path)
```

### 方法 2: 使用环境变量

```bash
export LIBCLANG_PATH=/usr/lib/x86_64-linux-gnu/
riscv-check tests/fixtures/
```

### 方法 3: 符号链接（不推荐，但有效）

```bash
sudo ln -s /usr/lib/x86_64-linux-gnu/libclang-14.so.1 /usr/lib/libclang.so
```

---

## 🎯 验证检测准确性

运行以下测试，验证检测器是否工作：

```bash
cd riscv-check
source .venv/bin/activate

# 测试内联汇编检测
riscv-check tests/fixtures/arch_cases/asm_bad.c

# 预期输出：
# 🔴 ERROR: ARCH_ASM at asm_bad.c:6

# 测试宏检测
riscv-check tests/fixtures/arch_cases/macro_bad.c

# 预期输出：
# 🟡 WARNING: ARCH_MACRO at macro_bad.c:3, 11

# 测试指针转换检测
riscv-check tests/fixtures/alignment_cases/ptr_cast_bad.c

# 预期输出：
# 🔴 ERROR: ALIGN_PTR_CAST at ptr_cast_bad.c:8, 17
```

---

## 🐛 故障排查

### 问题 1: ImportError: No module named 'clang'

**原因**: Python clang 绑定未安装

**解决**:
```bash
source .venv/bin/activate
pip install clang
```

### 问题 2: libclang.so not found

**原因**: 系统未安装 libclang

**解决**: 按照上面的步骤安装 libclang-dev

### 问题 3: 分析器不工作，但无错误

**原因**: libclang 找不到或版本不兼容

**解决**:
```bash
# 查找 libclang
find /usr -name "libclang*.so*" 2>/dev/null

# 设置环境变量
export LIBCLANG_PATH=/path/to/libclang/directory
```

---

## 📊 测试检查清单

安装 libclang 后，确认：

- [ ] `which clang` 找到 clang
- [ ] `clang --version` 显示版本
- [ ] `find /usr -name "libclang*.so*"` 找到库文件
- [ ] Python 可以 `from clang.cindex import Index`
- [ ] `riscv-check tests/fixtures/arch_cases/` 检测到问题
- [ ] `riscv-check tests/fixtures/alignment_cases/` 检测到问题

---

## 💡 无 libclang 也能用？

**可以，但功能受限**：

✅ **能用**：
- CLI 接口完整
- 文件扫描正常
- 报告生成工作
- 彩色输出美观

❌ **不能**：
- AST 解析
- 对齐问题检测
- 内联汇编检测（AST 方式）
- 准确的架构依赖检测

**建议**：至少安装 libclang 才能发挥完整功能。

---

## 🎉 安装完成后

回到之前的对话，告诉我：

```
"我已经安装了 libclang"
```

我会帮你：
1. 验证安装
2. 运行完整功能测试
3. 检查检测准确性
4. 生成测试报告

---

**准备好安装了吗？运行：**

```bash
bash scripts/install_libclang.sh
```

然后回来告诉我结果！🚀
