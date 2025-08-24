// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import {PoolSwapTest} from "@uniswap/v4-core/src/test/PoolSwapTest.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";

contract DeployPoolSwap is Script {
    function run() external {
        uint256 deployerPrivateKey = 0x3ba77d3e200829463be3a452927e78e70fdd92444967ac129b8ab92b2c5648b1;
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy PoolSwapTest with the PoolManager address
        PoolSwapTest swapTest = new PoolSwapTest(IPoolManager(0x046f421FE91C0BacC045406d5A772a1a7b22299b));
        
        console.log("Deployed PoolSwap at:", address(swapTest));
        console.log("Use this address in Python scripts as the swap router");
        
        vm.stopBroadcast();
    }
}