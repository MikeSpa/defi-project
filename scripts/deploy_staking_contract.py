from scripts.deploy_aave_lending_contract import deploy_aave_lending_contract
from scripts.helpful_scripts import (
    get_account,
    get_contract,
    CENT,
    POINT_ONE,
    ONE,
    get_verify_status,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
from brownie import (
    ProjectToken,
    StakingContract,
    AaveLending,
)

import yaml
import json
import os
import shutil


def deploy_staking_contract_and_project_token(front_end_update=False):
    """
    Deploy the ERC20 token: ProjectToken.
    Deploy the StakingContract.
    Deploy the AaveLending contract.
    Add WETH to the list of allowed token.
    Update the front end if front_end_update=True
    """
    account = get_account()

    # Deploy ProjectToken
    project_token = ProjectToken.deploy(
        {"from": account},
        # publish_source=get_verify_status(),
        publish_source=False,
    )

    # Deploy AaveLending
    lending_protocol = deploy_aave_lending_contract()

    # Deploy StakingContract
    staking_contract = StakingContract.deploy(
        project_token.address,
        lending_protocol,
        {"from": account},
        # publish_source=get_verify_status(),
        publish_source=False,
    )
    tx = project_token.transfer(
        staking_contract.address, project_token.totalSupply() - CENT, {"from": account}
    )
    tx.wait(1)

    # Allow WETH
    ## address of Mock or real ERC20 token contract
    weth_token = get_contract("weth_token")
    ## {address -> pricefeed} | pricefeed = MockAggregator or real agg
    pricefeed_of_token = {
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, 10, account)

    # Front End
    if front_end_update:
        update_front_end()
    return staking_contract, project_token, weth_token, lending_protocol


def deploy_and_stake_weth(amt=POINT_ONE):
    """
    Deploy the ERC20 token: ProjectToken.
    Deploy the StakingContract.
    Deploy the AaveLending contract.
    Add WETH to the list of allowed token.
    Stake amt of WETH on the StakingContract.
    """
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    tx = stake_and_approve_token(staking_contract, weth_token, amt, account)
    return staking_contract, project_token, weth_token, lending_protocol, tx


### HELPER functions to interact with the contract


def add_allowed_tokens(staking_contract, pricefeed_of_token, yield_rate, account):
    """
    Add several token to the approved token list of the contract.
    """
    for token in pricefeed_of_token:
        add_tx = staking_contract.addAllowedTokens(
            token.address, pricefeed_of_token[token], yield_rate, {"from": account}
        )
    last_tx = add_tx
    return last_tx


def stake_and_approve_token(staking_contract, token_address, amt, account):
    """
    Stake a given amount of token after having approve the transfer to the staking contract.
    """
    token_address.approve(staking_contract, amt, {"from": account})
    tx = staking_contract.stakeTokens(
        amt,
        token_address,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )
    tx.wait(1)
    return tx


### FRONT END


def update_front_end():
    """
    Copy the neccessary information from the backend to the front end
    """
    # Send the build folder (e.g. address of projectToken)
    copy_folders_to_front_end("./build", "./front_end/src/chain-info")

    # Sending the front end our config in JSON format (e.g. address of dai token)
    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open("./front_end/src/brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    """
    Copy folders
    """
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


### MAIN


def main():
    account = get_account()
    # front_end_update = True
    # (
    #     staking_contract,
    #     project_token,
    #     weth_token,
    #     lending_protocol,
    # ) = deploy_staking_contract_and_project_token(front_end_update)
    dai_token = get_contract("fau_token")
    pricefeed_of_token = {
        dai_token: get_contract("dai_usd_price_feed"),
    }

    add_allowed_tokens(staking_contract, pricefeed_of_token, 0, account)
    staking_contract = StakingContract[-1]
    weth_token = get_contract("weth_token")
    stake_and_approve_token(staking_contract, weth_token, POINT_ONE / 10, account)

    # aave_lending = AaveLending[-1]
    # print(aave_lending.pool())
    # print(staking_contract.tokenIsAllowed(pjtk))
    # aave_lending.setStakingContract(staking_contract, {"from": account})
    # print(aave_lending.stakingContract())
