#!/bin/bash
# Installation script for riscv-check

set -e

echo "=========================================="
echo "RISC-V Check Installation"
echo "=========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "Detected OS: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "Detected OS: macOS"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "Error: Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION"
echo ""

# Install system dependencies
echo "Installing system dependencies..."

if [ "$OS" == "linux" ]; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            clang \
            llvm \
            libclang-dev \
            gcc \
            g++ \
            make \
            python3 \
            python3-venv \
            python3-pip
    else
        echo "Warning: Only apt-get is supported for Linux"
        echo "Please install clang, llvm, libclang-dev manually"
    fi
elif [ "$OS" == "macos" ]; then
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew not found. Please install from https://brew.sh/"
        exit 1
    fi

    brew install llvm
fi

echo "✓ System dependencies installed"
echo ""

# Create virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$PROJECT_DIR/.venv"
fi

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
source "$PROJECT_DIR/.venv/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel > /dev/null 2>&1

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e ".[dev]" > /dev/null 2>&1

echo "✓ Python dependencies installed"
echo ""

# Run tests
echo "Running tests..."
cd "$PROJECT_DIR"
pytest tests/ -v

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment:"
echo "  source $PROJECT_DIR/.venv/bin/activate"
echo ""
echo "To run riscv-check:"
echo "  riscv-check /path/to/project"
echo ""
echo "To run the demo:"
echo "  bash scripts/demo.sh"
echo ""
