// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "@uniswap/v4-periphery/src/PositionManager.sol";
import "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import "@uniswap/permit2/src/interfaces/IPermit2.sol";
import "@uniswap/v4-periphery/src/interfaces/IPositionDescriptor.sol";
import "@uniswap/v4-periphery/src/interfaces/external/IWETH9.sol";

contract DeployPositionManager is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address poolManagerAddress = vm.envAddress("POOL_MANAGER_ADDRESS");
        address permit2Address = vm.envAddress("PERMIT2_ADDRESS");
        
        vm.startBroadcast(deployerPrivateKey);
        
        PositionManager positionManager = new PositionManager(
            IPoolManager(poolManagerAddress),
            IPermit2(permit2Address),
            100_000,
            IPositionDescriptor(address(0)), // Can be zero for now
            IWETH9(address(0)) // Can be zero if not using native token
        );
        console.log("PositionManager deployed at:", address(positionManager));
        
        vm.stopBroadcast();
        
        return address(positionManager);
    }
}