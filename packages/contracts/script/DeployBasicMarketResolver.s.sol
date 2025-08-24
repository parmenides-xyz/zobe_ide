// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/BasicMarketResolver.sol";

contract DeployBasicMarketResolver is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        BasicMarketResolver resolver = new BasicMarketResolver(
            deployer, // systemAdmin
            deployer  // accountHolder
        );
        console.log("BasicMarketResolver deployed at:", address(resolver));
        
        vm.stopBroadcast();
        
        return address(resolver);
    }
}