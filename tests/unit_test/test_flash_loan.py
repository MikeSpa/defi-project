from asyncio import exceptions
from brownie import exceptions
import pytest
from scripts.helpful_scripts import *
from scripts.deploy_flash_loan import *


## FlashLender
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
    fau_token = get_contract("fau_token")
    flash_fee = flash_lender.flashFee(weth_token, CENT)

    assert flash_fee == CENT * fee / 10000
    with pytest.raises(exceptions.VirtualMachineError):
        flash_lender.flashFee(fau_token, CENT)


# maxFlashLoan
def test_max_flash_loan_zero_if_no_balance():
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    weth_token = get_contract("weth_token")
    assert flash_lender.maxFlashLoan(weth_token) == 0


def test_max_flash_loan_zero_if_unsupported_token():
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    fau_token = get_contract("fau_token")
    assert flash_lender.maxFlashLoan(fau_token) == 0


def test_max_flash_loan_with_balance():
    account = get_account()
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    weth_token = get_contract("weth_token")
    weth_token.transfer(flash_lender.address, CENT)
    assert flash_lender.maxFlashLoan(weth_token) == CENT


## FlashBorrower

# constructor
def test_borrower_constructor():
    flash_lender = deploy_flash_lender(fee=1000)
    flash_borrower = deploy_flash_borrower(flash_lender)


def test_flash_borrow(fee=1000):
    account = get_account()
    weth_token = get_contract("weth_token")
    flash_lender = deploy_flash_lender(fee=fee)
    flash_borrower = deploy_flash_borrower(flash_lender)
    weth_token.transfer(flash_lender.address, CENT)
    weth_token.transfer(flash_borrower, CENT)

    pre_acc_bal = weth_token.balanceOf(account)
    pre_len_bal = weth_token.balanceOf(flash_lender)
    pre_bor_bal = weth_token.balanceOf(flash_borrower)

    amt = flash_lender.maxFlashLoan(weth_token)
    make_flash_loan(flash_borrower, weth_token, amt, account)
    post_acc_bal = weth_token.balanceOf(account)
    post_len_bal = weth_token.balanceOf(flash_lender)
    post_bor_bal = weth_token.balanceOf(flash_borrower)

    assert post_acc_bal == pre_acc_bal
    assert post_len_bal == pre_len_bal + CENT * fee / 10000
    assert post_bor_bal == pre_bor_bal - CENT * fee / 10000


def test_flash_borrow_amount_zero():
    account = get_account()
    weth_token = get_contract("weth_token")
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    flash_borrower = deploy_flash_borrower(flash_lender)
    weth_token.transfer(flash_lender.address, CENT)
    weth_token.transfer(flash_borrower, CENT)

    pre_acc_bal = weth_token.balanceOf(account)
    pre_len_bal = weth_token.balanceOf(flash_lender)
    pre_bor_bal = weth_token.balanceOf(flash_borrower)

    make_flash_loan(flash_borrower, weth_token, 0, account)
    post_acc_bal = weth_token.balanceOf(account)
    post_len_bal = weth_token.balanceOf(flash_lender)
    post_bor_bal = weth_token.balanceOf(flash_borrower)

    assert post_acc_bal == pre_acc_bal
    assert post_len_bal == pre_len_bal
    assert post_bor_bal == pre_bor_bal


def test_flash_borrow_no_fee():
    account = get_account()
    weth_token = get_contract("weth_token")
    fee = 0
    flash_lender = deploy_flash_lender(fee=fee)
    flash_borrower = deploy_flash_borrower(flash_lender)
    weth_token.transfer(flash_lender.address, CENT)
    weth_token.transfer(flash_borrower, CENT)

    pre_acc_bal = weth_token.balanceOf(account)
    pre_len_bal = weth_token.balanceOf(flash_lender)
    pre_bor_bal = weth_token.balanceOf(flash_borrower)

    amt = flash_lender.maxFlashLoan(weth_token)
    make_flash_loan(flash_borrower, weth_token, amt, account)
    post_acc_bal = weth_token.balanceOf(account)
    post_len_bal = weth_token.balanceOf(flash_lender)
    post_bor_bal = weth_token.balanceOf(flash_borrower)

    assert post_acc_bal == pre_acc_bal
    assert post_len_bal == pre_len_bal
    assert post_bor_bal == pre_bor_bal


def test_flash_borrow_a_lot():
    # borrow ten times with a ten percent fee and a balance == amt borrowed
    account = get_account()
    weth_token = get_contract("weth_token")
    fee = 1000
    flash_lender = deploy_flash_lender(fee=fee)
    flash_borrower = deploy_flash_borrower(flash_lender)
    weth_token.transfer(flash_lender.address, CENT)
    weth_token.transfer(flash_borrower, CENT)

    pre_acc_bal = weth_token.balanceOf(account)
    pre_len_bal = weth_token.balanceOf(flash_lender)
    pre_bor_bal = weth_token.balanceOf(flash_borrower)

    amt = flash_lender.maxFlashLoan(weth_token)
    for i in range(1, 11):
        make_flash_loan(flash_borrower, weth_token, amt, account)
        post_acc_bal = weth_token.balanceOf(account)
        post_len_bal = weth_token.balanceOf(flash_lender)
        post_bor_bal = weth_token.balanceOf(flash_borrower)

        assert post_len_bal == pre_len_bal + i * (amt / 10)
        assert post_bor_bal == pre_bor_bal - i * (amt / 10)

    assert post_acc_bal == pre_acc_bal
    assert post_len_bal == pre_len_bal + pre_bor_bal
    assert post_bor_bal == 0


def test_flash_borrow_revert_amount_exceeds_balance():
    account = get_account()
    weth_token = get_contract("weth_token")
    flash_lender = deploy_flash_lender()
    flash_borrower = deploy_flash_borrower(flash_lender)

    assert flash_lender.maxFlashLoan(weth_token) == 0
    with pytest.raises(exceptions.VirtualMachineError):
        make_flash_loan(flash_borrower, weth_token, 1, account)


def test_flash_borrow_revert_unsupported_currency():
    account = get_account()
    fau_token = get_contract("fau_token")
    flash_lender = deploy_flash_lender()
    flash_borrower = deploy_flash_borrower(flash_lender)
    fau_token.transfer(flash_lender.address, CENT)
    fau_token.transfer(flash_borrower, CENT)
    amt = flash_lender.maxFlashLoan(fau_token)

    with pytest.raises(exceptions.VirtualMachineError):
        make_flash_loan(flash_borrower, fau_token, amt, account)


def test_flash_borrow_revert_repay_failed():
    account = get_account()
    weth_token = get_contract("weth_token")
    flash_lender = deploy_flash_lender()
    flash_borrower = deploy_flash_borrower(flash_lender)
    weth_token.transfer(flash_lender.address, CENT)
    amt = flash_lender.maxFlashLoan(weth_token)

    with pytest.raises(exceptions.VirtualMachineError):
        make_flash_loan(flash_borrower, weth_token, amt, account)
