import { Token } from "./Main"
import { formatUnits } from "@ethersproject/units"
import { useStakingBalance } from "../hooks"


export interface WalletBalanceProps {
    token: Token
}


export const Balance = ({ token }: WalletBalanceProps) => {
    const { address } = token
    const stakingBalance = useStakingBalance(address)
    const formattedTokenBalance = stakingBalance ? parseInt(formatUnits(stakingBalance, 17)) / 10 : 0
    console.log(formattedTokenBalance)
    return formattedTokenBalance
}   