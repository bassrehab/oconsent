import pytest
import os
from pathlib import Path

def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
    parser.addoption(
        "--eth-provider",
        action="store",
        default="http://localhost:8545",
        help="Ethereum provider URL"
    )
    parser.addoption(
        "--contract-address",
        action="store",
        default="0x0000000000000000000000000000000000000000",
        help="Deployed contract address"
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

@pytest.fixture
def test_config(request):
    """Configuration for tests"""
    return {
        'ethereum': {
            'provider_url': request.config.getoption("--eth-provider"),
            'contract_address': request.config.getoption("--contract-address"),
            'private_key': os.getenv('TEST_PRIVATE_KEY', '0x0000000000000000000000000000000000000000000000000000000000000000')
        }
    }