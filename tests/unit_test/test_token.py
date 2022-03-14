from brownie import network, config, ProjectToken, accounts, reverts, exceptions
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    CENT,
    get_account,
)
import pytest
from scripts.deploy_token import deploy_token

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


## transfer
def test_transfer():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()

    token.transfer(accounts[1], CENT, {"from": account})

    assert token.balanceOf(account.address) == 0
    assert token.balanceOf(accounts[1].address) == CENT


def test_insufficient_balance_transfer():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()

    with reverts():
        token.transfer(accounts[1], 2 * CENT, {"from": account})


def test_transfer_null_address():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()

    with reverts():
        token.transfer(
            "0x0000000000000000000000000000000000000000", 2 * CENT, {"from": account}
        )


def test_transfer_event():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    tx = token.transfer(accounts[1], CENT, {"from": account})

    assert tx.events["Transfer"].values() == [account, accounts[1], CENT]


## allowance/approve
def test_initial_allowance():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()

    assert token.allowance(account, accounts[1]) == 0


def test_approve():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    token.approve(accounts[1], 1, {"from": account})

    assert token.allowance(account, accounts[1]) == 1


def test_approve_to_zero_address():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()

    with pytest.raises(exceptions.VirtualMachineError):
        token.approve(
            "0x0000000000000000000000000000000000000000", 1, {"from": account}
        )


def test_approval_event():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    tx = token.approve(accounts[1], 1, {"from": account})

    assert tx.events["Approval"].values() == [account, accounts[1], 1]


def test_decrease_allowance():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    STARTING_ALLOWANCE = 5
    token.approve(accounts[1], STARTING_ALLOWANCE, {"from": account})

    token.decreaseAllowance(accounts[1], 4, {"from": account})

    assert token.allowance(account, accounts[1]) == STARTING_ALLOWANCE - 4


def test_increade_allowance():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    STARTING_ALLOWANCE = 5
    token.approve(accounts[1], STARTING_ALLOWANCE, {"from": account})

    token.increaseAllowance(accounts[1], 4, {"from": account})

    assert token.allowance(account, accounts[1]) == STARTING_ALLOWANCE + 4


def test_decrease_allowance_higher_than_current():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    STARTING_ALLOWANCE = 5
    token.approve(accounts[1], STARTING_ALLOWANCE, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError):
        token.decreaseAllowance(accounts[1], 2 * STARTING_ALLOWANCE, {"from": account})


## transferFrom
def test_transfer_from():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    token.approve(accounts[1], 1, {"from": account})

    token.transferFrom(account, accounts[2], 1, {"from": accounts[1]})
    assert token.balanceOf(account.address) == CENT - 1
    assert token.balanceOf(accounts[1].address) == 0
    assert token.balanceOf(accounts[2].address) == 1


def test_transfer_from_fails_if_allowance_too_low():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token = deploy_token()
    token.approve(accounts[1], 1, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError):
        token.transferFrom(account, accounts[2], 2, {"from": accounts[1]})
