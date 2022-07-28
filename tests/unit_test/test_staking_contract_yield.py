from brownie import network, exceptions, ZERO_ADDRESS, reverts
from scripts.deploy_aave_lending_contract import deploy_aave_lending_contract
from scripts.deploy_compound_lending import deploy_compound_lending_contract
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    POINT_ONE,
    get_account,
    get_contract,
    CENT,
    distribute_token,
)
import pytest
from scripts.deploy_staking_contract import (
    deploy_staking_contract_and_project_token,
    deploy_and_stake_weth,
    add_allowed_tokens,
    stake_and_approve_token,
)
import time

WETH_INITIAL_YIELDRATE = 10  # 1%
PJTK_INITIAL_YIELDRATE = 0  # 0%


def cal_yield(amount, time, yield_rate):
    return (
        amount
        * INITIAL_PRICE_FEED_VALUE
        / 10 ** DECIMALS
        * time
        * yield_rate
        / 1000
        / 86400
    )


###########################################################  ONE TOKEN, ONE USER  #############################################################################


def test_tokenToClaim_after_2x_weth_stake_unstake():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    weth_staked = POINT_ONE
    init_tokenToClaim = staking_contract.tokenToClaim(account)
    assert init_tokenToClaim == 0
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )

    assert staking_contract.tokenToYieldRate(weth_token) == WETH_INITIAL_YIELDRATE

    # 1st STAKE 0.1 WETH for 4 sec
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    stake_timestamp = stake_tx.timestamp

    time.sleep(4)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time = unstake_timestamp - stake_timestamp

    yield_earn = cal_yield(weth_staked, staking_time, WETH_INITIAL_YIELDRATE)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn
    # Nothing should change since no stake during that time
    time.sleep(4)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn

    # 2nd STAKE 0.2 WETH for 7 sec
    cur_tokenToClaim = staking_contract.tokenToClaim(account)
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, 2 * weth_staked, account
    )
    stake_timestamp = stake_tx.timestamp

    time.sleep(7)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time = unstake_timestamp - stake_timestamp

    assert staking_contract.tokenToClaim(account) == cur_tokenToClaim + cal_yield(
        2 * weth_staked, staking_time, WETH_INITIAL_YIELDRATE
    )

    # CLAIM
    init_pjtk_balance = project_token.balanceOf(account)
    pjtk_to_claim = staking_contract.tokenToClaim(account)
    staking_contract.claimToken({"from": account})
    assert project_token.balanceOf(account) == init_pjtk_balance + pjtk_to_claim


def test_tokenToClaim_after_weth_stake_stake_unstake():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    weth_staked = POINT_ONE
    init_tokenToClaim = staking_contract.tokenToClaim(account)
    assert init_tokenToClaim == 0
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )

    assert staking_contract.tokenToYieldRate(weth_token) == WETH_INITIAL_YIELDRATE

    # 1st STAKE 0.1 WETH for 4 sec
    first_stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    first_stake_timestamp = first_stake_tx.timestamp

    time.sleep(4)

    # 2nd STAKE 0.1 WETH for 7 sec: total 0.2 WETH for 7 sec

    second_stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    second_stake_timestamp = second_stake_tx.timestamp
    first_stake_tokenToClaim = staking_contract.tokenToClaim(account)

    first_staking_time = second_stake_timestamp - first_stake_timestamp

    yield_earn = cal_yield(weth_staked, first_staking_time, WETH_INITIAL_YIELDRATE)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn

    # UNSTAKE
    time.sleep(7)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    second_staking_time = unstake_timestamp - second_stake_timestamp

    assert staking_contract.tokenToClaim(
        account
    ) == first_stake_tokenToClaim + cal_yield(
        2 * weth_staked, second_staking_time, WETH_INITIAL_YIELDRATE
    )

    # CLAIM
    init_pjtk_balance = project_token.balanceOf(account)
    pjtk_to_claim = staking_contract.tokenToClaim(account)
    staking_contract.claimToken({"from": account})
    assert project_token.balanceOf(account) == init_pjtk_balance + pjtk_to_claim


def test_tokenToClaim_after_2x_weth_stake_unstake_different_yield():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    weth_staked = POINT_ONE
    init_tokenToClaim = staking_contract.tokenToClaim(account)
    assert init_tokenToClaim == 0
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )

    assert staking_contract.tokenToYieldRate(weth_token) == WETH_INITIAL_YIELDRATE

    # 1st STAKE 0.1 WETH for 4 sec at 1%
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    stake_timestamp = stake_tx.timestamp

    time.sleep(4)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time = unstake_timestamp - stake_timestamp

    yield_earn = cal_yield(weth_staked, staking_time, WETH_INITIAL_YIELDRATE)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn
    # Nothing should change since no stake during that time
    time.sleep(1)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn

    # 2nd STAKE 0.1 WETH for 7 sec at 2%
    staking_contract.updateYieldRate(
        weth_token, 2 * WETH_INITIAL_YIELDRATE, {"from": account}
    )
    cur_tokenToClaim = staking_contract.tokenToClaim(account)
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    stake_timestamp = stake_tx.timestamp

    time.sleep(7)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time = unstake_timestamp - stake_timestamp

    assert staking_contract.tokenToClaim(account) == cur_tokenToClaim + cal_yield(
        weth_staked, staking_time, 2 * WETH_INITIAL_YIELDRATE
    )

    # CLAIM
    init_pjtk_balance = project_token.balanceOf(account)
    pjtk_to_claim = staking_contract.tokenToClaim(account)
    staking_contract.claimToken({"from": account})
    assert project_token.balanceOf(account) == init_pjtk_balance + pjtk_to_claim


