import { Token } from "../Main"
import { useEthers, useTokenBalance } from "@usedapp/core"
import { formatUnits } from "@ethersproject/units"
import { BalanceMsg } from "../BalanceMsg"

export interface WalletBalanceProps {
    token: Token
}


export const WalletBalance = ({ token }: WalletBalanceProps) => {
    const { image, address, name } = token
    const { account } = useEthers()
    const tokenBalance = useTokenBalance(address, account)
    const formattedTokenBalance: number = tokenBalance ? parseInt(formatUnits(tokenBalance, 18)) : 0
    return (<BalanceMsg
        label={'Your un-staked ' + name + ' balance:'}
        tokenImgSrc={image}
        amount={formattedTokenBalance} />)
}   