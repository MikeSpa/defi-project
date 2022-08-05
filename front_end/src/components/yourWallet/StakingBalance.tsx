import { Token } from "../Main"
import { formatUnits } from "@ethersproject/units"
import { BalanceMsg } from "../BalanceMsg"
import { useStakingBalance } from "../../hooks"


export interface WalletBalanceProps {
    token: Token
}


export const StakingBalance = ({ token }: WalletBalanceProps) => {
    const { address } = token
    const stakingBalance = useStakingBalance(address)
    const formattedTokenBalance = stakingBalance ? parseInt(formatUnits(stakingBalance, 16)) / 100 : 0
    console.log(formattedTokenBalance)
    return (<BalanceMsg
        label={formattedTokenBalance + ''}
        amount={formattedTokenBalance} />)
}   