from asyncio import exceptions
from brownie import exceptions
import pytest
from scripts.helpful_scripts import *
from scripts.deploy_flash_loan import *

# constructor
def test_constructor():
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)

    assert flash_lender.supportedTokens(get_contract("weth_token"))
    assert flash_lender.fee() == fee


# flashFee
def test_flash_fee():
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    weth_token = get_contract("weth_token")
    dai_token = get_contract("dai_token")
    flash_fee = flash_lender.flashFee(weth_token, CENT)

    assert flash_fee == CENT * fee / 10000
    with pytest.raises(exceptions.VirtualMachineError):
        flash_lender.flashFee(dai_token, CENT)


# maxFlashLoan
def test_max_flash_loan_zero_if_no_balance():
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    weth_token = get_contract("weth_token")
    assert flash_lender.maxFlashLoan(weth_token) == 0


def test_max_flash_loan_zero_if_unsupported_token():
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    dai_token = get_contract("dai_token")
    assert flash_lender.maxFlashLoan(dai_token) == 0


def test_max_flash_loan_with_balance():
    account = get_account()
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    weth_token = get_contract("weth_token")
    weth_token.transfer(flash_lender.address, CENT)
    assert flash_lender.maxFlashLoan(weth_token) == CENT
