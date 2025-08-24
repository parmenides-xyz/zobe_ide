// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/agent/AgentTokenFactory.sol";

contract DeployAgentTokenFactory is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get deployed contract addresses from environment
        address marketAddress = vm.envAddress("MARKET_ADDRESS");
        address baseCurrencyAddress = vm.envAddress("BASE_CURRENCY_ADDRESS"); // USDC or native token
        
        vm.startBroadcast(deployerPrivateKey);
        
        AgentTokenFactory factory = new AgentTokenFactory(
            marketAddress,
            baseCurrencyAddress
        );
        
        console.log("AgentTokenFactory deployed at:", address(factory));
        
        vm.stopBroadcast();
    }
}