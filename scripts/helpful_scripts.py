from brownie import (
    network,
    accounts,
    config,
)
from web3 import Web3

FORKED_LOCAL_ENVIRNOMENT = ["mainnet-fork", "mainnet-fork2"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local", "hardhat"]


def get_account(index=None, id=None):
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
