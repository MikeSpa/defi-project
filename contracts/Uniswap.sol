// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@uniswap/contracts/interfaces/IUniswapV2Factory.sol";
import "@uniswap/contracts/interfaces/IUniswapV2Pair.sol";

// import "../interfaces/IUniswapV2Factory.sol";

contract Uniswap is Ownable {
    IUniswapV2Factory public uniswapV2Factory;
    IERC20 public projectToken;
    IERC20 public daiToken;

    constructor(
        address _uniswapV2Factory,
        address _projectToken,
        address _daiToken
    ) {
        uniswapV2Factory = IUniswapV2Factory(_uniswapV2Factory);
        projectToken = IERC20(_projectToken);
        daiToken = IERC20(_daiToken);
        uniswapV2Factory.createPair(_projectToken, _daiToken);
    }

    // function createPair(address _tokenA, address _tokenB)
    //     external
    //     onlyOwner
    //     returns (address pair)
    // {
    //     uniswapV2Factory.createPair(_tokenA, _tokenB);
    // }
}
