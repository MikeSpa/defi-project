from scripts.helpful_scripts import (
    get_account,
    get_contract,
    get_weth,
    approve_erc20,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    FORKED_LOCAL_ENVIRNOMENT,
)
from brownie import config, network, interface, ProjectToken
from web3 import Web3


def get_factory():
    # return the address of UniswapV2Factory
    return interface.IUniswapV2Factory(
        config["networks"][network.show_active()]["UniswapV2Factory"]
    )


def get_pair(token0, token1):
    factory = get_factory()
    return factory.getPair(token0, token1)


def create_pair(token0, token1):
    # create pair token0/token1 if it doesn't exist
    # return the pair
    account = get_account()
    factory = get_factory()
    pair = get_pair(token0, token1)
    if pair == "0x0000000000000000000000000000000000000000":
        print("creating pair")
        tx = factory.createPair(token0, token1, {"from": account})
        pair = tx.return_value

    return pair


def main():
    print("## Uniswap")
    account = get_account()
    dai = get_contract("DAI")
    weth = get_contract("weth_token")
    pjtk = ProjectToken[-1]

    pair = create_pair(dai, pjtk)
    print(pair)
