// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

// import "../interfaces/ILendingPool.sol";

contract StakingContract is Ownable {
    IERC20 public projectToken;
    address[] public stakers;
    address[] public allowedTokens;
    mapping(address => mapping(address => uint256)) public stakingBalance;
    //how many different erc20 token the user has currently staked
    mapping(address => uint256) public uniqueTokensStaked;
    mapping(address => address) public tokenPriceFeedMapping;

    constructor(address _projectTokenAddress) public {
        projectToken = IERC20(_projectTokenAddress);
        // pool = _pool;
    }

    // set the price feed address for a token
    function setPriceFeedContract(address _token, address _priceFeed)
        public
        onlyOwner
    {
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    //issue project token to all stakers
    //TODO snapshot
    function issueTokens() public onlyOwner {
        // Issue tokens to all stakers
        for (uint256 i = 0; i < stakers.length; i++) {
            address recipient = stakers[i];
            uint256 userTotalValue = getUserTotalValue(recipient);
            projectToken.transfer(recipient, userTotalValue);
        }
    }

    // get the total value stake for a given user
    function getUserTotalValue(address _user) public view returns (uint256) {
        uint256 totalValue = 0;
        require(
            uniqueTokensStaked[_user] > 0,
            "StakingContract: No tokens staked!"
        );
        //for any stakable token
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            totalValue += getUserSingleTokenValue(_user, allowedTokens[i]);
        }
        return totalValue;
    }

    // get the value staked on one token for a user
    function getUserSingleTokenValue(address _user, address _token)
        public
        view
        returns (uint256)
    {
        if (uniqueTokensStaked[_user] <= 0) {
            return 0;
        }
        (uint256 price, uint256 decimals) = getTokenValue(_token);
        return ((stakingBalance[_token][_user] * price) / (10**decimals));
        //          amt staked                  * price  / 10**8
        // E.G.     10 ETH                      * 3'000(usd/eth)/ 100_000_000
    }

    // get the value of a token
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

    // stake a token
    function stakeTokens(uint256 _amount, address _token) public {
        require(_amount > 0, "StakingContract: Amount must be greater than 0");
        require(
            tokenIsAllowed(_token),
            "StakingContract: Token is currently no allowed"
        );
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        updateUniqueTokensStaked(msg.sender, _token);
        stakingBalance[_token][msg.sender] =
            stakingBalance[_token][msg.sender] +
            _amount;
        // add user to stakers list pnly if this is their first staking
        if (uniqueTokensStaked[msg.sender] == 1) {
            stakers.push(msg.sender);
        }
    }

    //unstake a token
    function unstakeTokens(address _token) public {
        uint256 balance = stakingBalance[_token][msg.sender];
        require(balance > 0, "StakingContract: Staking balance already 0!");
        stakingBalance[_token][msg.sender] = 0;
        uniqueTokensStaked[msg.sender] = uniqueTokensStaked[msg.sender] - 1;
        if (uniqueTokensStaked[msg.sender] == 0) {
            for (uint256 i = 0; i < stakers.length; i++) {
                if (stakers[i] == msg.sender) {
                    stakers[i] = stakers[stakers.length - 1];
                    stakers.pop();
                }
            }
        }
        IERC20(_token).transfer(msg.sender, balance);
    }

    // updates mapping telling us how any different token a user has staked
    function updateUniqueTokensStaked(address _user, address _token) internal {
        if (stakingBalance[_token][_user] <= 0) {
            uniqueTokensStaked[_user] = uniqueTokensStaked[_user] + 1;
        }
    }

    // add a new token to the list of stable token
    function addAllowedTokens(address _token) public onlyOwner {
        allowedTokens.push(_token);
    }

    // check if a token is stakable
    function tokenIsAllowed(address _token) public view returns (bool) {
        for (uint256 i = 0; i < allowedTokens.length; i++) {
            if (allowedTokens[i] == _token) {
                return true;
            }
        }
        return false;
    }

    //TODO remove token
}
