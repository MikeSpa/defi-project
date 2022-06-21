from brownie import network, exceptions, ZERO_ADDRESS, reverts
from scripts.deploy_aave_lending_contract import deploy_aave_lending_contract
from scripts.deploy_compound_lending import deploy_compound_lending_contract
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    get_account,
    get_contract,
    CENT,
)
import pytest
from scripts.deploy_staking_contract import (
    add_allowed_tokens,
    deploy_staking_contract_and_project_token,
    deploy_and_stake,
    stake_and_approve_token,
)


# setPriceFeedContract


def test_set_price_feed_contract_revert_on_non_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    non_owner = get_account(index=1)
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    with reverts("Ownable: caller is not the owner"):
        staking_contract.setPriceFeedContract(
            weth_token.address, non_owner.address, {"from": non_owner}
        )


def test_set_price_feed_contract():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    price_feed_address = get_contract("weth_token")
    staking_contract.setPriceFeedContract(
        weth_token.address, price_feed_address, {"from": account}
    )

    assert (
        staking_contract.tokenPriceFeedMapping(weth_token.address) == price_feed_address
    )


# issueToken
def test_issue_token(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    token_farm, project_token, weth_token, lending_protocol = deploy_and_stake(
        amount_staked
    )
    starting_balance = project_token.balanceOf(account.address)
    token_farm.issueTokens({"from": account})
    ending_balance = project_token.balanceOf(account.address)
    assert (
        ending_balance
        == starting_balance + amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS
    )


# getTokenValue
def test_get_token_value():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    assert staking_contract.getTokenValue(weth_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )
    fau_token = get_contract("fau_token")
    # token not added to contract
    with reverts(""):
        staking_contract.getTokenValue(fau_token.address)
    pricefeed_of_token = {
        fau_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, account)
    assert staking_contract.getTokenValue(fau_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )
    pricefeed_of_token = {
        project_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, account)
    assert staking_contract.getTokenValue(project_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )


## addAllowedTokens
def test_add_allowed_tokens():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    staking_contract.addAllowedTokens(project_token.address, {"from": account})

    assert staking_contract.allowedTokens(0) == weth_token.address
    assert staking_contract.allowedTokens(1) == project_token.address
    with reverts("Ownable: caller is not the owner"):
        staking_contract.addAllowedTokens(project_token.address, {"from": non_owner})


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
    add_tx = staking_contract.addAllowedTokens(project_token.address, {"from": account})
    add_tx.wait(1)
    assert add_tx.events["TokenAdded"] is not None
    assert add_tx.events["TokenAdded"]["token_address"] == project_token.address


# tokenIsAllowed
def test_token_is_allowed():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    assert staking_contract.tokenIsAllowed(weth_token.address)
    assert not staking_contract.tokenIsAllowed(project_token)
    assert not staking_contract.tokenIsAllowed(non_owner)
    staking_contract.addAllowedTokens(project_token.address, {"from": account})
    assert staking_contract.tokenIsAllowed(project_token)


# stakeTokens


def test_stake_tokens(amount_staked):
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
    staking_contract.stakeTokens(amount_staked, weth_token.address, {"from": account})

    assert (
        staking_contract.stakingBalance(weth_token.address, account.address)
        == amount_staked
    )
    assert staking_contract.uniqueTokensStaked(account.address) == 1
    assert staking_contract.stakers(0) == account.address
    # fails: token not allowed
    with reverts("StakingContract: Token is currently no allowed"):
        staking_contract.stakeTokens(
            amount_staked, project_token.address, {"from": account}
        )
    staking_contract.addAllowedTokens(project_token.address, {"from": account})
    # fails: allowance not approved to transfer
    with reverts("ERC20: transfer amount exceeds allowance"):
        staking_contract.stakeTokens(
            amount_staked, project_token.address, {"from": account}
        )

    project_token.approve(staking_contract.address, amount_staked, {"from": account})
    staking_contract.stakeTokens(
        amount_staked, project_token.address, {"from": account}
    )


def test_stake_tokens_fails_if_not_positive_amt(amount_staked):
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

    with reverts("StakingContract: Amount must be greater than 0"):
        staking_contract.stakeTokens(0, weth_token.address, {"from": account})


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


# unstakeTokens


def test_unstake_tokens(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, project_token, weth_token, lending_protocol = deploy_and_stake(
        amount_staked
    )
    initial_balance_contract = weth_token.balanceOf(
        staking_contract.address
    )  # 0 since its on aave
    initial_balance_staker_on_contract = staking_contract.stakingBalance(
        weth_token.address, account.address
    )
    initial_balance_staker = weth_token.balanceOf(account.address)

    staking_contract.unstakeTokens(weth_token.address, {"from": account})

    assert initial_balance_contract == 0
    assert (
        weth_token.balanceOf(staking_contract.address)
        == initial_balance_staker_on_contract - amount_staked
    )
    assert (
        weth_token.balanceOf(account.address) == initial_balance_staker + amount_staked
    )
    assert staking_contract.stakingBalance(weth_token.address, account.address) == 0
    assert staking_contract.uniqueTokensStaked(account.address) == 0


def test_unstake_token_fails_empty_balance():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    with reverts("StakingContract: Staking balance already 0!"):
        staking_contract.unstakeTokens(weth_token.address, {"from": account})


def test_unstake_token_multiple_stakers(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    # Accounts
    account = get_account()
    acc2 = get_account(index=1)
    non_staker = get_account(index=2)

    # Deploy
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    weth_token.transfer(acc2, 2 * amount_staked, {"from": account})
    # Stake
    stake_and_approve_token(staking_contract, weth_token, amount_staked, account)
    stake_and_approve_token(staking_contract, weth_token, 2 * amount_staked, acc2)
    initial_balance_contract = weth_token.balanceOf(staking_contract.address)
    initial_balance_staker1_on_contract = staking_contract.stakingBalance(
        weth_token.address, account.address
    )
    initial_balance_staker2_on_contract = staking_contract.stakingBalance(
        weth_token.address, acc2.address
    )
    initial_balance_staker1 = weth_token.balanceOf(account.address)
    initial_balance_staker2 = weth_token.balanceOf(acc2.address)
    initial_balance_non_staker = weth_token.balanceOf(non_staker.address)

    staking_contract.unstakeTokens(weth_token.address, {"from": acc2})

    assert weth_token.balanceOf(staking_contract.address) == 0
    assert weth_token.balanceOf(account.address) == initial_balance_staker1
    assert initial_balance_staker1_on_contract == amount_staked
    assert initial_balance_staker2_on_contract == 2 * amount_staked
    assert (
        weth_token.balanceOf(acc2.address)
        == initial_balance_staker2 + 2 * amount_staked
    )
    assert weth_token.balanceOf(non_staker.address) == initial_balance_non_staker
    assert (
        staking_contract.stakingBalance(weth_token.address, account.address)
        == amount_staked
    )
    assert staking_contract.stakingBalance(weth_token.address, acc2.address) == 0
    assert staking_contract.uniqueTokensStaked(account.address) == 1
    assert staking_contract.uniqueTokensStaked(acc2.address) == 0


def test_event_unstake(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, project_token, weth_token, lending_protocol = deploy_and_stake(
        amount_staked
    )
    initial_balance_contract = weth_token.balanceOf(
        staking_contract.address
    )  # 0 since its on aave

    unstake_tx = staking_contract.unstakeTokens(weth_token.address, {"from": account})

    assert unstake_tx.events["TokenUnstaked"]["token"] == weth_token
    assert unstake_tx.events["TokenUnstaked"]["staker"] == account
    assert unstake_tx.events["TokenUnstaked"]["amount"] == amount_staked


# Ownable
def test_transfer_ownership():
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    owner = get_account()
    non_owner = get_account(index=1)

    with reverts("Ownable: new owner is the zero address"):
        staking_contract.transferOwnership(ZERO_ADDRESS, {"from": owner})

    staking_contract.transferOwnership(non_owner, {"from": owner})

    with reverts("Ownable: caller is not the owner"):
        staking_contract.transferOwnership(non_owner, {"from": owner})


## getUserSingleTokenValue


def test_get_user_value_no_staking(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    user_value = staking_contract.getUserSingleTokenValue(
        account.address, weth_token.address
    )
    assert user_value == 0


def test_get_user_value(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, project_token, weth_token, lending_protocol = deploy_and_stake(
        amount_staked
    )

    user_value = staking_contract.getUserSingleTokenValue(
        account.address, weth_token.address
    )
    assert user_value == amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS


## getUserTotalValue


def test_get_user_total_value_revert_if_no_stake():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    with reverts(""):
        staking_contract.getUserTotalValue(account.address)


def test_get_user_total_value_with_different_tokens(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    # deploy
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    # Add different token (weth already added)
    fau_token = get_contract("fau_token")
    pricefeed_of_token = {
        fau_token: get_contract("dai_usd_price_feed"),
        project_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, account)
    user_value_weth = staking_contract.getUserSingleTokenValue(
        account.address, weth_token.address
    )
    assert user_value_weth == 0
    # revert: No tokens staked!
    with reverts(""):
        staking_contract.getUserTotalValue(account.address)

    # Stake tokens
    stake_and_approve_token(staking_contract, weth_token, amount_staked, account)
    stake_and_approve_token(staking_contract, fau_token, amount_staked, account)
    stake_and_approve_token(staking_contract, project_token, amount_staked, account)
    # Get value
    total_value = staking_contract.getUserTotalValue(account.address)
    user_value_weth = staking_contract.getUserSingleTokenValue(
        account.address, weth_token.address
    )
    user_value_pjtk = staking_contract.getUserSingleTokenValue(
        account.address, project_token.address
    )

    user_value_dai = staking_contract.getUserSingleTokenValue(
        account.address, fau_token.address
    )

    assert user_value_weth == amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS
    assert user_value_dai == amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS
    assert user_value_pjtk == amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS

    assert total_value == user_value_weth + user_value_dai + user_value_pjtk


## changeLendingProtocol


def test_change_lending_protocol(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, project_token, weth_token, lending_protocol = deploy_and_stake(
        amount_staked
    )

    assert staking_contract.lendingProtocol() == lending_protocol

    lending_protocol_compound = deploy_compound_lending_contract()
    staking_contract.changeLendingProtocol(lending_protocol_compound)

    assert staking_contract.lendingProtocol() == lending_protocol_compound

    lending_protocol_aave = deploy_aave_lending_contract()
    staking_contract.changeLendingProtocol(lending_protocol_aave)

    assert staking_contract.lendingProtocol() == lending_protocol_aave

    with reverts("Ownable: caller is not the owner"):
        staking_contract.changeLendingProtocol(
            lending_protocol_aave, {"from": get_account(1)}
        )


def test_event_change_lending_protocol(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, project_token, weth_token, lending_protocol = deploy_and_stake(
        amount_staked
    )

    lending_protocol_compound = deploy_compound_lending_contract()
    tx = staking_contract.changeLendingProtocol(lending_protocol_compound)
    assert (
        tx.events["LendingProtocolChanged"]["newProtocol"] == lending_protocol_compound
    )

    lending_protocol_aave = deploy_aave_lending_contract()
    tx = staking_contract.changeLendingProtocol(lending_protocol_aave)

    assert tx.events["LendingProtocolChanged"]["newProtocol"] == lending_protocol_aave
