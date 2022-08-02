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
    ONE,
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


###########################################################  ONE TOKEN, ONE USER  #############################################################################


def test_tokenToClaim_after_2x_weth_stake_unstake():
    """
    ACCOUNT: stake 0.1 WETH for 4 sec at yieldRate 10, unstake
    ACCOUNT: restake 0.1 WETH for 7 sec at yieldRate 10, unstake
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
    """
    ACCOUNT: stake 0.1 WETH for 4 sec at yieldRate 10
    ACCOUNT: stake additional 0.1 WETH for 7 sec at yieldRate 10, unstake
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
    """
    ACCOUNT: stake 0.1 WETH for 4 sec at yieldRate 10, unstake
    YieldRate for WETH change to 20
    ACCOUNT: reSTAKE 0.1 WETH for 7 sec at yieldRate 20, unstake
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
    """
    ACCOUNT: stake 0.1 WETH for 13 sec at yieldRate 10
    YieldRate for WETH change to 20
    ACCOUNT: still 0.1 WETH staked for 7 sec at yieldRate 20, unstake
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
    USER 1: stake 0.1 WETH for 4 sec, unstake
    USER 1: restake 0.1 WETH for 7 second, unstake.
    USER 2: stake 0.1 WETH for 11 sec, unstake
    USER 3: stake 0.1 WETH for 4 sec.
    USER 3: stake an additional 0.1 WETH for 7 sec, unstake.
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


##########################################################  PROJECTTOKEN, ONE USER  ###########################################################################


def test_tokenToClaim_after_project_token_stake_unstake():
    """
    ACCOUNT: stake 100 PJTK for 4 sec at yieldRate 0, unstake
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
    print(staking_contract.getUserTotalValue(account))
    pricefeed_of_token: dict = {
        project_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(
        staking_contract, pricefeed_of_token, PJTK_INITIAL_YIELDRATE, account
    )

    pjtk_staked = CENT
    init_tokenToClaim = staking_contract.tokenToClaim(account)
    assert init_tokenToClaim == 0

    assert staking_contract.tokenToYieldRate(account) == PJTK_INITIAL_YIELDRATE == 0

    # 1st STAKE 100 PJTK for 4 sec
    stake_tx = stake_and_approve_token(
        staking_contract, project_token, pjtk_staked, account
    )
    stake_timestamp = stake_tx.timestamp

    time.sleep(4)
    unstake_tx = staking_contract.unstakeTokens(project_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time = unstake_timestamp - stake_timestamp

    yield_earn = cal_yield(pjtk_staked, staking_time, PJTK_INITIAL_YIELDRATE)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn
    # Nothing should change since no stake during that time
    time.sleep(4)
    assert staking_contract.tokenToClaim(account) == init_tokenToClaim + yield_earn

    # CLAIM
    init_pjtk_balance = project_token.balanceOf(account)
    pjtk_to_claim = staking_contract.tokenToClaim(account)
    staking_contract.claimToken({"from": account})
    assert project_token.balanceOf(account) == init_pjtk_balance + pjtk_to_claim


##########################################################  SEVERAL TOKENS, ONE USER  #########################################################################


def test_tokenToClaim_weth_and_dai():
    """
    ACCOUNT: stake 0.1 WETH for 4 sec at yieldRate 10, unstake
    ACCOUNT: restake 0.2 WETH for 7 sec at yieldRate 10, unstake
    ACCOUNT: stake 0.1 DAI for 7 sec at yieldRate 35, unstake
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
    staking_contract.updateYieldRate(
        weth_token, WETH_INITIAL_YIELDRATE, {"from": account}
    )

    dai_token = get_contract("fau_token")
    pricefeed_of_token = {
        dai_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(
        staking_contract, pricefeed_of_token, DAI_INITIAL_YIELDRATE, account
    )
    print(dai_token.balanceOf(account))

    weth_staked = POINT_ONE
    dai_staked = POINT_ONE

    init_tokenToClaim = staking_contract.tokenToClaim(account)
    assert init_tokenToClaim == 0
    assert (
        staking_contract.tokenIsAllowed(dai_token)
        == staking_contract.tokenIsAllowed(weth_token)
        == True
    )
    assert staking_contract.tokenToYieldRate(weth_token) == WETH_INITIAL_YIELDRATE
    assert staking_contract.tokenToYieldRate(dai_token) == DAI_INITIAL_YIELDRATE

    # 1st STAKE 0.1 WETH for 4 sec
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, weth_staked, account
    )
    stake_weth_first_timestamp = stake_tx.timestamp

    time.sleep(4)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_timestamp = unstake_tx.timestamp
    staking_time_1_first = unstake_timestamp - stake_weth_first_timestamp

    # 2nd STAKE 0.2 WETH for 7 sec
    stake_tx = stake_and_approve_token(
        staking_contract, weth_token, 2 * weth_staked, account
    )
    stake_weth_1_second_timestamp = stake_tx.timestamp

    # STAKE  0.1 DAI for 7 sec
    stake_tx = stake_and_approve_token(staking_contract, dai_token, dai_staked, account)
    stake_dai_timestamp = stake_tx.timestamp

    time.sleep(7)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": account})
    unstake_weth_timestamp = unstake_tx.timestamp
    staking_time_weth_second = unstake_weth_timestamp - stake_weth_1_second_timestamp

    unstake_tx = staking_contract.unstakeTokens(dai_token, {"from": account})
    unstake_dai_timestamp = unstake_tx.timestamp
    staking_time_dai = unstake_dai_timestamp - stake_dai_timestamp

    assert staking_contract.tokenToClaim(account) == cal_yield(
        weth_staked, staking_time_1_first, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        2 * weth_staked, staking_time_weth_second, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        dai_staked, staking_time_dai, DAI_INITIAL_YIELDRATE
    )

    # CLAIM
    init_pjtk_balance = project_token.balanceOf(account)
    pjtk_to_claim = staking_contract.tokenToClaim(account)
    staking_contract.claimToken({"from": account})
    assert project_token.balanceOf(account) == init_pjtk_balance + pjtk_to_claim


