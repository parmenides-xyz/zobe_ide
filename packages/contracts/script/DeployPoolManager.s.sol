// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "@uniswap/v4-core/src/PoolManager.sol";

contract DeployPoolManager is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        PoolManager poolManager = new PoolManager(deployer);
        console.log("PoolManager deployed at:", address(poolManager));
        
        vm.stopBroadcast();
        
        return address(poolManager);
    }
}