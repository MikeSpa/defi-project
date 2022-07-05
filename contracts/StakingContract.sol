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
    //user -> ERC20 -> amount stakes
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
    uint256 public yieldRate = 10; //TODO mutable + yieldRate[_token]
    // user => time of last update
    mapping(address => uint256) public userToUnrealisedYieldTime;

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
        _updateYield(msg.sender);

        require(_amount > 0, "StakingContract: Amount must be greater than 0");
        require(
            tokenIsAllowed(_token),
            "StakingContract: Token is currently no allowed"
        );
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
        _updateYield(msg.sender);
        uint256 balance = stakingBalance[_token][msg.sender];
        require(balance > 0, "StakingContract: Staking balance already 0!");
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
        _updateYield(msg.sender);
        uint256 amount = tokenToClaim[msg.sender];
        tokenToClaim[msg.sender] = 0;
        require(projectToken.transfer(msg.sender, amount));
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
    function addAllowedTokens(address _token, address _pricefeed)
        external
        onlyOwner
    {
        allowedTokens.push(_token);
        require(
            IERC20(_token).approve(address(lendingProtocol), type(uint256).max),
            "StakingContract: approve() failed"
        );
        setPriceFeedContract(_token, _pricefeed);
        emit TokenAdded(_token);
    }

    /// @notice Change the lending protocol
    /// @param _newLendingProtocol The address of the new lending protocol contract
    function changeLendingProtocol(address _newLendingProtocol)
        external
        onlyOwner
    {
        //TODO
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
        emit LendingProtocolChanged(_newLendingProtocol, oldProtocol);
    }

    //  INTERNAL FUNCTION

    //TODO could be a modifier
    /// @notice Update the tokenToClaim variable of _user
    /// @param _user The address of the user
    function _updateYield(address _user) internal {
        uint256 unrealisedYieldTime = userToUnrealisedYieldTime[_user];
        userToUnrealisedYieldTime[_user] = block.timestamp;

        uint256 totalValue = getUserTotalValue(_user);
        uint256 time = block.timestamp - unrealisedYieldTime;
        uint256 secondsInDay = 86400;
        //TODO yieldRate[_token]
        uint256 additionalYield = ((totalValue * time * yieldRate) / 1000) /
            secondsInDay;

        tokenToClaim[_user] += additionalYield;
    }
}
