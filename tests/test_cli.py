"""Tests for CLI module."""

from click.testing import CliRunner
from pathlib import Path


def test_cli_help():
    """Test CLI help command."""
    from riscv_check.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "RISC-V migration risk detector" in result.output


def test_cli_version():
    """Test CLI version command."""
    from riscv_check.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_cli_no_files(temp_dir: Path):
    """Test CLI with empty directory."""
    from riscv_check.cli import main

    runner = CliRunner()
    result = runner.invoke(main, [str(temp_dir)])
    assert result.exit_code == 0
