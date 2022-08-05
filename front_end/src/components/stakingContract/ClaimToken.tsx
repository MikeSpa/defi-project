import { useState, useEffect } from "react"
import {
    Button,
    CircularProgress,
    Snackbar,
    makeStyles,
} from "@material-ui/core"
import { Token } from "../Main"
import { useClaimToken } from "../../hooks"
import Alert from "@material-ui/lab/Alert"
import { useNotifications } from "@usedapp/core"
import { BalanceMsg } from ".."

export interface UnstakeFormProps {
    token: Token
}

const useStyles = makeStyles((theme) => ({
    contentContainer: {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        gap: theme.spacing(2),
    },
}))

export const ClaimToken = () => {

    const { notifications } = useNotifications()


    const { send: claimTokensSend, state: claimTokensState } =
        useClaimToken()

    const handleUnstakeSubmit = () => {
        return claimTokensSend()
    }

    const [showClaimSucess, setshowClaimSucess] = useState(false)

    const handleCloseSnack = () => {
        showClaimSucess && setshowClaimSucess(false)
    }

    useEffect(() => {
        if (
            notifications.filter(
                (notification) =>
                    notification.type === "transactionSucceed" &&
                    notification.transactionName === "Unstake tokens"
            ).length > 0
        ) {
            !showClaimSucess && setshowClaimSucess(true)
        }
    }, [notifications, showClaimSucess])

    const isMining = claimTokensState.status === "Mining"


    const classes = useStyles()

    return (
        <>
            <div className={classes.contentContainer}>
                <BalanceMsg
                    label={''}
                    amount={0}
                />
                <Button
                    color="primary"
                    variant="contained"
                    size="large"
                    onClick={handleUnstakeSubmit}
                    disabled={isMining}
                >
                    {isMining ? <CircularProgress size={26} /> : `Claim Token`}
                </Button>
            </div>
            <Snackbar
                open={showClaimSucess}
                autoHideDuration={5000}
                onClose={handleCloseSnack}
            >
                <Alert onClose={handleCloseSnack} severity="success">
                    Tokens claimed successfully!
                </Alert>
            </Snackbar>
        </>
    )
}