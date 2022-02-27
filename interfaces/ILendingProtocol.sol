// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

//Staking contract should have a Ilending OR mapping of Ilending per asset
// add fct to change lending protocol
//MockLending is ILending
//AaveLendingPool is ILending
//CompoundSmth is ILending

interface ILendingProtocol {
    /**
     * @notice Deposit '_amounts' worth of '_asset' to a lending protocol
     * @dev Will revert if the amount exceeds the balance.
     * @param _token The address of the token to be deposited
     * @param _amount The amount to deposit
     * @param _from The address that deposit
     */
    function deposit(
        address _token,
        uint256 _amount,
        address _from
    ) external;

    /**
     * @notice Withdraw '_amounts' worth of '_asset' from a lending protocol
     * @dev Will revert if the amount exceeds the balance deposited.
     * @param _token The address of the token to be deposited
     * @param _amount The amount to withdraw
     * @param _to The address that should receive thefunds
     * @return The final amount withdrawn
     */
    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) external returns (uint256);
}
