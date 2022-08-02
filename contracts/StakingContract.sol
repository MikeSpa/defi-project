// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

import "../interfaces/ILendingProtocol.sol";

contract StakingContract is Ownable {
    IERC20 public projectToken;
    address[] public stakers;
    address[] public allowedTokens;
    //ERC20 -> user -> amount stakes
    mapping(address => mapping(address => uint256)) public stakingBalance;
    //how many different erc20 token the user has currently staked
    mapping(address => uint256) public uniqueTokensStaked;
    // ERC20 -> price feed address
    mapping(address => address) public tokenPriceFeedMapping;
    // user -> amount of projectToken they can claimed
    mapping(address => uint256) public tokenToClaim;
    // how much token user can earn per amount of time
    // token earn = total value [USD] * yield/1000 * time period[timestamp] / second_in_days
    // for a yieldRate of 10, user gain 1% of total value [USD] per day
    // token -> yieldRate
    mapping(address => uint256) public tokenToYieldRate;
    // user => token => time of last update
    mapping(address => mapping(address => uint256))
        public userToTokenToUnrealisedYieldTime;

    ILendingProtocol public lendingProtocol;

    // EVENTS
    event TokenAdded(address indexed token_address);
    event TokenStaked(
        address indexed token,
        address indexed staker,
        uint256 amount
    );
    event TokenUnstaked(
        address indexed token,
        address indexed staker,
        uint256 amount
    );
    event LendingProtocolChanged(address newProtocol, address oldProtocol);

    event YieldRateChange(address indexed token, uint256 newYield);

    // CONSTRUCTOR
    constructor(address _projectTokenAddress, address _lendingProtocol) {
        projectToken = IERC20(_projectTokenAddress);
        lendingProtocol = ILendingProtocol(_lendingProtocol);
    }

    // PUBLIC FUNCTIONS

    /// @notice Stake _amount of _token
    /// @param _amount The amount ot stake
    /// @param _token The address of the token
    function stakeTokens(uint256 _amount, address _token) external {
        // check parameters
        require(_amount > 0, "StakingContract: Amount must be greater than 0");
        require(
            tokenIsAllowed(_token),
            "StakingContract: Token is currently no allowed"
        );
        //update token to claim (if some amount already staked)
        _updateOneTokenToClaim(msg.sender, _token);
        require(
            IERC20(_token).transferFrom(msg.sender, address(this), _amount),
            "StakingContract: transferFrom() failed"
        );

        if (stakingBalance[_token][msg.sender] == 0) {
            uniqueTokensStaked[msg.sender] = uniqueTokensStaked[msg.sender] + 1;
        }

        stakingBalance[_token][msg.sender] =
            stakingBalance[_token][msg.sender] +
            _amount;

        // add user to stakers list pnly if this is their first staking
        if (uniqueTokensStaked[msg.sender] == 1) {
            stakers.push(msg.sender);
        }

        //deposit on lending protocol
        lendingProtocol.deposit(_token, _amount, address(this));
        emit TokenStaked(_token, msg.sender, _amount);
    }

    /// @notice Unstake all _token staked
    /// @param _token The address of the token
    function unstakeTokens(address _token) external {
        //check token to unstake
        uint256 balance = stakingBalance[_token][msg.sender];
        require(balance > 0, "StakingContract: Staking balance already 0!");
        //update token to claim
        _updateOneTokenToClaim(msg.sender, _token);
        // update contract data
        stakingBalance[_token][msg.sender] = 0;
        uniqueTokensStaked[msg.sender] = uniqueTokensStaked[msg.sender] - 1;
        if (uniqueTokensStaked[msg.sender] == 0) {
            for (uint256 i = 0; i < stakers.length; i++) {
                if (stakers[i] == msg.sender) {
                    stakers[i] = stakers[stakers.length - 1];
                    stakers.pop();
                    break;
                }
            }
        }

        //withdraw from lending protocol and send to user
        //and send tokens to user
        require(
            lendingProtocol.withdraw(_token, balance, msg.sender) > 0,
            "StakingContract: withdraw error"
        );
        emit TokenUnstaked(_token, msg.sender, balance);
    }

    /// @notice Send Earned "ProjectToken" to user
    function claimToken() external {
        //Todo update yield per token in stake/unstake and here do it for each token
        _updateTokenToClaim(msg.sender);
        uint256 amount = tokenToClaim[msg.sender];
        tokenToClaim[msg.sender] = 0;
        require(
            projectToken.transfer(msg.sender, amount),
            "StakingContract: transfer failed"
        );
    }

    /// @notice Check wheter a token is stakable on this contract
    /// @param _token The address of the token
    /// @return bool Wheter the token is stakable or not
    function tokenIsAllowed(address _token) public view returns (bool) {
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            if (allowedTokens[i] == _token) {
                return true;
            }
        }
        return false;
    }

    /// @notice Get the total value (in USD) staked by _user
    /// @param _user The address of the user
    /// @return totalValue The total value  of the tokens staked on the contract by _user
    function getUserTotalValue(address _user) public view returns (uint256) {
        if (uniqueTokensStaked[_user] == 0) {
            return 0;
        }
        uint256 totalValue = 0;
        //for any stakable token
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            totalValue += getUserSingleTokenValue(_user, allowedTokens[i]);
        }
        return totalValue;
    }

    /// @notice Get the value (in USD) of _token staked by _user
    /// @param _user The address of the user
    /// @param _token The address of the token
    /// @return tokenValue The value of _token staked on the contract by _user
    function getUserSingleTokenValue(address _user, address _token)
        public
        view
        returns (uint256)
    {
        (uint256 price, uint256 decimals) = getTokenValue(_token);
        //TODO
        uint256 tokenValue = ((stakingBalance[_token][_user] * price) /
            (10**decimals));
        return tokenValue;
        //          amt staked                  * price  / 10**8
        // E.G.     10 WETH                      * 3'000(usd/weth)/ 100_000_000
    }

    /// @notice Get the value (in USD) of a _token and its decimals()
    /// @param _token The address of the token
    /// @return price The value of _token
    /// @return decimals The number of decimals of the _token
    function getTokenValue(address _token)
        public
        view
        returns (uint256, uint256)
    {
        address priceFeedAddress = tokenPriceFeedMapping[_token];
        AggregatorV3Interface priceFeed = AggregatorV3Interface(
            priceFeedAddress
        );
        (, int256 price, , , ) = priceFeed.latestRoundData();
        uint256 decimals = uint256(priceFeed.decimals());
        return (uint256(price), decimals);
    }

    // ONLYOWNER

    /// @notice Set the price feed address for an ERC20 token
    /// @dev Gets call automatically when adding new token
    /// @param _token The address of the token
    /// @param _priceFeed The address of the pricefeed
    function setPriceFeedContract(address _token, address _priceFeed)
        public
        onlyOwner
    {
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    /// @notice Add a new _token to the list of stakable token
    /// @param _token The address of the token
    /// @param _pricefeed The address for the price feed of _token
    function addAllowedTokens(
        address _token,
        address _pricefeed,
        uint256 _yield
    ) external onlyOwner {
        allowedTokens.push(_token);
        require(
            IERC20(_token).approve(address(lendingProtocol), type(uint256).max),
            "StakingContract: approve() failed"
        );
        setPriceFeedContract(_token, _pricefeed);
        updateYieldRate(_token, _yield);
        emit TokenAdded(_token);
    }

    // @notice Update the yield rate for _token
    /// @param _token The address of the token
    /// @param _newYieldRate The new yield rate
    function updateYieldRate(address _token, uint256 _newYieldRate)
        public
        onlyOwner
    {
        //for all staker who have _token staked, we calculate the amount they can claim with the previous yield
        //before updating the yield
        for (uint256 i = 0; i < stakers.length; i++) {
            if (stakingBalance[_token][stakers[i]] > 0) {
                _updateOneTokenToClaim(stakers[i], _token);
            }
        }
        //update yield
        tokenToYieldRate[_token] = _newYieldRate;
        emit YieldRateChange(_token, _newYieldRate);
    }

    /// @notice Change the lending protocol
    /// @param _newLendingProtocol The address of the new lending protocol contract
    function changeLendingProtocol(address _newLendingProtocol)
        external
        onlyOwner
    {
        address oldProtocol = address(lendingProtocol);
        lendingProtocol = ILendingProtocol(_newLendingProtocol);
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            require(
                IERC20(allowedTokens[i]).approve(
                    _newLendingProtocol,
                    type(uint256).max
                ),
                "StakingContract: approve() failed"
            );
        }
        //withdraw and redeposit
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            address token = allowedTokens[i];
            uint256 totalStaked = 0;
            for (uint256 j = 0; j < stakers.length; j++) {
                address staker = stakers[j];
                totalStaked += stakingBalance[token][staker]; //TODO
            }
            ILendingProtocol(oldProtocol).withdraw(
                token,
                totalStaked,
                address(this)
            );
            lendingProtocol.deposit(token, totalStaked, address(this));
        }
        emit LendingProtocolChanged(_newLendingProtocol, oldProtocol);
    }

    //  INTERNAL FUNCTION

    /// @notice Update the tokenToClaim variable of _user for all token staked
    /// @param _user The address of the user
    function _updateTokenToClaim(address _user) internal {
        //loop through all token
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            if (stakingBalance[allowedTokens[i]][_user] > 0) {
                _updateOneTokenToClaim(_user, allowedTokens[i]);
            }
        }
    }

    /// @notice Update the tokenToClaim variable of _user for _token
    /// @param _user The address of the user
    /// @param _token The address of the token
    function _updateOneTokenToClaim(address _user, address _token) internal {
        uint256 unrealisedYieldTime = userToTokenToUnrealisedYieldTime[_user][
            _token
        ];
        userToTokenToUnrealisedYieldTime[_user][_token] = block.timestamp;

        uint256 valueStaked = getUserSingleTokenValue(_user, _token);
        uint256 time = block.timestamp - unrealisedYieldTime;
        uint256 day = 1 days;
        uint256 tokenYieldRate = tokenToYieldRate[_token];
        uint256 additionalYield = ((valueStaked * time * tokenYieldRate) /
            1000) / day;

        tokenToClaim[_user] += additionalYield;
    }
}
