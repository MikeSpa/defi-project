from brownie import network, AaveLending
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    CENT,
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


def test_aave_lending_contract(amt=POINT_ONE):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for integration testing")

    account = get_account()
    # Deploy
    aave_lending_contract = deploy_aave_lending_contract()
    weth_token = get_contract("weth_token")
    aweth_token = get_contract("aWETH")
    initial_balance_user = weth_token.balanceOf(account.address)
    inital_aweth_balance_user = aweth_token.balanceOf(aave_lending_contract)
    assert aweth_token.balanceOf(aave_lending_contract) == 0

    # Deposit
    approve_erc20(weth_token, aave_lending_contract, amt, account)
    deposit_aave(aave_lending_contract, weth_token, amt, account)
    assert weth_token.balanceOf(account.address) == initial_balance_user - amt
    assert aweth_token.balanceOf(aave_lending_contract) > amt

    # Withdraw
    withdraw_aave(aave_lending_contract, weth_token, amt, account)
    assert weth_token.balanceOf(account.address) == initial_balance_user
    assert aweth_token.balanceOf(aave_lending_contract) > 0

    # Drain Funds

    aave_lending_contract.drainToken(aweth_token, {"from": account})
    assert aweth_token.balanceOf(aave_lending_contract) == 0
    assert aweth_token.balanceOf(account) > inital_aweth_balance_user
