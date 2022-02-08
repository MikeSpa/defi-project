from brownie import CompoundInteractionContract, config, network
from scripts.helpful_scripts import POINT_ONE, get_account, get_contract


def deploy_contract():
    account = get_account()
    print(account.balance())
    compound_int_con = CompoundInteractionContract.deploy({"from": account})

    print(account.balance())
    return compound_int_con


def supplyEth(compound_int_con):
    account = get_account()
    cETH = config["networks"][network.show_active()]["cETH"]

    compound_int_con.supplyEthToCompound(cETH, {"from": account, "value": POINT_ONE})
    print(account.balance())


def redeemEth(compound_int_con):
    account = get_account()
    cETH = config["networks"][network.show_active()]["cETH"]
    account.transfer(compound_int_con.address, POINT_ONE / 10)
    compound_int_con.redeemCEth(POINT_ONE, True, cETH, {"from": account})
    print(account.balance())
    compound_int_con.drainAllFundscETH(cETH)
    print(account.balance())


def main():
    compound_int_con = deploy_contract()
    supplyEth(compound_int_con)
    redeemEth(compound_int_con)