def test_tokenToClaim_after_weth_stake_unstake_with_yield_update_between():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()

    weth_staked = POINT_ONE
    init_tokenToClaim = staking_contract.tokenToClaim(account)
    assert init_tokenToClaim == 0
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )

    assert staking_contract.tokenToYieldRate(weth_token) == WETH_INITIAL_YIELDRATE

    # STAKE 0.1 WETH for 13 sec at 1%
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    stake_timestamp = stake_tx.timestamp

    time.sleep(13)

    # YIELD CHANGE
    update_tx = staking_contract.updateYieldRate(
        weth_token, 2 * WETH_INITIAL_YIELDRATE, {"from": account}
    )
    update_timestamp = update_tx.timestamp
    staking_time = update_timestamp - stake_timestamp
    yield_earn = cal_yield(weth_staked, staking_time, WETH_INITIAL_YIELDRATE)
    tokenToClaim_at_update = staking_contract.tokenToClaim(account)
    assert tokenToClaim_at_update == init_tokenToClaim + yield_earn

    # STAKE 0.1 WETH for 7 sec at 2%

    time.sleep(7)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time = unstake_timestamp - update_timestamp

    assert staking_contract.tokenToClaim(account) == tokenToClaim_at_update + cal_yield(
        weth_staked, staking_time, 2 * WETH_INITIAL_YIELDRATE
    )

    # CLAIM
    init_pjtk_balance = project_token.balanceOf(account)
    pjtk_to_claim = staking_contract.tokenToClaim(account)
    staking_contract.claimToken({"from": account})
    assert project_token.balanceOf(account) == init_pjtk_balance + pjtk_to_claim


###########################################################  ONE TOKEN, THREE USERs  ##########################################################################


def test_tokenToClaim_after_three_users_stake_unstake_weth():
    """
    USER 1: stake 0.1 for 4 sec, unstake; stake 0.1 for 7 second.
    USER 2: stake 0.1 for 11 sec.
    USER 3: stake 0.1 for 4 sec; stake an additional 0.1 for 7 sec
    """
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    user1 = get_account(index=1)
    user2 = get_account(index=2)
    user3 = get_account(index=3)
    (
        staking_contract,
        project_token,
        weth_token,
        lending_protocol,
    ) = deploy_staking_contract_and_project_token()
    # send some WETH to user 1 and 2
    distribute_token(weth_token, 3)
    # print(weth_token.balanceOf(account))
    # print(weth_token.balanceOf(user1))
    # print(weth_token.balanceOf(user2))

    weth_staked = POINT_ONE
    init_tokenToClaim_1 = staking_contract.tokenToClaim(user1)
    init_tokenToClaim_2 = staking_contract.tokenToClaim(user2)
    init_tokenToClaim_3 = staking_contract.tokenToClaim(user3)
    # Initial
    assert init_tokenToClaim_1 == init_tokenToClaim_2 == init_tokenToClaim_3 == 0
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )

    # User1,2,3 STAKE 0.1 WETH
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user1)
    stake_1_timestamp = stake_tx.timestamp
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user2)
    stake_2_timestamp = stake_tx.timestamp
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user3)
    stake_3_timestamp = stake_tx.timestamp

    # User 1 unstake
    time.sleep(4)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user1})
    unstake_timestamp = unstake_tx.timestamp
    staking_time_1_first = unstake_timestamp - stake_1_timestamp

    # User1 reSTAKE 0.1 WETH for 7 sec
    # User3 STAKE additional 0.1 for 7 sec
    cur_tokenToClaim = staking_contract.tokenToClaim(user1)
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user1)
    stake_1_timestamp = stake_tx.timestamp
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user3)
    stake_3_timestamp_second = stake_tx.timestamp

    # User 1,2,3 unstake
    time.sleep(7)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user1})
    unstake_timestamp = unstake_tx.timestamp
    staking_time_1_second = unstake_timestamp - stake_1_timestamp
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user2})
    unstake_timestamp_2 = unstake_tx.timestamp
    staking_time_2 = unstake_timestamp_2 - stake_2_timestamp
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user3})
    unstake_timestamp_3 = unstake_tx.timestamp
    stake_3_time_first = stake_3_timestamp_second - stake_3_timestamp
    staking_time_3 = unstake_timestamp_3 - stake_3_timestamp_second

    # User 1
    assert staking_contract.tokenToClaim(user1) == cal_yield(
        weth_staked, staking_time_1_first, WETH_INITIAL_YIELDRATE
    ) + cal_yield(weth_staked, staking_time_1_second, WETH_INITIAL_YIELDRATE)
    # User 2
    assert staking_contract.tokenToClaim(user2) == cal_yield(
        weth_staked, staking_time_2, WETH_INITIAL_YIELDRATE
    )
    # User 3
    assert staking_contract.tokenToClaim(user3) == cal_yield(
        weth_staked, stake_3_time_first, WETH_INITIAL_YIELDRATE
    ) + cal_yield(2 * weth_staked, staking_time_3, WETH_INITIAL_YIELDRATE)

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
