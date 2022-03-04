from scripts.helpful_scripts import (
    get_account,
    get_contract,
    get_weth,
    approve_erc20,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    FORKED_LOCAL_ENVIRNOMENT,
    TEN,
)
from brownie import config, network, interface, ProjectToken
from web3 import Web3

DAI_PJTK_PAIR = "0xA4f3f3D34Bd9AEB1901ade030CBCA978878dbE8e"


def get_factory():
    # return the address of UniswapV2Factory
    return interface.IUniswapV2Factory(
        config["networks"][network.show_active()]["UniswapV2Factory"]
    )


def get_router():
    # return the address of UniswapV2Factory
    return interface.IUniswapV2Router02(
        config["networks"][network.show_active()]["UniswapV2Router02"]
    )


def get_pair_x():
    return interface.IUniswapV2Pair(DAI_PJTK_PAIR)


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


def add_liquidity(
    tokenA,
    tokenB,
    amount_a_desired,
    amount_b_desired,
    amount_a_min=None,
    amount_b_min=None,
    to=get_account(),
):
    account = get_account()
    router = get_router()
    if not amount_a_min:
        amount_a_min = amount_a_desired * 99 / 100
    if not amount_b_min:
        amount_b_min = amount_b_desired * 99 / 100

    approve_erc20(tokenA, router, amount_a_desired, account)
    erc20 = interface.IERC20(tokenB)
    tx = erc20.approve(router, amount_b_desired, {"from": account})
    timestamp = tx.timestamp
    print(timestamp)
    pair = get_pair_x()
    resA, resB, _ = pair.getReserves()
    print(f"reservesA: {resA}")
    print(f"reservesB: {resB}")

    tx = router.addLiquidity(
        tokenA,
        tokenB,
        amount_a_desired,
        amount_b_desired,
        amount_a_min,
        amount_b_min,
        account,
        timestamp + 100,
        # 2 ** 255,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )
    print(tx)

    resA, resB, _ = pair.getReserves()
    print(f"reservesA: {resA}")
    print(f"reservesB: {resB}")


def main():
    print("## Uniswap")
    account = get_account()
    dai = get_contract("DAI")
    weth = get_contract("weth_token")
    pjtk = ProjectToken[-1]

    # pair = create_pair(dai, pjtk)
    # print(pair)

    a, b, l = add_liquidity(dai, pjtk, TEN, TEN)
