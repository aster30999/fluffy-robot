"""
Simple tests for Solana Trading Bot CI/CD
"""

import sys


def test_python_version():
    """Test that we're using a supported Python version."""
    assert sys.version_info >= (3, 10), f"Requires Python 3.10+, got {sys.version}"


def test_basic_math():
    """Basic math test."""
    assert 1 + 1 == 2
    assert 2 * 2 == 4
    assert 10 / 2 == 5


def test_string_operations():
    """Test basic string operations."""
    assert "hello" + " world" == "hello world"
    assert len("test") == 4


def test_list_operations():
    """Test basic list operations."""
    lst = [1, 2, 3]
    assert len(lst) == 3
    assert lst[0] == 1
    assert lst[-1] == 3


if __name__ == "__main__":
    print("Running simple tests...")
    test_python_version()
    test_basic_math()
    test_string_operations()
    test_list_operations()
    print("All tests passed!")