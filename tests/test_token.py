from brownie import network, config, ProjectToken
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    CENT,
    get_account,
)
import pytest
from scripts.deploy import deploy_token

MM = 1_000_000_000_000_000_000_000_000


def test_issue_tokens():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()

    starting_balance_account = token.balanceOf(account.address)
    starting_balance_contract = token.balanceOf(token.address)

    assert starting_balance_contract == MM - CENT
    assert starting_balance_account == CENT
