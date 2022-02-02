// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "./FlashLoanPool.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title FlashLoanReceiver
 * @author Michael Spahr
 */
contract FlashLoanReceiver {
    FlashLoanPool private immutable pool;
    address private immutable owner;

    constructor(address poolAddress) {
        pool = FlashLoanPool(poolAddress);
        owner = msg.sender;
    }

    // Function called by the pool during the loan
    function receiveTokens(address tokenAddress, uint256 amount) external {
        require(msg.sender == address(pool), "Sender must be pool");
        // Return all tokens to the pool plus the fee
        uint256 fee = pool.getFee();
        require(
            IERC20(tokenAddress).transfer(msg.sender, amount + fee),
            "Transfer of tokens failed"
        );
    }

    function executeFlashLoan(uint256 amount) external {
        require(msg.sender == owner, "Only owner can execute flash loan");
        pool.flashLoan(amount);
    }
}
