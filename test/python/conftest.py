"""Pytest configuration for Python property-based tests."""


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "pbt: property-based test marker"
    )
