import { Token } from "../Main"
import { formatUnits } from "@ethersproject/units"
import { BalanceMsg2 } from "../BalanceMsg2"
import { useStakingBalance } from "../../hooks"


export interface WalletBalanceProps {
    token: Token
}


export const StakingBalance = ({ token }: WalletBalanceProps) => {
    const { address } = token
    const stakingBalance = useStakingBalance(address)
    const formattedTokenBalance = stakingBalance ? parseInt(formatUnits(stakingBalance, 16)) / 100 : 0
    console.log(formattedTokenBalance)
    return (<BalanceMsg2
        label={formattedTokenBalance + ''}
        amount={formattedTokenBalance} />)
}   