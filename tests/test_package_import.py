"""Smoke tests for the installable package."""

from importlib.metadata import version

import credit_risk_platform


def test_package_import_and_version() -> None:
    """The package imports and exposes its configured distribution version."""
    assert credit_risk_platform.__version__ == "0.1.0"
    assert credit_risk_platform.__version__ == version("corporate-credit-risk-platform")
