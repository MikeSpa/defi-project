from brownie import FlashLender, FlashBorrower
from scripts.helpful_scripts import get_contract, get_account, get_verify_status


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


def main():
    deploy_flash_lender()
