import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that make real HTTP requests (skip with -m 'not integration')"
    )
