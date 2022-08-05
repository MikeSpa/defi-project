import { Token } from "../Main"
import { Box, Table, TableBody, TableHead, TableRow, Paper, TableCell, TableContainer, makeStyles } from "@material-ui/core"
import { WalletBalance } from "./WalletBalance"
import { StakingBalance } from "./StakingBalance"
import { StakeForm } from "./StakeForm"
import { ConnectionRequiredMsg } from "../ConnectionRequiredMsg"
import { useEthers } from "@usedapp/core"

import { YieldRate, Unstake } from "../stakingContract"

import { styled } from '@material-ui/core';

interface YourWalletProps {
    supportedTokens: Array<Token>
}


const useStyles = makeStyles((theme) => ({
    box: {
        backgroundColor: "white",
        borderRadius: "25px"
    },
    header: {
    },
    tokenImg: {
        width: "30px",
        height: "32px"
    },
    tokenName: {
        alignContent: "middle",
    },
}))

const StyledTableCell = styled(TableCell)(({ theme }) => ({
    // [`&.${head}`]: {
    backgroundColor: theme.palette.common.black,
    color: theme.palette.common.white,
    // },
    // [`&.${body}`]: {
    fontSize: 18,
    // },
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
    '&:nth-of-type(odd)': {
        backgroundColor: theme.palette.action.hover,
    },
    // hide last border
    '&:last-child td, &:last-child th': {
        border: 0,
    },
}));


export const YourWallet = ({ supportedTokens }: YourWalletProps) => {

    const { account } = useEthers()
    const isConnected = account !== undefined


    const classes = useStyles()

    return (
        <Box sx={{ width: '115%' }}>
            <h2 className={classes.header}>Your Assets</h2>
            <Box className={classes.box}>
                <div>
                    {isConnected ? (
                        <TableContainer component={Paper}>
                            <Table >
                                <TableHead>
                                    <TableRow >
                                        <StyledTableCell align="center">Token</StyledTableCell>
                                        <StyledTableCell align="center">Balance</StyledTableCell>
                                        <StyledTableCell align="center">Staked</StyledTableCell>
                                        <StyledTableCell align="center">APY</StyledTableCell>
                                        <StyledTableCell align="center">Stake more!</StyledTableCell>
                                        <StyledTableCell align="center">Unstake</StyledTableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {supportedTokens.map((token, index) => (
                                        <StyledTableRow
                                            key={token.name}
                                        >
                                            <TableCell vertical-align="middle" align="center">
                                                {<div ><p className={classes.tokenName} >{token.name}</p><img className={classes.tokenImg} src={token.image} alt="token logo" /></div>}
                                            </TableCell>
                                            <TableCell align="center">{<WalletBalance token={token} />}</TableCell>
                                            <TableCell align="center">{<StakingBalance token={token} />}</TableCell>
                                            <TableCell align="center">{<YieldRate token={token} />}</TableCell>
                                            <TableCell align="center">{<StakeForm token={token} />}</TableCell>
                                            <TableCell align="center">{<Unstake token={token} />}</TableCell>
                                        </StyledTableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )
                        : (
                            <ConnectionRequiredMsg />
                        )}
                </div>
            </Box>
        </Box>)
}