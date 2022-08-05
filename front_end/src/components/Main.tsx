import { useEthers } from "@usedapp/core"
import helperConfig from "../helper-config.json"
import networkMapping from "../chain-info/deployments/map.json"
import { constants } from "ethers"
import brownieConfig from "../brownie-config.json"
import pjtk2 from "../pjtk2.png"
import eth2 from "../eth2.svg"
import dai from "../dai.png"
import link from "../link.svg"
import { YourWallet } from "./yourWallet/YourWallet"
import { StakingContract } from "./stakingContract"
import { Snackbar, Typography, makeStyles, Box } from "@material-ui/core"
import React, { useEffect, useState } from "react"
import Alert from "@material-ui/lab/Alert"




export type Token = {
    image: string
    address: string
    name: string
}
const useStyles = makeStyles((theme) => ({
    title: {
        // color: theme.palette.common.white,
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

    // Our supported token
    const dappTokenAddress: string = chainId ? networkMapping[String(chainId)]["ProjectToken"][0] : constants.AddressZero
    const wethTokenAddress: string = chainId ? brownieConfig["networks"][networkName]["weth_token"] : constants.AddressZero
    const daiTokenAddress: string = chainId ? brownieConfig["networks"][networkName]["fau_token"] : constants.AddressZero
    const cETHTokenAddress: string = chainId ? brownieConfig["networks"][networkName]["cETH"] : constants.AddressZero //not supported in deployed contract on kovan
    const LINKTokenAddress: string = chainId ? brownieConfig["networks"][networkName]["LINK"] : constants.AddressZero //not supported in deployed contract on kovan

    const supportedTokens: Array<Token> = [
        {
            image: pjtk2,
            address: dappTokenAddress,
            name: "PJTK"
        },
        {
            image: eth2,
            address: wethTokenAddress,
            name: "WETH"
        },
        {
            image: dai,
            address: daiTokenAddress,
            name: "DAI"
        },
        {
            image: link,
            address: LINKTokenAddress,
            name: "LINK"
        },
        {
            image: eth2,
            address: cETHTokenAddress,
            name: "cETH"
        },

    ]

    const [showNetworkError, setShowNetworkError] = useState(false)

    const handleCloseNetworkError = (
        event: React.SyntheticEvent | React.MouseEvent,
        reason?: string
    ) => {
        if (reason === "clickaway") {
            return
        }

        showNetworkError && setShowNetworkError(false)
    }

    /**
     * useEthers will return a populated 'error' field when something has gone wrong.
     * We can inspect the name of this error and conditionally show a notification
     * that the user is connected to the wrong network.
     */
    useEffect(() => {
        if (error && error.name === "UnsupportedChainIdError") {
            !showNetworkError && setShowNetworkError(true)
        } else {
            showNetworkError && setShowNetworkError(false)
        }
    }, [error, showNetworkError])

    return (
        <>
            <Typography
                variant="h2"
                component="h1"
                classes={{
                    root: classes.title,
                }}
            >
                Staking Contract
            </Typography>
            <StakingContract supportedTokens={supportedTokens} />
            <YourWallet supportedTokens={supportedTokens} />
            <Box>
                <br></br>
            </Box>

            <Snackbar
                open={showNetworkError}
                autoHideDuration={5000}
                onClose={handleCloseNetworkError}
            >
                <Alert onClose={handleCloseNetworkError} severity="warning">
                    You need to be connected to the Kovan network!
                </Alert>
            </Snackbar>
        </>
    )
}