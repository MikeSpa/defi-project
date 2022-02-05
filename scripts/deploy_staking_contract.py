from scripts.helpful_scripts import get_account, get_contract, CENT, get_verify_status
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
    return staking_contract, project_token


def add_allowed_tokens(staking_contract, dict_of_allowed_tokens, account):
    for token in dict_of_allowed_tokens:
        add_tx = staking_contract.addAllowedTokens(token.address, {"from": account})
        add_tx.wait(1)
        set_tx = staking_contract.setPriceFeedContract(
            token.address, dict_of_allowed_tokens[token], {"from": account}
        )
        set_tx.wait(1)


def main():
    deploy_staking_contract_and_project_token()
