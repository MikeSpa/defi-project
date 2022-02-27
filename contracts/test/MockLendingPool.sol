// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../../interfaces/ILendingProtocol.sol";

//Todo mock interest
contract MockLendingPool is ILendingProtocol {
    mapping(address => uint256) public stakingBalancePerToken;

    constructor() {}

    function deposit(
        address _token,
        uint256 _amount,
        address _from
    ) external override(ILendingProtocol) {
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        stakingBalancePerToken[_token] += _amount;
    }

    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) external override(ILendingProtocol) returns (uint256) {
        IERC20(_token).transfer(_to, _amount);
        stakingBalancePerToken[_token] -= _amount;
        return _amount;
    }
}
