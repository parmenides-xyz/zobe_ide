// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/MarketUtilsSwapHook.sol";

contract InitializeContracts is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address marketAddress = vm.envAddress("MARKET_ADDRESS");
        address hookAddress = vm.envAddress("HOOK_ADDRESS");
        address routerAddress = vm.envAddress("ROUTER_ADDRESS");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Initialize hook with market address
        MarketUtilsSwapHook hook = MarketUtilsSwapHook(hookAddress);
        hook.initialize(marketAddress);
        console.log("Hook initialized with market address:", marketAddress);
        
        // Add router as verified
        hook.addRouter(routerAddress);
        console.log("Router added as verified:", routerAddress);
        
        vm.stopBroadcast();
    }
}