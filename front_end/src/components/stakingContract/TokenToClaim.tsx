import { Token } from "../Main"
import { useContractCall, useEthers } from "@usedapp/core"
import { constants } from "ethers"
import { formatUnits } from "@ethersproject/units"
import { BalanceMsg2 } from "../BalanceMsg2"
import { useTokenToClaim } from "../../hooks"


export interface WalletBalanceProps {
    token: Token
}


export const TokenToClaim = () => {
    // const { address } = token
    const { account } = useEthers()
    const accountAddr: string = account ? account : constants.AddressZero
    const tokenToClaim = useTokenToClaim(accountAddr)
    // const formattedtokenToClaim = tokenToClaim
    const formattedtokenToClaim: number = tokenToClaim ? parseInt(formatUnits(tokenToClaim, 14)) / 10000 : 0
    console.log(formattedtokenToClaim)
    return (<BalanceMsg2
        label={'You currently have ' + formattedtokenToClaim + ' token available on the Staking Contract. Click the button below to claim them:'}
        amount={formattedtokenToClaim} />)
}   