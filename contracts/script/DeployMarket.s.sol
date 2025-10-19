// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/Market.sol";

contract DeployMarket is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        address positionManagerAddress = vm.envAddress("POSITION_MANAGER_ADDRESS");
        address routerAddress = vm.envAddress("ROUTER_ADDRESS");
        address permit2Address = vm.envAddress("PERMIT2_ADDRESS");
        address hookAddress = vm.envAddress("HOOK_ADDRESS");
        
        vm.startBroadcast(deployerPrivateKey);
        
        Market market = new Market(
            deployer, // admin
            positionManagerAddress,
            payable(routerAddress),
            permit2Address,
            hookAddress
        );
        console.log("Market deployed at:", address(market));
        
        vm.stopBroadcast();
        
        return address(market);
    }
}