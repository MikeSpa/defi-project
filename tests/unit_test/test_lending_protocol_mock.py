from brownie import network
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    POINT_ONE,
    approve_erc20,
    get_account,
    get_contract,
)
import pytest
from scripts.deploy_aave_lending_contract import (
    deploy_aave_lending_contract,
    withdraw_aave,
    deposit_aave,
)


def test_deploy_mock():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    mock_lending = deploy_aave_lending_contract()

    weth_token = get_contract("weth_token")

    assert mock_lending.stakingBalancePerToken(weth_token) == 0


def test_deposit(amt=POINT_ONE):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    mock_lending = deploy_aave_lending_contract()

    weth_token = get_contract("weth_token")
    initial_acc_balance = weth_token.balanceOf(account)

    approve_erc20(weth_token, mock_lending, amt, account)
    deposit_aave(mock_lending, weth_token, amt, account)
    assert mock_lending.stakingBalancePerToken(weth_token) == amt
    assert weth_token.balanceOf(account) == initial_acc_balance - amt


def test_withdraw(amt=POINT_ONE):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    acc2 = get_account(index=1)
    mock_lending = deploy_aave_lending_contract()

    weth_token = get_contract("weth_token")
    initial_acc_balance = weth_token.balanceOf(account)

    # Mock already as the first deposit
    assert mock_lending.stakingBalancePerToken(weth_token) == amt

    withdraw_aave(mock_lending, weth_token, amt / 2, account)

    assert mock_lending.stakingBalancePerToken(weth_token) == amt / 2
    assert weth_token.balanceOf(account) == initial_acc_balance + amt / 2

    withdraw_aave(mock_lending, weth_token, amt / 2, account)

    assert mock_lending.stakingBalancePerToken(weth_token) == 0
    assert weth_token.balanceOf(account) == initial_acc_balance + amt
