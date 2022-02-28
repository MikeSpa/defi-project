from scripts.helpful_scripts import (
    get_account,
    get_contract,
    approve_erc20,
    CENT,
    POINT_ONE,
    get_verify_status,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
from brownie import (
    AaveLending,
    config,
    network,
    interface,
)


def deploy_aave_lending_contract():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        aave_lending_protocol = get_contract("lending_pool")
        return aave_lending_protocol
    account = get_account()
    aave_lending_protocol = AaveLending.deploy(
        get_aave_lending_pool(),
        {"from": account},
        # publish_source=get_verify_status(),
        publish_source=False,
    )
    return aave_lending_protocol


def get_aave_lending_pool():
    # return the address of the aave lending pool
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        lending_pool = get_contract("lending_pool")
    else:
        lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
            config["networks"][network.show_active()]["lending_pool_addresses_provider"]
        )
        lending_pool_address = lending_pool_addresses_provider.getLendingPool()
        lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def deposit_aave(aave_lending_contract, token, amt, account):

    aave_lending_contract.deposit(
        token,
        amt,
        account.address,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )


def withdraw_aave(aave_lending_contract, token, amt, account):
    aave_lending_contract.withdraw(token, amt, account, {"from": account})


def drain_token(aave_lending_contract, token, account):
    aave_lending_contract.drainToken(token, {"from": account})


def main():
    account = get_account()
    aave_lending_contract = deploy_aave_lending_contract()
    weth_token = get_contract("weth_token")
    aWETH = get_contract("aWETH")
    approve_erc20(weth_token, aave_lending_contract, POINT_ONE, account)
    deposit_aave(aave_lending_contract, weth_token, POINT_ONE, account)
    withdraw_aave(aave_lending_contract, weth_token, POINT_ONE, account)
    drain_token(aave_lending_contract, aWETH, account)
