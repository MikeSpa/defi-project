from scripts.helpful_scripts import (
    get_account,
    get_contract,
    CENT,
    POINT_ONE,
    get_verify_status,
    get_weth,
)
from brownie import ProjectToken, StakingContract, config, network


def deploy_staking_contract_and_project_token():
    account = get_account()
    project_token = ProjectToken.deploy(
        {"from": account},
        publish_source=get_verify_status(),
    )
    staking_contract = StakingContract.deploy(
        project_token.address,
        {"from": account},
        publish_source=get_verify_status(),
    )
    tx = project_token.transfer(
        staking_contract.address, project_token.totalSupply() - CENT, {"from": account}
    )
    tx.wait(1)
    weth_token = get_contract("weth_token")
    dict_of_allowed_tokens = {
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, dict_of_allowed_tokens, account)
    return staking_contract, project_token, weth_token


def add_allowed_tokens(staking_contract, dict_of_allowed_tokens, account):
    for token in dict_of_allowed_tokens:
        add_tx = staking_contract.addAllowedTokens(token.address, {"from": account})
        add_tx.wait(1)
        set_tx = staking_contract.setPriceFeedContract(
            token.address, dict_of_allowed_tokens[token], {"from": account}
        )
        set_tx.wait(1)


def stake_token(staking_contract, token_address, amt, account):
    token_address.approve(staking_contract, CENT, {"from": account})
    staking_contract.stakeTokens(amt, token_address, {"from": account})


def unstake_token(staking_contract, token_address, account):
    staking_contract.unstakeTokens(token_address, {"from": account})


def deploy_and_stake(amt=POINT_ONE):
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    stake_token(staking_contract, weth_token, amt, account)
    return staking_contract, project_token, weth_token


def main():
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    weth_token_address = get_contract("weth_token")
    stake_token(staking_contract, weth_token_address, POINT_ONE, account)
    balacne = weth_token_address.balanceOf(account.address)
    print(balacne)
    balacne = weth_token_address.balanceOf(staking_contract.address)
    print(balacne)

    unstake_token(staking_contract, weth_token_address, account)

    balacne = weth_token_address.balanceOf(account.address)
    print(balacne)
    balacne = weth_token_address.balanceOf(staking_contract.address)
    print(balacne)
