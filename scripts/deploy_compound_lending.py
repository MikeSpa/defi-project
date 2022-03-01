from scripts.helpful_scripts import (
    TEN,
    get_account,
    get_contract,
    approve_erc20,
    CENT,
    POINT_ONE,
    get_verify_status,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
from brownie import (
    CompoundLending,
    config,
    network,
    interface,
)


def deploy_compound_lending_contract():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        compound_lending = get_contract("compound_lending")
        return compound_lending
    account = get_account()
    DAI = get_contract("DAI")
    cDAI = get_contract("cDAI")
    compound_lending = CompoundLending.deploy(
        DAI,
        cDAI,
        {"from": account},
        # publish_source=get_verify_status(),
        publish_source=False,
    )
    return compound_lending


def deposit_compound(compound_lending, token, amt, account):

    compound_lending.deposit(
        token,
        amt,
        account,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )


def withdraw_compound(compound_lending, token, amt, account):
    compound_lending.withdraw(
        token,
        amt,
        account,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
        # otherwise fails with out-of-gas
        # 0x52210db57a34303cd099d2ecd9ca63c4a1507e7051f6a315a124babc76425c1b
    )


def drain_token_compound(compound_lending, token, account):
    compound_lending.drainToken(token, {"from": account})


def main():
    account = get_account()
    # compound_lending = deploy_compound_lending_contract()
    DAI = get_contract("DAI")
    cDAI = get_contract("cDAI")
    amt = TEN
    compound_lending = CompoundLending[-1]
    # approve_erc20(DAI, compound_lending, amt, account)
    # deposit_compound(compound_lending, DAI, amt, account)
    # withdraw_compound(compound_lending, DAI, amt, account)
    drain_token_compound(compound_lending, DAI, account)
