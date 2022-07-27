## Test the Event of StakingContract.sol

from brownie import network
from scripts.deploy_aave_lending_contract import deploy_aave_lending_contract
from scripts.deploy_compound_lending import deploy_compound_lending_contract
from scripts.deploy_staking_contract import (
    deploy_staking_contract_and_project_token,
    deploy_and_stake_weth,
)
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    get_account,
    get_contract,
)

import pytest
import time


# claimToken
def test_transfer_event(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    # stake WETH
    token_farm, project_token, weth_token, lending_protocol, tx = deploy_and_stake_weth(
        amount_staked
    )
    start_time = tx.timestamp
    starting_balance = project_token.balanceOf(account.address)
    time.sleep(5)
    tx = token_farm.claimToken({"from": account})
    end_time = tx.timestamp
    staking_time = end_time - start_time
    yieldRate = token_farm.tokenToYieldRate(weth_token)
    ending_balance = project_token.balanceOf(account.address)
    assert (
        ending_balance
        == starting_balance
        + amount_staked
        * INITIAL_PRICE_FEED_VALUE
        / 10 ** DECIMALS
        * staking_time
        * yieldRate
        / 1000
        / 86400
    )
    # Can claim more if time has passed
    time.sleep(1)
    assert token_farm.tokenToClaim(account) == 0
    token_farm.claimToken({"from": account})
    assert project_token.balanceOf(account.address) > ending_balance

    # Test Transfer Event
    assert len(tx.events) == 1
    assert tx.events["Transfer"]["from"] == token_farm
    assert tx.events["Transfer"]["to"] == account
    assert (
        tx.events["Transfer"]["value"]
        == amount_staked
        * INITIAL_PRICE_FEED_VALUE
        / 10 ** DECIMALS
        * staking_time
        * yieldRate
        / 1000
        / 86400
    )


def test_event_TokenAdded():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    pricefeed_of_token = get_contract("dai_usd_price_feed")
    add_tx = staking_contract.addAllowedTokens(
        project_token.address, pricefeed_of_token, 0, {"from": account}
    )
    add_tx.wait(1)
    assert add_tx.events["TokenAdded"] is not None
    assert add_tx.events["TokenAdded"]["token_address"] == project_token.address


def test_event_token_staked(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    weth_token.approve(staking_contract.address, amount_staked, {"from": account})

    stake_tx = staking_contract.stakeTokens(
        amount_staked, weth_token.address, {"from": account}
    )
    assert stake_tx.events["TokenStaked"]["token"] == weth_token
    assert stake_tx.events["TokenStaked"]["staker"] == account
    assert stake_tx.events["TokenStaked"]["amount"] == amount_staked


def test_event_unstake(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
        tx,
    ) = deploy_and_stake_weth(amount_staked)

    unstake_tx = staking_contract.unstakeTokens(weth_token.address, {"from": account})

    assert unstake_tx.events["TokenUnstaked"]["token"] == weth_token
    assert unstake_tx.events["TokenUnstaked"]["staker"] == account
    assert unstake_tx.events["TokenUnstaked"]["amount"] == amount_staked


def test_event_change_lending_protocol(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
        tx,
    ) = deploy_and_stake_weth(amount_staked)

    lending_protocol_compound = deploy_compound_lending_contract()
    initial_lending_protocol = staking_contract.lendingProtocol()
    tx = staking_contract.changeLendingProtocol(lending_protocol_compound)
    assert (
        tx.events["LendingProtocolChanged"]["newProtocol"] == lending_protocol_compound
    )
    assert (
        tx.events["LendingProtocolChanged"]["oldProtocol"] == initial_lending_protocol
    )

    lending_protocol_aave = deploy_aave_lending_contract()
    tx = staking_contract.changeLendingProtocol(lending_protocol_aave)

    assert tx.events["LendingProtocolChanged"]["newProtocol"] == lending_protocol_aave
    assert (
        tx.events["LendingProtocolChanged"]["oldProtocol"] == lending_protocol_compound
    )


def test_event_YieldRateChange():

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    pricefeed_of_token = get_contract("dai_usd_price_feed")
    tx = staking_contract.addAllowedTokens(
        project_token.address, pricefeed_of_token, 0, {"from": account}
    )
    tx.wait(1)
    assert tx.events["YieldRateChange"]["token"] == project_token.address
    assert tx.events["YieldRateChange"]["newYield"] == 0

    tx2 = staking_contract.updateYieldRate(project_token, 42)

    tx2.wait(1)
    assert tx2.events["YieldRateChange"]["token"] == project_token.address
    assert tx2.events["YieldRateChange"]["newYield"] == 42
