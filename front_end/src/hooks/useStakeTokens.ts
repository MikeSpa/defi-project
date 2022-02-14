import { useEffect, useState } from "react"
import { useEthers, useContractFunction } from "@usedapp/core"
import { constants, utils } from "ethers"
import StakingContract from "../chain-info/contracts/StakingContract.json"
import ERC20 from "../chain-info/contracts/MockERC20.json"
import { Contract } from "@ethersproject/contracts"
import networkMapping from "../chain-info/deployments/map.json"

export const useStakeTokens = (tokenAddress: string) => {

    const { chainId } = useEthers()
    const { abi } = StakingContract
    const stakingContractAddress = chainId ? networkMapping[String(chainId)]["StakingContract"][0] : constants.AddressZero
    const stakingContractInterface = new utils.Interface(abi)
    const stakingContract = new Contract(stakingContractAddress, stakingContractInterface)

    const erc20ABI = ERC20.abi
    const erc20Interface = new utils.Interface(erc20ABI)
    const erc20Contract = new Contract(tokenAddress, erc20Interface)
    // approve
    // useContractFunction: Hook returns an object with four variables: state , send, events , and resetState.
    //param: contract, functionname in the contract, options?
    const { send: approveErc20Send, state: approveAndStakeErc20State } =
        useContractFunction(erc20Contract, "approve", {
            transactionName: "Approve ERC20 transfer",
        })
    const approveAndStake = (amount: string) => {
        setAmountToStake(amount)
        return approveErc20Send(stakingContractAddress, amount)
    }
    // stake
    const { send: stakeSend, state: stakeState } =
        useContractFunction(stakingContract, "stakeTokens", {
            transactionName: "Stake Tokens",
        })
    const [amountToStake, setAmountToStake] = useState("0") // we get the amount from approveAndStake

    //useEffect: do smth if some variable has changed
    useEffect(() => {
        if (approveAndStakeErc20State.status === "Success") {
            stakeSend(amountToStake, tokenAddress) // param of the function in solidity
        }
    }, [approveAndStakeErc20State, amountToStake, tokenAddress]) //if smth in this array changed, is approveerc20 done? yes -> stake some token


    const [state, setState] = useState(approveAndStakeErc20State)

    useEffect(() => {
        if (approveAndStakeErc20State.status === "Success") {
            setState(stakeState)
        } else {
            setState(approveAndStakeErc20State)
        }
    }, [approveAndStakeErc20State, stakeState])

    return { approveAndStake, state }
}