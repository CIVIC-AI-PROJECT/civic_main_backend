"""Basic test to verify the test setup is working."""
import sys


def test_python_version():
    """Verify Python 3.11 is being used."""
    assert sys.version_info >= (3, 11), "Python 3.11 or higher is required"


def test_imports():
    """Verify required packages can be imported."""
    try:
        import boto3
        import jsonschema
        import hypothesis
        import pytest
        assert True
    except ImportError as e:
        assert False, f"Failed to import required package: {e}"
