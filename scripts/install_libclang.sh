#!/bin/bash
# 安装 libclang 系统库

echo "=========================================="
echo "安装 libclang 系统库"
echo "=========================================="
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "检测到操作系统: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "检测到操作系统: macOS"
else
    echo "不支持的操作系统: $OSTYPE"
    exit 1
fi

echo ""
echo "即将安装以下软件包："
echo "  - clang (C/C++ 编译器)"
echo "  - llvm (LLVM 工具链)"
echo "  - libclang-dev (libclang 开发库)"
echo ""
echo "这需要 sudo 权限..."
echo ""

# 询问是否继续
read -p "是否继续? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "安装已取消"
    exit 0
fi

# 安装
if [ "$OS" == "linux" ]; then
    echo ""
    echo "正在更新软件包列表..."
    sudo apt-get update

    echo ""
    echo "正在安装 clang、llvm 和 libclang-dev..."
    sudo apt-get install -y \
        clang \
        llvm \
        libclang-dev \
        clang-tools-extra

    echo ""
    echo "✅ 安装完成！"

    # 验证安装
    echo ""
    echo "验证安装:"
    echo "------------"
    which clang && echo "✓ clang: $(clang --version | head -1)" || echo "✗ clang 未找到"
    which llvm-config && echo "✓ llvm-config: $(llvm-config --version)" || echo "✗ llvm-config 未找到"

    # 查找 libclang
    echo ""
    echo "libclang 库位置:"
    find /usr -name "libclang*.so*" 2>/dev/null | head -3

elif [ "$OS" == "macos" ]; then
    echo ""
    echo "正在安装 llvm (包含 libclang)..."
    brew install llvm

    echo ""
    echo "✅ 安装完成！"

    # 设置环境变量提示
    echo ""
    echo "⚠️  注意：如果 libclang 未找到，可能需要设置环境变量："
    echo ""
    echo "   export LIBCLANG_PATH=\$(brew --prefix llvm)/lib"
    echo ""
fi

echo ""
echo "=========================================="
echo "下一步"
echo "=========================================="
echo ""
echo "1. 激活虚拟环境:"
echo "   source .venv/bin/activate"
echo ""
echo "2. 设置 libclang 路径（如果需要）:"
echo "   export LIBCLANG_PATH=/usr/lib/x86_64-linux-gnu/"
echo ""
echo "3. 测试完整功能:"
echo "   riscv-check tests/fixtures/alignment_cases/ -v"
echo ""
