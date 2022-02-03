from scripts.helpful_scripts import (
    get_account,
    get_weth,
    approve_erc20,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    FORKED_LOCAL_ENVIRNOMENT,
)
from brownie import config, network, interface
from web3 import Web3

AMOUNT = Web3.toWei(0.1, "ether")


def get_lending_pool():
    # return the address of the lending pool
    print("get_lending_pool")
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def deposit(lending_pool, token, amount, account):
    print("#deposit")
    deposit_tx = lending_pool.deposit(
        token, amount, account.address, 0, {"from": account}
    )
    deposit_tx.wait(1)
    print("Deposited")


def withdraw(lending_pool, token, amount, account):
    print("#withdraw")
    withdraw_tx = lending_pool.withdraw(
        token, amount, account.address, {"from": account}
    )
    withdraw_tx.wait(1)
    print("Withdrawed")


def main():
    print("## deposit_to_aave")
    account = get_account()
    weth_address = config["networks"][network.show_active()]["weth_token"]
    get_weth()

    lending_pool = get_lending_pool()
    approve_erc20(weth_address, lending_pool.address, AMOUNT, account)
    print("Depositing...")
    deposit(lending_pool, weth_address, AMOUNT, account)
    print("Withdrawing...")
    withdraw(lending_pool, weth_address, AMOUNT, account)
