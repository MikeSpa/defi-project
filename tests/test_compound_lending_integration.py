from brownie import network
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    CENT,
    POINT_ONE,
    TEN,
    approve_erc20,
    get_account,
    get_contract,
)
import pytest
from scripts.deploy_compound_lending import (
    deploy_compound_lending_contract,
    withdraw_compound,
    deposit_compound,
    drain_token_compound,
)


def test_compound_lending_contract(amt=TEN):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for integration testing")

    account = get_account()
    # Deploy
    compound_lending = deploy_compound_lending_contract()
    DAI = get_contract("DAI")
    cDAI = get_contract("cDAI")
    initial_DAI_balance_user = DAI.balanceOf(account)
    inital_cDAI_balance_user = cDAI.balanceOf(compound_lending)
    assert DAI.balanceOf(compound_lending) == 0
    assert cDAI.balanceOf(compound_lending) == 0

    # Deposit
    approve_erc20(DAI, compound_lending, amt, account)
    deposit_compound(compound_lending, DAI, amt, account)
    assert DAI.balanceOf(account) == initial_DAI_balance_user - amt
    assert cDAI.balanceOf(compound_lending) > 0

    # Withdraw
    withdraw_compound(compound_lending, DAI, amt, account)
    assert DAI.balanceOf(account) == initial_DAI_balance_user
    assert DAI.balanceOf(compound_lending) == 0
    assert cDAI.balanceOf(compound_lending) > 0

    # Drain Funds

    drain_token_compound(compound_lending, cDAI, account)
    assert cDAI.balanceOf(compound_lending) == 0
    assert cDAI.balanceOf(account) > inital_cDAI_balance_user
