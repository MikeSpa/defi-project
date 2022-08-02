// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

//Staking contract should have a Ilending OR mapping of Ilending per asset
// add fct to change lending protocol
//MockLending is ILending
//AaveLending is ILending
//CompounLending is ILending

interface ILendingProtocol {
    event StakingContractChange(address newContract);

    /**
     * @notice Deposit '_amount' worth of '_token' to a lending protocol
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
     * @notice Withdraw '_amount' worth of '_token' from a lending protocol AND send it to _to
     * @dev Will revert if the amount exceeds the balance deposited.
     * @param _token The address of the token to be deposited
     * @param _amount The amount to withdraw
     * @param _to The address that should receive the funds
     * @return The final amount withdrawn
     */
    function withdraw(
        address _token,
        uint256 _amount,
        address _to
    ) external returns (uint256);

    /**
     * @notice Drain all the token of address _token
     * @param _token The address of the token we want to drain
     */
    function drainToken(address _token) external;
}
