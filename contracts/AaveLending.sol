//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../interfaces/ILendingProtocol.sol";
import "../interfaces/ILendingPool.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract AaveLending is ILendingProtocol, Ownable {
    ILendingPool public pool;

    constructor(address _pool) {
        pool = ILendingPool(_pool);
    }

    function deposit(
        address _token,
        uint256 _amount,
        address _from
    ) external override(ILendingProtocol) {
        IERC20(_token).approve(address(pool), _amount); //TODO general approve per asset
        pool.deposit(_token, _amount, _from, 0);
    }

    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) external override(ILendingProtocol) returns (uint256) {
        pool.withdraw(_token, _amount, _to);
    }
}
