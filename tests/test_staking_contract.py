from brownie import network, exceptions, ZERO_ADDRESS, MockDAI
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
    deploy_staking_contract_and_project_token,
    deploy_and_stake,
)


def test_set_price_feed_contract_revert_on_non_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    non_owner = get_account(index=1)
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    with pytest.raises(exceptions.VirtualMachineError):
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
    ) = deploy_staking_contract_and_project_token()
    price_feed_address = get_contract("weth_token")
    staking_contract.setPriceFeedContract(
        weth_token.address, price_feed_address, {"from": account}
    )

    assert (
        staking_contract.tokenPriceFeedMapping(weth_token.address) == price_feed_address
    )


# TODO test issue token


def test_get_token_value():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()

    assert staking_contract.getTokenValue(weth_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )


def test_add_allowed_tokens():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    staking_contract.addAllowedTokens(project_token.address, {"from": account})

    assert staking_contract.allowedTokens(0) == weth_token.address
    assert staking_contract.allowedTokens(1) == project_token.address
    with pytest.raises(exceptions.VirtualMachineError):
        staking_contract.addAllowedTokens(project_token.address, {"from": non_owner})


def test_token_is_allowed():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    assert staking_contract.tokenIsAllowed(project_token)
    assert staking_contract.tokenIsAllowed(weth_token.address)
    # assert not staking_contract.tokenIsAllowed(non_owner)


def test_stake_tokens(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
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
    with pytest.raises(exceptions.VirtualMachineError):
        staking_contract.stakeTokens(
            amount_staked, project_token.address, {"from": account}
        )
    staking_contract.addAllowedTokens(project_token.address, {"from": account})
    # fails: allowance not approved to transfer
    with pytest.raises(exceptions.VirtualMachineError):
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
    ) = deploy_staking_contract_and_project_token()
    weth_token.approve(staking_contract.address, amount_staked, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError):
        staking_contract.stakeTokens(0, weth_token.address, {"from": account})


def test_unstake_tokens(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, project_token, weth_token = deploy_and_stake(amount_staked)
    initial_balance_contract = weth_token.balanceOf(staking_contract.address)
    initial_balance_staker = weth_token.balanceOf(account.address)

    staking_contract.unstakeTokens(weth_token.address, {"from": account})

    assert (
        weth_token.balanceOf(staking_contract.address)
        == initial_balance_contract - amount_staked
    )
    assert (
        weth_token.balanceOf(account.address) == initial_balance_staker + amount_staked
    )
    assert staking_contract.stakingBalance(weth_token.address, account.address) == 0
    assert staking_contract.uniqueTokensStaked(account.address) == 0
