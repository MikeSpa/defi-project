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
    const formattedTokenBalance = tokenBalance ? parseInt(formatUnits(tokenBalance, 17)) / 10 : 0
    console.log(formattedTokenBalance)
    // formattedTokenBalance = 
    return (<BalanceMsg
        label={'Your un-staked ' + name + ' balance:'}
        tokenImgSrc={image}
        amount={formattedTokenBalance} />)
}   