// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../../interfaces/ILendingProtocol.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

//Todo mock interest
contract MockLendingPool is ILendingProtocol, Ownable {
    mapping(address => uint256) public stakingBalancePerToken;

    constructor() {}

    function deposit(
        address _token,
        uint256 _amount,
        address _from
    ) external override(ILendingProtocol) {
        require(
            IERC20(_token).transferFrom(msg.sender, address(this), _amount),
            "MockLendingProtocol: transfer failed"
        );
        stakingBalancePerToken[_token] += _amount;
    }

    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) external override(ILendingProtocol) returns (uint256) {
        stakingBalancePerToken[_token] -= _amount;
        require(
            IERC20(_token).transfer(_to, _amount),
            "MockLendingProtocol: transfer failed"
        );
        return _amount;
    }

    function drainToken(address _token) external onlyOwner {
        IERC20 token = IERC20(_token);
        require(
            token.transfer(msg.sender, token.balanceOf(address(this))),
            "MockLendingProtocol: transfer() failed"
        );
    }
}
