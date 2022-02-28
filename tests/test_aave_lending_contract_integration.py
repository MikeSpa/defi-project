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


def test_aave_lending_contract(amt=POINT_ONE / 10):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for integration testing")

    account = get_account()
    # Deploy
    aave_lending_contract = deploy_aave_lending_contract()
    weth_token = get_contract("weth_token")
    initial_balance_user = weth_token.balanceOf(account.address)

    # Deposit
    pool = aave_lending_contract.pool()
    print(pool)
    approve_erc20(weth_token, aave_lending_contract, amt, account)
    deposit_aave(aave_lending_contract, weth_token, amt, account)
    assert weth_token.balanceOf(account.address) == initial_balance_user - amt

    # Withdraw
    withdraw_aave(aave_lending_contract, weth_token, amt, account)
    assert weth_token.balanceOf(account.address) == initial_balance_user


# def main():
#     aave_lending_contract = AaveLending[-1]
#     account = get_account()
#     pool = aave_lending_contract.getPool({"from": account})
#     print(pool)
