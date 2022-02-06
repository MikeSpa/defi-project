from scripts.helpful_scripts import get_account
import pytest
from web3 import Web3
from scripts.helpful_scripts import get_account


@pytest.fixture
def amount_staked():
    return Web3.toWei(1, "ether")
