// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockLendingPool {
    mapping(address => uint256) public stakingBalancePerToken;

    constructor() {}

    function deposit(
        address _token,
        uint256 _amount,
        address onBehalfOf,
        uint16 referralCode
    ) external {
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        stakingBalancePerToken[_token] += _amount;
    }

    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) external returns (uint256) {
        require(
            _amount <= stakingBalancePerToken[_token],
            "Can't withdraw more than current balance deposit"
        );
        IERC20(_token).transfer(_to, _amount);
        stakingBalancePerToken[_token] -= _amount;
        return _amount;
    }
}
