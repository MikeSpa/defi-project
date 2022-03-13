from brownie import network, StakingContract
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    POINT_ONE,
    get_contract,
    TEN,
)
from scripts.deploy_staking_contract import deploy_staking_contract_and_project_token
from scripts.deploy_aave_lending_contract import drain_token
from scripts.deploy_compound_lending import (
    deploy_compound_lending_contract,
    drain_token_compound,
)


def test_deploy_and_stake_unstake_aave_lending(amount_staked=POINT_ONE / 10):
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
    lending_protocol.setStakingContract(staking_contract, {"from": account})
    assert lending_protocol.stakingContract() == staking_contract

    # Get states
    initial_weth_deployer = weth_token.balanceOf(account)
    initial_aWETH_deployer = aWETH.balanceOf(account)

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
    staking_contract.unstakeTokens(
        weth_token.address,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )

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


def test_deploy_and_stake_unstake_compound_lending(amount_staked=TEN):
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
    # staking_contract = StakingContract[-1]
    lending_protocol = deploy_compound_lending_contract()
    lending_protocol.setStakingContract(staking_contract, {"from": account})
    assert lending_protocol.stakingContract() == staking_contract
    DAI = get_contract("DAI")
    cDAI = get_contract("cDAI")
    staking_contract.addAllowedTokens(DAI, {"from": account})
    assert staking_contract.tokenIsAllowed(DAI) == True
    staking_contract.changeLendingProtocol(lending_protocol, {"from": account})
    assert staking_contract.lendingProtocol() == lending_protocol

    # Get states
    initial_DAI_deployer = DAI.balanceOf(account)
    initial_cDAI_deployer = cDAI.balanceOf(account)

    # Stake: deployer stake some DAI
    ## -> StakingC transfer to CompoundLending
    ## CLending deposit to Compound Dai contract and receive cDAI
    DAI.approve(staking_contract.address, amount_staked, {"from": account})
    staking_contract.stakeTokens(
        amount_staked,
        DAI,
        {"from": account, "gas_limit": 1_000_000, "allow_revert": True},
    )

    # StakingContract data is correct
    assert staking_contract.stakingBalance(DAI, account) == amount_staked
    assert staking_contract.uniqueTokensStaked(account) == 1
    assert staking_contract.stakers(0) == account

    # Assets where they should be
    assert DAI.balanceOf(account) == initial_DAI_deployer - amount_staked
    assert DAI.balanceOf(staking_contract) == 0
    assert DAI.balanceOf(lending_protocol) == 0
    assert cDAI.balanceOf(lending_protocol) > 0

    # Unstake: deployer withdraw its DAI
    ## DAI: cDAI contract -> CompoundLending -> Staking -> deployer
    ## cDAI: CompoundLending -> cDAI contract, some stay on CompoundLending
    staking_contract.unstakeTokens(
        DAI, {"from": account, "gas_limit": 1_000_000, "allow_revert": True}
    )

    # StakingContract data is correct
    assert staking_contract.stakingBalance(DAI, account) == 0
    assert staking_contract.uniqueTokensStaked(account) == 0

    # Assets where they should be
    assert DAI.balanceOf(account) == initial_DAI_deployer
    assert DAI.balanceOf(staking_contract) == 0
    assert DAI.balanceOf(lending_protocol) == 0
    assert cDAI.balanceOf(lending_protocol) > 0

    # DrainToken: deployer drain interest cDAI from AaveLending
    drain_token_compound(lending_protocol, cDAI, account)

    # Assets where they should be
    assert DAI.balanceOf(account) == initial_DAI_deployer
    assert DAI.balanceOf(staking_contract) == 0
    assert DAI.balanceOf(lending_protocol) == 0
    assert cDAI.balanceOf(lending_protocol) == 0
    assert cDAI.balanceOf(account) > initial_cDAI_deployer
