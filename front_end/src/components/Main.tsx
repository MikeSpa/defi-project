import { useEthers } from "@usedapp/core"
import helperConfig from "../helper-config.json"
import networkMapping from "../chain-info/deployments/map.json"
import { constants } from "ethers"
import brownieConfig from "../brownie-config.json"
import pjtk from "../pjtk.png"
import eth from "../eth.png"
import dai from "../dai.png"
import { YourWallet } from "./yourWallet/YourWallet"
import { makeStyles } from "@material-ui/core"
export type Token = {
    image: string
    address: string
    name: string
}
const useStyles = makeStyles((theme) => ({
    title: {
        color: theme.palette.common.white,
        textAlign: "center",
        padding: theme.spacing(4)
    }
}))

export const Main = () => {

    const classes = useStyles()

    const { chainId, error } = useEthers()
    const networkName: string = chainId ? helperConfig[chainId] : "dev"
    console.log(chainId)
    console.log(networkName)

    const dappTokenAddress: string = chainId ? networkMapping[String(chainId)]["ProjectToken"][0] : constants.AddressZero
    const wethTokenAddress: string = chainId ? brownieConfig["networks"][networkName]["weth_token"] : constants.AddressZero
    const daiTokenAddress: string = chainId ? brownieConfig["networks"][networkName]["dai_token"] : constants.AddressZero

    const supportedTokens: Array<Token> = [
        {
            image: pjtk,//TODO add image
            address: dappTokenAddress,
            name: "PJTK"
        },
        {
            image: eth,
            address: wethTokenAddress,
            name: "WETH"
        },
        {
            image: dai,
            address: daiTokenAddress,
            name: "DAI"
        }
    ]



    return (<>
        <h1 className={classes.title}>Project Token</h1>
        <YourWallet supportedTokens={supportedTokens} />
    </>)
}