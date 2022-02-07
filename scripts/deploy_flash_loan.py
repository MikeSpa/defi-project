from brownie import FlashLender, FlashBorrower
from scripts.helpful_scripts import get_contract, get_account, get_verify_status, CENT


def deploy_flash_lender(fee=1000):
    account = get_account()
    weth_token = get_contract("weth_token")
    supported_token = [weth_token]
    flash_lender = FlashLender.deploy(
        supported_token,
        fee,
        {"from": account},
        publish_source=get_verify_status(),
    )
    return flash_lender


def deploy_flash_borrower(flash_lender):
    account = get_account()
    flash_borrower = FlashBorrower.deploy(flash_lender, {"from": account})
    return flash_borrower


def make_flash_loan(flash_borrower, token, amount, account):
    flash_borrower.flashBorrow(token, amount, {"from": account})


def main():
    account = get_account()
    weth_token = get_contract("weth_token")
    flash_lender = deploy_flash_lender()
    flash_borrower = deploy_flash_borrower(flash_lender)

    print("starting")
    weth_balance = weth_token.balanceOf(account)
    print(f"accWETH:\t{weth_balance}")
    print(f"lenderWETH:\t {weth_token.balanceOf(flash_lender)}")
    print(f"borrowerWETH:\t {weth_token.balanceOf(flash_borrower)}")

    print("transfer")
    weth_token.transfer(flash_lender.address, CENT)
    weth_token.transfer(flash_borrower, CENT)
    print(f"accWETH:\t {weth_balance}")
    print(f"lenderWETH:\t {weth_token.balanceOf(flash_lender)}")
    print(f"borrowerWETH:\t {weth_token.balanceOf(flash_borrower)}")
    amt = flash_lender.maxFlashLoan(weth_token)

    print(f"maxflashloan:\t {amt}")

    make_flash_loan(flash_borrower, weth_token, amt, account)

    print("after")
    print(f"accWETH:\t {weth_balance}")
    print(f"lenderWETH:\t {weth_token.balanceOf(flash_lender)}")
    print(f"borrowerWETH:\t {weth_token.balanceOf(flash_borrower)}")
