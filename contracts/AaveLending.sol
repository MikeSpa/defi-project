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
            "AaveLending: Caller is not Staking Contract or owner"
        );
        _;
    }

    constructor(address _pool) {
        stakingContract = msg.sender;
        pool = ILendingPool(_pool);
    }

    function setStakingContract(address _stakingContract) external onlyOwner {
        require(
            _stakingContract != address(0),
            "AaveLending: address given is 0x0"
        );
        stakingContract = _stakingContract;
        emit StakingContractChange(_stakingContract);
    }

    function deposit(
        address _token,
        uint256 _amount,
        address
    ) external override(ILendingProtocol) onlyStakingContract {
        // LendingPool.deposit calls
        // IERC20(asset).safeTransferFrom(msg.sender, aToken, amount);
        // so this contract need the have the funds, cant just be a middleman
        require(
            IERC20(_token).transferFrom(msg.sender, address(this), _amount),
            "AaveLending: transferFrom() failed"
        );
        require(
            IERC20(_token).approve(address(pool), _amount),
            "AaveLending: approve() failed"
        ); //TODO general approve per asset
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
        // set _amount to type(uint256).max to withdraw the entire balance
        // need to return what is actually withdrawn
        uint256 amountWithdrawn = pool.withdraw(_token, _amount, _to);

        return amountWithdrawn;
    }

    function drainToken(address _token) external onlyOwner {
        IERC20 token = IERC20(_token);
        require(
            token.transfer(msg.sender, token.balanceOf(address(this))),
            "AaveLending: transfer() failed"
        );
    }
}
