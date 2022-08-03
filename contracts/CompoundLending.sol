// SPDX-License-Identifier: MIT

pragma solidity ^0.8.6;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/ILendingProtocol.sol";

interface CErc20 {
    function mint(uint256) external returns (uint256);

    function exchangeRateCurrent() external returns (uint256);

    function supplyRatePerBlock() external returns (uint256);

    function redeem(uint256) external returns (uint256);

    function redeemUnderlying(uint256) external returns (uint256);
}

contract CompoundLending is ILendingProtocol, Ownable {
    mapping(address => address) public tokenToCtoken;
    address public stakingContract;

    modifier onlyStakingContract() {
        require(
            msg.sender == stakingContract,
            "CompoundLending: Caller is not Staking Contract or owner"
        );
        _;
    }

    constructor(address _dai, address _cDAI) {
        stakingContract = msg.sender;
        tokenToCtoken[_dai] = _cDAI;
    }

    function setStakingContract(address _stakingContract) external onlyOwner {
        require(
            _stakingContract != address(0),
            "CompoundLending: address given is 0x0"
        );
        stakingContract = _stakingContract;
        emit StakingContractChange(_stakingContract);
    }

    function addToken(address _token, address _cToken) external onlyOwner {
        tokenToCtoken[_token] = _cToken;
    }

    function deposit(
        address _token,
        uint256 _amount,
        address /*_from*/
    ) external override(ILendingProtocol) onlyStakingContract {
        // Create a reference to the underlying asset contract, like DAI.
        IERC20 token = IERC20(_token);

        // Create a reference to the corresponding cToken contract, like cDAI
        CErc20 cToken = CErc20(tokenToCtoken[_token]);
        require(
            token.transferFrom(msg.sender, address(this), _amount),
            "CompoundLending: transferFrom() failed"
        );
        require(
            token.approve(tokenToCtoken[_token], _amount),
            "CompoundLending: approve() failed"
        );

        uint256 mintResult = cToken.mint(_amount);
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
        // Create a reference to the corresponding cToken contract, like cDAI
        CErc20 cToken = CErc20(tokenToCtoken[_token]);
        uint256 amountWithdrawn = cToken.redeemUnderlying(_amount);

        IERC20 token = IERC20(_token);
        require(
            token.transfer(_to, amountWithdrawn),
            "CompoundLending: transfer() failed"
        );

        return amountWithdrawn;
    }

    function drainToken(address _ctoken)
        external
        override(ILendingProtocol)
        onlyOwner
    {
        IERC20 token = IERC20(_ctoken);
        require(
            token.transfer(msg.sender, token.balanceOf(address(this))),
            "CompoundLending: transfer() failed"
        );
    }
}
