# DeFi Project

- ERC20 Token `ProjectToken`
- Staking contract
- FlashLoan contract 
- Deposit and Withdraw to Aave and Compound


Trying a lot of stuff in DeFi: flash loan, farming, arbitrage, LP, trading, ...
Coding interaction with Aave, Compound, Curve, ...
Later join with futur NFT marketplace project


## TODO

- [ ] refactoring of deploy_staking_contract
- [ ] get second account and differentiate between deployer ans user in tests

### Token
- [x] Token: deployment script
- [x] Token: tests
- [ ] better way of issuing token to stakers

### Staking Contract
- [x] deploy script
- [x] test
- [x] add Aave deposit/withdraw
- [x] test       "
- [x] proxy to deposit on aave or compound, contract that take care of sending token x to one protocol and x to another

### Lending Protocol interaction

- [x] Add Aave interaction
- [x] Aave: deployment script
- [x] Aave: tests
- [x] Add Compound interaction
- [x] C: deployment script
- [x] C: tests
- [x] Lending protocol Interface
- [x] Adapt contract to use several lending protocol
- [ ] security/error handling

### Uniswap

- [x] Create pair PJTK/DAI
- [ ] Do some arbitrage
### Flash Loan
- [x] Proper Flash Loan Contract
- [x] Loan: deployment script
- [x] Loan: tests

### Others
- [ ] Uniswap, Curve
- [ ] DAO
- [x] Make a front end at some point
- [ ] dydx, yearn

