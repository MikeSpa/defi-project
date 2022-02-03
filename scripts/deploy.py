from scripts.helpful_scripts import get_account
from brownie import ProjectToken, network, config
from web3 import Web3

CENT = Web3.toWei(100, "ether")


def deploy_token():
    print(network.show_active())
    account = get_account()
    token = ProjectToken.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    tx = token.transfer(token.address, token.totalSupply(), {"from": account})
    tx.wait(1)
    return token


def main():
    deploy_token()
