from brownie import network
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    POINT_ONE,
    get_contract,
)
from scripts.deploy_staking_contract import deploy_staking_contract_and_project_token
from scripts.deploy_aave_lending_contract import drain_token


def test_deploy_and_stake_unstake(amount_staked=POINT_ONE / 10):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for integration testing")

    # Deploy
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    aWETH = get_contract("aWETH")

    # Get states
    initial_weth_deployer = weth_token.balanceOf(account)
    initial_aWETH_deployer = aWETH.balanceOf(account)
    initial_weth_staking_contract = weth_token.balanceOf(staking_contract)
    initial_aWETH_staking_contract = aWETH.balanceOf(staking_contract)
    initial_weth_lending_protocol_contract = weth_token.balanceOf(lending_protocol)
    initial_aWETH_lending_protocol_contract = aWETH.balanceOf(lending_protocol)

    # Stake: deployer stake some weth
    ## -> StakingC transfer to AaveLending
    ## AaveLending deposit to Aave lending pool and feceive aWETH
    weth_token.approve(staking_contract.address, amount_staked, {"from": account})
    staking_contract.stakeTokens(amount_staked, weth_token.address, {"from": account})

    # StakingContract data is correct
    assert staking_contract.stakingBalance(weth_token.address, account) == amount_staked
    assert staking_contract.uniqueTokensStaked(account.address) == 1
    assert staking_contract.stakers(0) == account.address

    # Assets where they should be
    assert weth_token.balanceOf(account) == initial_weth_deployer - amount_staked
    assert weth_token.balanceOf(staking_contract) == 0
    assert weth_token.balanceOf(lending_protocol) == 0
    assert aWETH.balanceOf(lending_protocol) > 0

    # Unstake: deployer withdraw its weth
    ## weth: Aave pool -> AaveLending -> Stacking -> deployer
    ## aWETH: AaveLending -> ZERO, some stay on AaveLending
    staking_contract.unstakeTokens(weth_token.address, {"from": account})

    # StakingContract data is correct
    assert staking_contract.stakingBalance(weth_token.address, account) == 0
    assert staking_contract.uniqueTokensStaked(account.address) == 0

    # Assets where they should be
    assert weth_token.balanceOf(account) == initial_weth_deployer
    assert weth_token.balanceOf(staking_contract) == 0
    assert weth_token.balanceOf(lending_protocol) == 0
    assert aWETH.balanceOf(lending_protocol) > 0

    # DrainToken: deployer drain interest aWETH from AaveLending
    drain_token(lending_protocol, aWETH, account)

    # Assets where they should be
    assert weth_token.balanceOf(account) == initial_weth_deployer
    assert weth_token.balanceOf(staking_contract) == 0
    assert weth_token.balanceOf(lending_protocol) == 0
    assert aWETH.balanceOf(lending_protocol) == 0
    assert aWETH.balanceOf(account) > initial_aWETH_deployer
