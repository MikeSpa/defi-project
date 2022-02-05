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
    add_allowed_tokens,
    deploy_staking_contract_and_project_token,
    deploy_and_stake,
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

# getTokenValue
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


# addAllowedTokens
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
    ) = deploy_staking_contract_and_project_token()
    assert staking_contract.tokenIsAllowed(project_token)
    assert staking_contract.tokenIsAllowed(weth_token.address)
    # assert not staking_contract.tokenIsAllowed(non_owner)


# stakeTokens


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


# unstakeTokens


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


def test_unstake_token_empty_balance():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    with pytest.raises(exceptions.VirtualMachineError):

        staking_contract.unstakeTokens(weth_token.address, {"from": account})


# Ownable
def test_transfer_ownership():
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()
    owner = get_account()
    non_owner = get_account(index=1)

    with pytest.raises(exceptions.VirtualMachineError):
        staking_contract.transferOwnership(ZERO_ADDRESS, {"from": owner})

    staking_contract.transferOwnership(non_owner, {"from": owner})

    with pytest.raises(exceptions.VirtualMachineError):
        staking_contract.transferOwnership(non_owner, {"from": owner})


## getUserSingleTokenValue


def test_get_user_value_no_staking(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        dapp_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()

    user_value = staking_contract.getUserSingleTokenValue(
        account.address, weth_token.address
    )
    assert user_value == 0


def test_get_user_value(amount_staked):
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_contract, dapp_token, weth_token = deploy_and_stake(amount_staked)

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
        dapp_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()

    with pytest.raises(exceptions.VirtualMachineError):
        staking_contract.getUserTotalValue(account.address)


# def test_get_user_total_value_with_different_tokens(amount_staked):
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account()
#     (
#         staking_contract,
#         dapp_token,
#         weth_token,
#     ) = deploy_staking_contract_and_project_token()
#     mock_dai_token = get_contract("dai_usd_price_feed")
#     dict_of_allowed_tokens = {
#         weth_token: get_contract("eth_usd_price_feed"),
#         mock_dai_token: get_contract("dai_usd_price_feed"),
#     }
#     add_allowed_tokens(staking_contract, dict_of_allowed_tokens, account)
#     print("dai toekn")
#     print(mock_dai_token)
#     print(get_contract("dai_usd_price_feed"))
#     mock_dai_token.approve(staking_contract.address, amount_staked, {"from": account})
#     staking_contract.stakeTokens(
#         amount_staked, mock_dai_token.address, {"from": account}
#     )
#     user_value_weth = staking_contract.getUserSingleTokenValue(
#         account.address, weth_token.address
#     )

#     user_value_dai = staking_contract.getUserSingleTokenValue(
#         account.address, mock_dai_token.address
#     )

#     assert user_value_weth == amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS
#     assert user_value_dai == amount_staked * INITIAL_PRICE_FEED_VALUE / 10 ** DECIMALS
#     total_value = staking_contract.getUserTotalValue(account.address)
#     assert total_value == amount_staked
