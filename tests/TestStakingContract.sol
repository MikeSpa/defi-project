// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./StakingContract.sol";
import "./ProjectToken.sol";
import "./AaveLending.sol";

contract Test {
    StakingContract stakingContract;
    ILendingProtocol aaveLending;
    ProjectToken pToken;
    ERC20 randomToken = new ERC20("Random Token", "RT");

    constructor() {
        // Create the target contract.
        aaveLending = new AaveLending(address(0x50000));
        stakingContract = new StakingContract(
            address(pToken),
            address(aaveLending)
        );
    }

    function echidna_test_owner() public view returns (bool) {
        return stakingContract.owner() == address(this);
    }

    function echidna_cant_add_allowed_token() public view returns (bool) {
        return !stakingContract.tokenIsAllowed(address(randomToken));
    }

    function echidna_cant_change_lending_protocol() public view returns (bool) {
        return stakingContract.lendingProtocol() == aaveLending;
    }
}
