import sys
import os

import pytest

# Add project root to path so tests can import app, db, etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that make real HTTP requests (skip with -m 'not integration')"
    )
