// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

interface IReceiver {
    function receiveTokens(address tokenAddress, uint256 amount) external;
}

/**
 * @title FlashLoanPool
 * @author Michael Spahr
 */
contract FlashLoanPool is ReentrancyGuard, Ownable {
    IERC20 public immutable token;
    uint256 public poolBalance;
    uint256 public fee;

    // address payable owner;

    constructor(address _tokenAddress, uint256 _fee) {
        require(
            _tokenAddress != address(0),
            "Need a valid ERC20 Token address"
        );
        token = IERC20(_tokenAddress);
        fee = _fee;
        // owner = msg.sender;
    }

    //Return the fee for a flash loan
    function getFee() external returns (uint256) {
        return fee;
    }

    //Set the fee
    function setFee(uint256 _fee) external onlyOwner {
        fee = _fee;
    }

    //Owner can add token to the pool
    function depositTokens(uint256 amount) external onlyOwner {
        require(amount > 0, "Must deposit at least one token");
        // require(msg.sender == owner, "Only the owner can deposit funds");

        token.transferFrom(msg.sender, address(this), amount);
        poolBalance = poolBalance + amount;
    }

    //Owner can withdraw token to the pool
    function withdrawTokens(uint256 amount) external onlyOwner {
        // require(msg.sender == owner, "Only the owner can withdraw funds");
        require(amount > 0, "Must withdraw at least one token");
        require(amount <= poolBalance, "Not enough token in the pool");

        token.transferFrom(address(this), msg.sender, amount);
        poolBalance = poolBalance - amount;
    }

    //Flashloan function
    function flashLoan(uint256 borrowAmount) external nonReentrant {
        require(borrowAmount > 0, "Must borrow at least one token");
        uint256 balanceBefore = token.balanceOf(address(this));
        require(balanceBefore >= borrowAmount, "Not enough tokens in the pool");

        token.transfer(msg.sender, borrowAmount);

        IReceiver(msg.sender).receiveTokens(address(token), borrowAmount);

        uint256 balanceAfter = token.balanceOf(address(this));
        require(
            balanceAfter >= balanceBefore + fee,
            "Flash loan hasn't been paid back"
        );
    }
}
