from brownie import network
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    POINT_ONE,
)
from scripts.deploy_staking_contract import deploy_staking_contract_and_project_token


def test_deploy_and_stake_unstake(amount_staked=POINT_ONE):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for integration testing")

    # Deploy
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
    ) = deploy_staking_contract_and_project_token()

    # Stake
    weth_token.approve(staking_contract.address, amount_staked, {"from": account})
    staking_contract.stakeTokens(amount_staked, weth_token.address, {"from": account})

    assert (
        staking_contract.stakingBalance(weth_token.address, account.address)
        == amount_staked
    )
    assert staking_contract.uniqueTokensStaked(account.address) == 1
    assert staking_contract.stakers(0) == account.address

    # Unstake
    initial_balance_staker_on_contract = staking_contract.stakingBalance(
        weth_token.address, account.address
    )
    initial_balance_staker = weth_token.balanceOf(account.address)

    staking_contract.unstakeTokens(weth_token.address, {"from": account})

    assert weth_token.balanceOf(staking_contract.address) == 0
    assert initial_balance_staker_on_contract == amount_staked

    assert (
        weth_token.balanceOf(account.address) == initial_balance_staker + amount_staked
    )
    assert staking_contract.stakingBalance(weth_token.address, account.address) == 0
    assert staking_contract.uniqueTokensStaked(account.address) == 0
