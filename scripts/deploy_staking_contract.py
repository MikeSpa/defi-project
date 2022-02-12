from scripts.helpful_scripts import (
    get_account,
    get_contract,
    CENT,
    POINT_ONE,
    get_verify_status,
    get_weth,
)
from brownie import ProjectToken, StakingContract, config, network

import yaml
import json
import os
import shutil


def deploy_staking_contract_and_project_token(front_end_update=False):
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
    ## address of Mock or real ERC20 token contract
    weth_token = get_contract("weth_token")
    # {address -> pricefeed} | pricefeed = MockAggregator or real agg
    pricefeed_of_token = {
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, account)
    if front_end_update:
        update_front_end()
    return staking_contract, project_token, weth_token


def add_allowed_tokens(staking_contract, pricefeed_of_token, account):
    for token in pricefeed_of_token:
        add_tx = staking_contract.addAllowedTokens(token.address, {"from": account})
        add_tx.wait(1)
        set_tx = staking_contract.setPriceFeedContract(
            token.address, pricefeed_of_token[token], {"from": account}
        )
        set_tx.wait(1)


def stake_and_approve_token(staking_contract, token_address, amt, account):
    token_address.approve(staking_contract, amt, {"from": account})
    tx = staking_contract.stakeTokens(amt, token_address, {"from": account})
    tx.wait(1)


def unstake_token(staking_contract, token_address, account):
    tx = staking_contract.unstakeTokens(token_address, {"from": account})
    tx.wait(1)


def issue_tokens(stacking_contract, account):
    account = get_account()
    tx = stacking_contract.issueTokens({"from": account})
    tx.wait(1)


def deploy_and_stake(amt=POINT_ONE):
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    stake_and_approve_token(staking_contract, weth_token, amt, account)
    return staking_contract, project_token, weth_token


def update_front_end():
    # Send the build folder
    copy_folders_to_front_end("./build", "./front_end/src/chain-info")

    # Sending the front end our config in JSON format
    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open("./front_end/src/brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main():
    account = get_account()
    front_end_update = True
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token(front_end_update)
    # weth_token_address = get_contract("weth_token")
    # stake_and_approve_token(staking_contract, weth_token_address, POINT_ONE, account)

    # unstake_token(staking_contract, weth_token_address, account)
