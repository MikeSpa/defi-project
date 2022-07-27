from scripts.deploy_aave_lending_contract import deploy_aave_lending_contract
from scripts.helpful_scripts import (
    get_account,
    get_contract,
    CENT,
    POINT_ONE,
    get_verify_status,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
from brownie import (
    ProjectToken,
    StakingContract,
    AaveLending,
    config,
    network,
    interface,
)

import yaml
import json
import os
import shutil


def deploy_staking_contract_and_project_token(front_end_update=False):
    account = get_account()
    project_token = ProjectToken.deploy(
        {"from": account},
        # publish_source=get_verify_status(),
        publish_source=False,
    )
    lending_protocol = deploy_aave_lending_contract()
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
    ## address of Mock or real ERC20 token contract
    weth_token = get_contract("weth_token")
    # {address -> pricefeed} | pricefeed = MockAggregator or real agg
    pricefeed_of_token = {
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, account)
    if front_end_update:
        update_front_end()
    return staking_contract, project_token, weth_token, lending_protocol


def deploy_aave_lending_protocol():
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


def add_allowed_tokens(staking_contract, pricefeed_of_token, account):
    for token in pricefeed_of_token:
        add_tx = staking_contract.addAllowedTokens(
            token.address, pricefeed_of_token[token], 10, {"from": account}
        )
        add_tx.wait(1)
        # set_tx = staking_contract.setPriceFeedContract(
        #     token.address, pricefeed_of_token[token], {"from": account}
        # )
        # set_tx.wait(1)


def stake_and_approve_token(staking_contract, token_address, amt, account):
    token_address.approve(staking_contract, amt, {"from": account})
    tx = staking_contract.stakeTokens(
        amt,
        token_address,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )
    tx.wait(1)
    return tx


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
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    tx = stake_and_approve_token(staking_contract, weth_token, amt, account)
    return staking_contract, project_token, weth_token, lending_protocol, tx


def update_front_end():
    # Send the build folder (e.g. address of projectToken)
    copy_folders_to_front_end("./build", "./front_end/src/chain-info")

    # Sending the front end our config in JSON format (e.g. address of dai token)
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
    # account = get_account()
    # front_end_update = False
    # (
    #     staking_contract,
    #     project_token,
    #     weth_token,
    #     lending_protocol,
    # ) = deploy_staking_contract_and_project_token(front_end_update)
    # weth_token_address = get_contract("weth_token")
    # staking_contract = StakingContract[-1]
    # stake_and_approve_token(
    #     staking_contract, weth_token_address, POINT_ONE / 10, account
    # )

    # unstake_token(staking_contract, weth_token_address, account)

    update_front_end()
