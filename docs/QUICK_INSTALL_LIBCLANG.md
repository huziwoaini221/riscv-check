# ⚡ 快速安装 libclang - 3 步完成

## 一条命令安装（推荐）

```bash
cd riscv-check && bash scripts/install_libclang.sh
```

---

## 或者手动安装（3 步）

### 步骤 1: 安装系统包

```bash
sudo apt-get update
sudo apt-get install -y clang llvm libclang-dev
```

### 步骤 2: 设置环境变量（如果需要）

```bash
export LIBCLANG_PATH=/usr/lib/x86_64-linux-gnu/
```

### 步骤 3: 测试

```bash
cd riscv-check
source .venv/bin/activate
riscv-check tests/fixtures/arch_cases/ -v
```

**预期输出**: 应该检测到内联汇编和架构宏问题

---

## ✅ 验证安装成功

```bash
# 1. 检查 clang
which clang
# 输出: /usr/bin/clang

# 2. 检查 Python 绑定
python3 -c "from clang.cindex import Index; print('✓ OK')"
# 输出: ✓ OK

# 3. 运行测试
riscv-check tests/fixtures/alignment_cases/
# 应该检测到指针转换问题
```

---

## 🔍 找不到 libclang？

查看详细指南：`docs/INSTALL_LIBCLANG.md`

常见位置：
- `/usr/lib/x86_64-linux-gnu/libclang-14.so.1`
- `/usr/lib/llvm-14/lib/libclang.so`
- `$(brew --prefix llvm)/lib/libclang.so` (macOS)

---

**完成后回来告诉我！** 🚀
