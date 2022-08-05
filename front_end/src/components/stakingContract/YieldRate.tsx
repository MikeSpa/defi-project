import { Token } from "../Main"
import { formatUnits } from "@ethersproject/units"
import { BalanceMsg2 } from "../BalanceMsg2"
import { useYieldRate } from "../../hooks"


export interface WalletBalanceProps {
    token: Token
}


export const YieldRate = ({ token }: WalletBalanceProps) => {
    const { address } = token
    const yieldRate = useYieldRate(address)
    const formattedYieldRate = yieldRate ? parseInt(formatUnits(yieldRate, 0)) / 10 : 0
    console.log(formattedYieldRate)
    return (<BalanceMsg2
        label={formattedYieldRate + ' %'}
        amount={formattedYieldRate} />)
}   