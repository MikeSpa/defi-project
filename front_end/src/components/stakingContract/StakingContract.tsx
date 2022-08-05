import React, { useState } from "react"
import { useEthers } from "@usedapp/core"
import { ConnectionRequiredMsg } from "../ConnectionRequiredMsg"
import { Box, makeStyles, Grid } from "@material-ui/core"
import { Token } from "../Main"
import { ClaimToken } from "./ClaimToken"
import { TokenToClaim } from "./TokenToClaim"


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
            <h2 className={classes.header}>Claim Your Tokens</h2>
            <Box className={classes.box}>
                <div>
                    {isConnected ? (
                        <Grid>
                            <TokenToClaim />
                            <ClaimToken />
                        </Grid>

                    ) : (
                        // <p>you need to connect</p>
                        <ConnectionRequiredMsg />
                    )}
                </div>
            </Box>
        </Box>
    )
}