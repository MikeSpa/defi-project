import { useContractCall, useEthers } from "@usedapp/core"
import StakingContract from "../chain-info/contracts/StakingContract.json"
import { utils, BigNumber, constants } from "ethers"
import networkMapping from "../chain-info/deployments/map.json"

/**
 * Get the yield rate of a certain token in our Staking contract
 * @param address - The contract address of the token
 */
export const useYieldRate = (address: string): BigNumber | undefined => {
    const { account, chainId } = useEthers()

    const { abi } = StakingContract
    const stakingContractAddress = chainId ? networkMapping[String(chainId)]["StakingContract"][0] : constants.AddressZero

    const stakingInterface = new utils.Interface(abi)

    const [yieldRate] =
        useContractCall({
            abi: stakingInterface,
            address: stakingContractAddress,
            method: "tokenToYieldRate",
            args: [address],
        }) ?? []

    return yieldRate
}