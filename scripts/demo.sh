#!/bin/bash
# Demo script for riscv-check

set -e

echo "=========================================="
echo "RISC-V Check Demo"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/.venv"
fi

# Activate virtual environment
source "$PROJECT_DIR/.venv/bin/activate"

# Install in development mode
echo "Installing riscv-check..."
cd "$PROJECT_DIR"
pip install -e . > /dev/null 2>&1

# Run on test fixtures
echo ""
echo "Running riscv-check on alignment test cases..."
echo "-------------------------------------------"
echo ""

riscv-check "$PROJECT_DIR/tests/fixtures/alignment_cases/" --output /tmp/riscv-demo-report.md

echo ""
echo "✓ Demo complete!"
echo ""
echo "Full report saved to: /tmp/riscv-demo-report.md"
echo ""
echo "To view the report:"
echo "  cat /tmp/riscv-demo-report.md"
echo ""
