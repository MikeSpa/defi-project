from brownie import network, accounts, config, interface
from web3 import Web3

FORKED_LOCAL_ENVIRNOMENT = ["mainnet-fork", "mainnet-fork2"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local", "hardhat"]

CENT = Web3.toWei(100, "ether")


def get_account(index=None, id=None):
    print("#get_account")
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRNOMENT
    ):
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["from_key"])


def get_weth(amount=0.1):
    print(f"#get_weth, amt={amount}")
    account = get_account()
    weth = interface.IWETH(config["networks"][network.show_active()]["weth_token"])
    deposit_tx = weth.deposit({"from": account, "value": amount * 10 ** 18})
    deposit_tx.wait(1)
    print(f"Received {amount} WETH")
    return deposit_tx


def get_eth(amount=0.1):
    print(f"#get_eth, amt={amount}")
    account = get_account()
    weth = interface.IWETH(config["networks"][network.show_active()]["weth_token"])
    withdraw_tx = weth.withdraw(amount * 10 ** 18, {"from": account})
    withdraw_tx.wait(1)
    print(f"Received {amount} ETH")
    return withdraw_tx


def approve_erc20(token_address, spender, amount, account):
    print(f"#approve_erc20, {amount} {token_address}")
    erc20 = interface.IERC20(token_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved")


def get_asset_price(price_feed_address):
    price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The price is {converted_latest_price}")
    return float(converted_latest_price)


def main():
    get_asset_price(config["networks"][network.show_active()]["dai_eth_price_feed"])
    pass
