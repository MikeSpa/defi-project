import { useContractFunction, useEthers } from "@usedapp/core"
import StakingContract from "../chain-info/contracts/StakingContract.json"
import { utils, constants } from "ethers"
import { Contract } from "@ethersproject/contracts"
import networkMapping from "../chain-info/deployments/map.json"

/**
 * Expose { send, state } object to facilitate unstaking the user's tokens from the staking contract
 */
export const useClaimToken = () => {
    const { chainId } = useEthers()

    const { abi } = StakingContract
    const stakingContractAddress = chainId ? networkMapping[String(chainId)]["StakingContract"][0] : constants.AddressZero

    const stakingInterface = new utils.Interface(abi)

    const stakingContract = new Contract(
        stakingContractAddress,
        stakingInterface
    )

    return useContractFunction(stakingContract, "claimToken", {
        transactionName: "Claim tokens",
    })
}