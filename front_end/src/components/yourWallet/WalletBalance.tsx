import { Token } from "../Main"
import { useEthers, useTokenBalance } from "@usedapp/core"
import { formatUnits } from "@ethersproject/units"
import { BalanceMsg } from "../BalanceMsg"
import brownieConfig from "../../brownie-config.json"
import helperConfig from "../../helper-config.json"


export interface WalletBalanceProps {
    token: Token
}

export const WalletBalance = ({ token }: WalletBalanceProps) => {
    const { image, address, name } = token
    const { account } = useEthers()
    const tokenBalance = useTokenBalance(address, account)
    const { chainId } = useEthers()
    const networkName: string = chainId ? helperConfig[chainId] : "dev"
    const decimals = address === brownieConfig["networks"][networkName]["cETH"] ? 8 : 18
    const formattedTokenBalance = tokenBalance ? parseInt(formatUnits(tokenBalance, 0)) / 10 ** decimals : 0
    console.log(formattedTokenBalance)
    return (<BalanceMsg
        label={formattedTokenBalance + ''}
        amount={formattedTokenBalance} />)
}   