##########################################################  SEVERAL TOKENS, SEVERAL USER  #####################################################################


def test_tokenToClaim_three_user_weth_dai_and_project_token():
    """
    _______________________WETH______________________________
    USER1: stake 0.1 WETH for 4 sec at yieldRate 10, unstake
    USER1: restake 0.1 WETH at 10 for 7 sec
    USER2: stake 0.1 WETH for 11 sec at yieldRate 10
    USER3: stake 0.1 WETH for 11 sec at yieldRate 10
    USER3: stake add. 0.1 WETH for 7 sec at yieldRate 10

    11: YieldRate of WETH change to 20

    USER1: still 0.1 WETH staked at 20 for 10 sec, unstake
    USER2: still 0.1 WETH staked at 20 for 10 sec, unstake
    USER3: still 0.2 WETH staked at 20 for 10 sec, unstake

    _______________________DAI______________________________

    USER1: stake 500 DAI for 15 sec at yieldRate 35
    USER2: no DAI
    USER3: nothing yet

    15: YieldRate of DAI change to 45

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
    print(weth_token.balanceOf(account))
    print(weth_token.balanceOf(user1))
    print(weth_token.balanceOf(user2))
    print(weth_token.balanceOf(user3))
    print(dai_token.balanceOf(account))
    print(dai_token.balanceOf(user1))
    print(dai_token.balanceOf(user2))
    print(dai_token.balanceOf(user3))
    print(project_token.balanceOf(account))
    print(project_token.balanceOf(user1))
    print(project_token.balanceOf(user2))
    print(project_token.balanceOf(user3))

    weth_staked = POINT_ONE
    FIVEHUNDRED = 5 * CENT
    pjtk_staked = ONE

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
    stake_tx = stake_and_approve_token(staking_contract, dai_token, FIVEHUNDRED, user1)
    stake_dai_1_timestamp = stake_tx.timestamp
    # User2 STAKE 8.12 PJTK
    stake_tx = stake_and_approve_token(
        staking_contract, project_token, 8.12 * ONE, user2
    )
    stake_pjtk_2_timestamp = stake_tx.timestamp

    # t=4
    # User 1 unstake
    time.sleep(4)
    unstake_tx = staking_contract.unstakeTokens(weth_token, {"from": user1})
    unstake_weth_1_first_timestamp = unstake_tx.timestamp
    # User1 reSTAKE 0.1 WETH for 7 sec
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user1)
    stake_weth_1_second_timestamp = stake_tx.timestamp
    # User3 STAKE additional 0.1 for 7 sec
    stake_tx = stake_and_approve_token(staking_contract, weth_token, weth_staked, user3)
    stake_weth_3_second_timestamp = stake_tx.timestamp

    # t=11
    # WETH YieldRate change to 20
    time.sleep(7)
    update_weth_tx = staking_contract.updateYieldRate(
        weth_token, 2 * WETH_INITIAL_YIELDRATE, {"from": account}
    )
    update_weth_tx_timestamp = update_weth_tx.timestamp

    # t=15
    # DAI YieldRate change to 45
    time.sleep(4)
    update_dai_tx = staking_contract.updateYieldRate(dai_token, 45, {"from": account})
    update_dai_tx_timestamp = update_dai_tx.timestamp
    # USER3 STAKE 222 DAI
    stake_tx = stake_and_approve_token(staking_contract, dai_token, 222 * ONE, user3)
    stake_dai_3_timestamp = stake_tx.timestamp

    # t=21
    # User 1,2,3 unstake WETH
    time.sleep(6)
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
        weth_staked, staking_time_weth_1_third, 2 * WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        FIVEHUNDRED, staking_time_dai_1_first, DAI_INITIAL_YIELDRATE
    ) + cal_yield(
        FIVEHUNDRED, staking_time_dai_1_second, 45
    )

    # User 2
    assert (
        staking_contract.tokenToClaim(user2)
        == cal_yield(weth_staked, staking_time_weth_2_first, WETH_INITIAL_YIELDRATE)
        + cal_yield(weth_staked, staking_time_weth_2_second, 2 * WETH_INITIAL_YIELDRATE)
        + 0
    )

    # User 3
    assert staking_contract.tokenToClaim(user3) == cal_yield(
        weth_staked, staking_time_weth_3_first, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        2 * weth_staked, staking_time_weth_3_second, WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        2 * weth_staked, staking_time_weth_3_third, 2 * WETH_INITIAL_YIELDRATE
    ) + cal_yield(
        222 * ONE, staking_time_dai_3, 45
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
