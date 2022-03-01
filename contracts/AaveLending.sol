//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../interfaces/ILendingProtocol.sol";
import "../interfaces/ILendingPool.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract AaveLending is ILendingProtocol, Ownable {
    ILendingPool public pool;
    address public stakingContract;

    modifier onlyStakingContract() {
        require(
            msg.sender == stakingContract,
            "CompoundLending: Caller is not Staking Contract or owner"
        );
        _;
    }

    constructor(address _pool) {
        pool = ILendingPool(_pool);
    }

    function setStakingContract(address _stakingContract) public onlyOwner {
        stakingContract = _stakingContract;
    }

    function deposit(
        address _token,
        uint256 _amount,
        address _from
    ) external override(ILendingProtocol) onlyStakingContract {
        // LendingPool.deposit calls
        // IERC20(asset).safeTransferFrom(msg.sender, aToken, amount);
        // so this contract need the have the funds, cant just be a middleman
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        IERC20(_token).approve(address(pool), _amount); //TODO general approve per asset
        pool.deposit(_token, _amount, address(this), 0);
    }

    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    )
        external
        override(ILendingProtocol)
        onlyStakingContract
        returns (uint256)
    {
        pool.withdraw(_token, _amount, _to);
    }

    function drainToken(address _token) public onlyOwner {
        IERC20 token = IERC20(_token);
        token.transfer(msg.sender, token.balanceOf(address(this)));
    }
}
