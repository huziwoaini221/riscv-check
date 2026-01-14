"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_c_file(temp_dir: Path) -> Path:
    """Create a sample C file.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to sample C file
    """
    file_path = temp_dir / "test.c"
    file_path.write_text(
        """
#include <stdio.h>
#include <stdlib.h>

void test_normal() {
    int *p = malloc(sizeof(int));
    *p = 42;
    free(p);
}

void test_bad_cast() {
    char *buffer = malloc(10);
    buffer++;
    int *i = (int*)buffer;  /* ERROR: misaligned cast */
    *i = 42;
    free(buffer);
}

void test_asm() {
    __asm__ volatile("nop");  /* ERROR: inline asm */
}
"""
    )
    return file_path


@pytest.fixture
def sample_compile_db(temp_dir: Path) -> Path:
    """Create a sample compile_commands.json.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to compile_commands.json
    """
    db_path = temp_dir / "compile_commands.json"
    db_path.write_text(
        json.dumps(
            [
                {
                    "directory": str(temp_dir),
                    "command": f"gcc -c {temp_dir}/test.c -I/usr/include",
                    "file": str(temp_dir / "test.c"),
                }
            ]
        )
    )
    return db_path


@pytest.fixture
def packed_struct_file(temp_dir: Path) -> Path:
    """Create a file with packed struct example.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to packed struct file
    """
    file_path = temp_dir / "packed_test.c"
    file_path.write_text(
        """
#include <stdlib.h>

struct __attribute__((packed)) Packet {
    char type;
    int value;  /* Misaligned field */
};

int get_value(struct Packet *p) {
    return p->value;  /* ERROR: packed struct access */
}

void safe_access(struct Packet *p) {
    char c = p->type;  /* OK: char access */
}
"""
    )
    return file_path
