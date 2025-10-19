// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/MarketUtilsSwapHook.sol";
import "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import "@uniswap/v4-core/src/libraries/Hooks.sol";
import "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import "./base/Constants.sol";

contract DeployMarketUtilsSwapHook is Script, Constants {
    
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address poolManagerAddress = vm.envAddress("POOL_MANAGER_ADDRESS");
        
        // MarketUtilsSwapHook needs BEFORE_SWAP and AFTER_SWAP flags
        uint160 flags = uint160(
            Hooks.BEFORE_SWAP_FLAG | Hooks.AFTER_SWAP_FLAG
        );
        
        // Get deployer address
        address deployer = vm.addr(deployerPrivateKey);
        
        // Mine a salt that will produce a hook address with the correct flags
        bytes memory constructorArgs = abi.encode(poolManagerAddress, deployer);
        (address hookAddress, bytes32 salt) = HookMiner.find(
            CREATE2_DEPLOYER,
            flags,
            type(MarketUtilsSwapHook).creationCode,
            constructorArgs
        );
        
        console.log("Expected hook address:", hookAddress);
        console.log("Salt found:", uint256(salt));
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy the hook using CREATE2 with deployer as owner
        MarketUtilsSwapHook hook = new MarketUtilsSwapHook{salt: salt}(IPoolManager(poolManagerAddress), deployer);
        require(address(hook) == hookAddress, "Hook address mismatch");
        
        console.log("MarketUtilsSwapHook deployed at:", address(hook));
        console.log("Owner set to:", deployer);
        
        // Add UniversalRouter as verified router
        address routerAddress = vm.envAddress("ROUTER_ADDRESS");
        hook.addRouter(routerAddress);
        console.log("Router added:", routerAddress);
        
        vm.stopBroadcast();
        
        return address(hook);
    }
}