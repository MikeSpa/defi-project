import { useEthers } from "@usedapp/core"
import {
    Button,
    makeStyles,
    AppBar,
    Toolbar,
    Typography,
} from "@material-ui/core"

const useStyles = makeStyles((theme) => ({
    // container: {
    //     padding: theme.spacing(4),
    //     display: "flex",
    //     justifyContent: "flex-end",
    //     gap: theme.spacing(1),
    // },
    header: {
        backgroundColor: "#400C88",
        // width: "max-content"
    },
    logo: {
        fontFamily: "Work Sans, sans-serif",
        fontWeight: 600,
        color: "#FFFEFE",
        textAlign: "left",
    },
    wallet: {
        fontFamily: "Work Sans, sans-serif",
        fontWeight: 600,
        color: "#FFFEFE",
        textAlign: "right",
    },
    menu: {
        fontFamily: "Work Sans, sans-serif",
        fontWeight: 600,
        color: "#FFFEFE",
        textAlign: "center",
    },
}))

const headersData = [
    {
        label: "Staking",
        href: "/staking",
    },
    {
        label: "Flash Loans",
        href: "/flash-loan",
    },
    {
        label: "NFT",
        href: "/nft",
    },

    {
        label: "My Account",
        href: "/account",
    },

];

export const Header = () => {
    const classes = useStyles()
    const { account, activateBrowserWallet, deactivate } = useEthers()

    const isConnected = account !== undefined

    const displayDesktop = () => {
        return (
            <Toolbar>
                {DeFiProjectLogo}
                {getMenuButtons()}
                {getWallet()}
            </Toolbar >
        );
    };

    const DeFiProjectLogo = (
        <Typography variant="h6" component="h1" className={classes.logo}>
            DeFi Project
        </Typography>
    );

    const getMenuButtons = () => {
        return headersData.map(({ label, href }) => {
            return (
                <div className={classes.menu}>
                    <Button
                        {...{
                            key: label,
                            color: "inherit",
                            to: href
                        }}
                    >
                        {label}
                    </Button>
                </div>

            );
        });
    };

    const getWallet = () => {
        return (
            <div className={classes.wallet}>
                {isConnected ?//Acount connect/disconnect
                    (<Button color="primary" variant="contained"
                        onClick={deactivate}>
                        Disconnect
                    </Button>) :
                    (<Button color="primary" variant="contained"
                        onClick={() => activateBrowserWallet()}>
                        Connect
                    </Button>)
                }
            </div>
        )
    }

    return (
        <header>
            <AppBar className={classes.header}>{displayDesktop()}</AppBar>
        </header>
    );

    // return (
    //     <div className={classes.container}>
    //         <div>

    //             {isConnected ?//Acount connect/disconnect
    //                 (<Button color="primary" variant="contained"
    //                     onClick={deactivate}>
    //                     Disconnect
    //                 </Button>) :
    //                 (<Button color="primary" variant="contained"
    //                     onClick={() => activateBrowserWallet()}>
    //                     Connect
    //                 </Button>)
    //             }
    //         </div>
    //     </div>
    // )
}

