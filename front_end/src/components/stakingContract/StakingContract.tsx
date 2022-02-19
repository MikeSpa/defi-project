import React, { useState } from "react"
import { useEthers } from "@usedapp/core"
import { TabContext, TabList, TabPanel } from "@material-ui/lab"
import { ConnectionRequiredMsg } from "../ConnectionRequiredMsg"
import { Tab, Box, makeStyles } from "@material-ui/core"
import { Token } from "../Main"
import { Unstake } from "./Unstake"

interface StakingContractProps {
    supportedTokens: Array<Token>
}

const useStyles = makeStyles((theme) => ({
    tabContent: {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: theme.spacing(4),
    },
    box: {
        backgroundColor: "white",
        borderRadius: "25px",
        margin: `${theme.spacing(4)}px 0`,
        padding: theme.spacing(2),
    },
    header: {
    }
}))


export const StakingContract = ({ supportedTokens, }: StakingContractProps) => {
    const classes = useStyles()
    const [selectedTokenIndex, setSelectedTokenIndex] = useState<number>(0)

    const handleChange = (event: React.ChangeEvent<{}>, newValue: string) => {
        setSelectedTokenIndex(parseInt(newValue))
    }

    const { account } = useEthers()

    const isConnected = account !== undefined

    return (
        <Box>
            <h2 className={classes.header}>The Stacking Contract</h2>
            <Box className={classes.box}>
                <div>
                    {isConnected ? (
                        <TabContext value={selectedTokenIndex.toString()}>
                            <TabList onChange={handleChange} aria-label="stake form tabs">
                                {supportedTokens.map((token, index) => {
                                    return (
                                        <Tab
                                            label={token.name}
                                            value={index.toString()}
                                            key={index}
                                        />
                                    )
                                })}
                            </TabList>
                            {supportedTokens.map((token, index) => {
                                return (
                                    <TabPanel value={index.toString()} key={index}>
                                        <Unstake token={token} />
                                    </TabPanel>
                                )
                            })}
                        </TabContext>
                    ) : (
                        // <p>you need to connect</p>
                        <ConnectionRequiredMsg />
                    )}
                </div>
            </Box>
        </Box>
    )
}