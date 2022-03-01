// SPDX-License-Identifier: MIT

pragma solidity ^0.8.6;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/ILendingProtocol.sol";

interface Erc20 {
    function approve(address, uint256) external returns (bool);

    function transfer(address, uint256) external returns (bool);
}

interface CErc20 {
    function mint(uint256) external returns (uint256);

    function exchangeRateCurrent() external returns (uint256);

    function supplyRatePerBlock() external returns (uint256);

    function redeem(uint256) external returns (uint256);

    function redeemUnderlying(uint256) external returns (uint256);
}

contract CompoundLending is ILendingProtocol, Ownable {
    // event MyLog(string, uint256);

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
        tokenToCtoken[_dai] = _cDAI;
    }

    function setStakingContract(address _stakingContract) public onlyOwner {
        stakingContract = _stakingContract;
    }

    function addToken(address _token, address _cToken) public onlyOwner {
        tokenToCtoken[_token] = _cToken;
    }

    function deposit(
        address _token,
        uint256 _amount,
        address _from
    ) public override(ILendingProtocol) onlyStakingContract {
        // Create a reference to the underlying asset contract, like DAI.
        IERC20 token = IERC20(_token);

        // Create a reference to the corresponding cToken contract, like cDAI
        CErc20 cToken = CErc20(tokenToCtoken[_token]);

        token.transferFrom(msg.sender, address(this), _amount);
        token.approve(tokenToCtoken[_token], _amount);
        uint256 mintResult = cToken.mint(_amount);
    }

    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) public override(ILendingProtocol) onlyStakingContract returns (uint256) {
        // Create a reference to the corresponding cToken contract, like cDAI
        CErc20 cToken = CErc20(tokenToCtoken[_token]);
        cToken.redeemUnderlying(_amount);

        IERC20 token = IERC20(_token);
        token.transfer(_to, _amount);

        return _amount;
    }

    function drainToken(address _ctoken) public onlyOwner {
        IERC20 token = IERC20(_ctoken);
        token.transfer(msg.sender, token.balanceOf(address(this)));
    }
}
