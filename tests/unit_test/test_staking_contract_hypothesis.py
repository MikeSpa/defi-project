import brownie
from brownie import network, chain
from scripts.deploy_staking_contract import (
    deploy_staking_contract_and_project_token,
    add_allowed_tokens,
    stake_and_approve_token,
)

# from scripts.deploy_aave_lending_contract import deploy_aave_lending_contract
# from scripts.deploy_compound_lending import deploy_compound_lending_contract
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    POINT_ONE,
    get_account,
    get_contract,
    CENT,
    ONE,
    distribute_token,
    # cal_yield,
    print_balance,
)
import pytest
from brownie.test import given, strategy
from hypothesis import settings

# import time
import math

WETH_INITIAL_YIELDRATE = 10  # 1%
PJTK_INITIAL_YIELDRATE = 0  # 0%
DAI_INITIAL_YIELDRATE = 35  # 3.5%


def cal_yield(amount, time, yield_rate):
    return math.floor(
        (
            amount
            * INITIAL_PRICE_FEED_VALUE
            / 10 ** DECIMALS
            * time
            * yield_rate
            / 1000
            / 86400
        )
    )


@brownie.test.given(
    _weth_new_yield=strategy("uint256", max_value=5000),  # 500%
    _dai_new_yield=strategy("uint256", max_value=5000),
    # _pjtk_new_yield=strategy("uint256"),
)
@settings(max_examples=10)
def test_updateYieldRate(_weth_new_yield, _dai_new_yield):
    """
    _______________________WETH______________________________
    USER1: stake 0.1 WETH for 4 sec at yieldRate 10, unstake
    USER1: restake 0.1 WETH at 10 for 7 sec
    USER2: stake 0.1 WETH for 11 sec at yieldRate 10
    USER3: stake 0.1 WETH for 11 sec at yieldRate 10
    USER3: stake add. 0.1 WETH for 7 sec at yieldRate 10

    11: YieldRate of WETH change to _weth_new_yield

    USER1: still 0.1 WETH staked at 20 for 10 sec, unstake
    USER2: still 0.1 WETH staked at 20 for 10 sec, unstake
    USER3: still 0.2 WETH staked at 20 for 10 sec, unstake

    _______________________DAI______________________________

    USER1: stake 500 DAI for 15 sec at yieldRate 35
    USER2: no DAI
    USER3: nothing yet

    15: YieldRate of DAI change to _dai_new_yield

    USER1: still 500 DAI staked at 45 for 6 sec, unstake
    USER2: no DAI
    USER3: staked 222 DAI at 45 for 6 sec, unstake

    _______________________PJTK______________________________

    USER2: stake 8.12 PJTK for 21 sec at yieldRate 0, unstake
    """
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    user1 = get_account(index=1)
    user2 = get_account(index=2)
    user3 = get_account(index=3)

    dai_token = get_contract("fau_token")
    pricefeed_of_token = {
        dai_token: get_contract("dai_usd_price_feed"),
        project_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(staking_contract, pricefeed_of_token, 0, account)
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )
    staking_contract.updateYieldRate(
        dai_token, DAI_INITIAL_YIELDRATE, {"from": account}
    )

    distribute_token(weth_token, 3, amt=ONE)
    distribute_token(dai_token, 3, amt=5 * CENT)
    distribute_token(project_token, 3, amt=10 * ONE)
    # print_balance([user1, user2, user3], [weth_token, project_token, dai_token])

    weth_staked = POINT_ONE
    pjtk_staked = ONE
    dai_staked = 500 * ONE

    init_tokenToClaim_1 = staking_contract.tokenToClaim(user1)
    init_tokenToClaim_2 = staking_contract.tokenToClaim(user2)
    init_tokenToClaim_3 = staking_contract.tokenToClaim(user3)
    # Initial
    assert init_tokenToClaim_1 == init_tokenToClaim_2 == init_tokenToClaim_3 == 0

    # t=0
    # User1,2,3 STAKE 0.1 WETH
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user1)
    stake_weth_1_first_timestamp = stake_tx.timestamp
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user2)
    stake_weth_2_timestamp = stake_tx.timestamp
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user3)
    stake_weth_3_timestamp = stake_tx.timestamp
    # User1 STAKE 500 DAI
    stake_tx = stake_and_approve_token(staking_contract, dai_token, dai_staked, user1)
    stake_dai_1_timestamp = stake_tx.timestamp
    # User2 STAKE 8.12 PJTK
    stake_tx = stake_and_approve_token(
        staking_contract, project_token, 8.12 * ONE, user2
    )
    stake_pjtk_2_timestamp = stake_tx.timestamp

    # User 1 unstake
    chain.sleep(10000)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user1})
    unstake_weth_1_first_timestamp = unstake_tx.timestamp
    # User1 reSTAKE 0.1 WETH for 7 sec
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user1)
    stake_weth_1_second_timestamp = stake_tx.timestamp
    # User3 STAKE additional 0.1 for 7 sec
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user3)
    stake_weth_3_second_timestamp = stake_tx.timestamp

    # WETH YieldRate change to _weth_new_yield
    chain.sleep(10000)
    update_weth_tx = staking_contract.updateYieldRate(
        weth_token, _weth_new_yield, {"from": account}
    )
    update_weth_tx_timestamp = update_weth_tx.timestamp

    # DAI YieldRate change to _dai_new_yield
    chain.sleep(10000)
    update_dai_tx = staking_contract.updateYieldRate(
        dai_token, _dai_new_yield, {"from": account}
    )
    update_dai_tx_timestamp = update_dai_tx.timestamp
    # USER3 STAKE 222 DAI
    stake_tx = stake_and_approve_token(staking_contract, dai_token, 222 * ONE, user3)
    stake_dai_3_timestamp = stake_tx.timestamp

    # User 1,2,3 unstake WETH
    chain.sleep(10000)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user1})
    unstake_weth_1_second_timestamp = unstake_tx.timestamp
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user2})
    unstake_weth_2_timestamp = unstake_tx.timestamp
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user3})
    unstake_weth_3_timestamp = unstake_tx.timestamp
    # USER1,3 unstake DAI
    unstake_tx = staking_contract.unstakeTokens(dai_token, {"from": user1})
    unstake_dai_1_timestamp = unstake_tx.timestamp
    unstake_tx = staking_contract.unstakeTokens(dai_token, {"from": user3})
    unstake_dai_3_timestamp = unstake_tx.timestamp
    # USER2 unstake PJTK
    unstake_tx = staking_contract.unstakeTokens(project_token, {"from": user2})
    unstake_pjtk_2_timestamp = unstake_tx.timestamp

    staking_time_weth_1_first = (
        unstake_weth_1_first_timestamp - stake_weth_1_first_timestamp
    )
    staking_time_weth_1_second = (
        update_weth_tx_timestamp - stake_weth_1_second_timestamp
    )
    staking_time_weth_1_third = (
        unstake_weth_1_second_timestamp - update_weth_tx_timestamp
    )
    staking_time_dai_1_first = update_dai_tx_timestamp - stake_dai_1_timestamp
    staking_time_dai_1_second = unstake_dai_1_timestamp - update_dai_tx_timestamp

    staking_time_weth_2_first = update_weth_tx_timestamp - stake_weth_2_timestamp
    staking_time_weth_2_second = unstake_weth_2_timestamp - update_weth_tx_timestamp
    staking_time_pjtk_2 = unstake_pjtk_2_timestamp - stake_pjtk_2_timestamp

    staking_time_weth_3_first = stake_weth_3_second_timestamp - stake_weth_3_timestamp
    staking_time_weth_3_second = (
        update_weth_tx_timestamp - stake_weth_3_second_timestamp
    )
    staking_time_weth_3_third = unstake_weth_3_timestamp - update_weth_tx_timestamp
    staking_time_dai_3 = unstake_dai_3_timestamp - stake_dai_3_timestamp

    # User 1
    assert staking_contract.tokenToClaim(user1) == cal_yield(
        weth_staked, staking_time_weth_1_first, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        weth_staked, staking_time_weth_1_second, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        weth_staked, staking_time_weth_1_third, _weth_new_yield
    ) + cal_yield(
        dai_staked, staking_time_dai_1_first, DAI_INITIAL_YIELDRATE
    ) + cal_yield(
        dai_staked, staking_time_dai_1_second, _dai_new_yield
    )

    # User 2
    assert (
        staking_contract.tokenToClaim(user2)
        == cal_yield(weth_staked, staking_time_weth_2_first, WETH_INITIAL_YIELDRATE)
        + cal_yield(weth_staked, staking_time_weth_2_second, _weth_new_yield)
        + 0
    )

    # User 3
    assert staking_contract.tokenToClaim(user3) == cal_yield(
        weth_staked, staking_time_weth_3_first, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        2 * weth_staked, staking_time_weth_3_second, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        2 * weth_staked, staking_time_weth_3_third, _weth_new_yield
    ) + cal_yield(
        222 * ONE, staking_time_dai_3, _dai_new_yield
    )

    # User 1,2,3 CLAIM their token
    init_pjtk_balance = project_token.balanceOf(user1)
    pjtk_to_claim = staking_contract.tokenToClaim(user1)
    staking_contract.claimToken({"from": user1})
    assert project_token.balanceOf(user1) == init_pjtk_balance + pjtk_to_claim

    init_pjtk_balance = project_token.balanceOf(user2)
    pjtk_to_claim = staking_contract.tokenToClaim(user2)
    staking_contract.claimToken({"from": user2})
    assert project_token.balanceOf(user2) == init_pjtk_balance + pjtk_to_claim

    init_pjtk_balance = project_token.balanceOf(user3)
    pjtk_to_claim = staking_contract.tokenToClaim(user3)
    staking_contract.claimToken({"from": user3})
    assert project_token.balanceOf(user3) == init_pjtk_balance + pjtk_to_claim
