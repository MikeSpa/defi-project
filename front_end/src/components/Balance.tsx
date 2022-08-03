import { Token } from "./Main"
import { useEthers, useTokenBalance } from "@usedapp/core"
import { formatUnits } from "@ethersproject/units"
import { useUnstakeTokens, useStakingBalance } from "../hooks"


export interface WalletBalanceProps {
    token: Token
}


export const Balance = ({ token }: WalletBalanceProps) => {
    const { image, address, name } = token
    const { account } = useEthers()
    const stakingBalance = useStakingBalance(address)
    const formattedTokenBalance = stakingBalance ? parseInt(formatUnits(stakingBalance, 17)) / 10 : 0
    console.log(formattedTokenBalance)
    return formattedTokenBalance
}   