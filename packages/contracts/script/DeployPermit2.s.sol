// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "@uniswap/permit2/src/Permit2.sol";

contract DeployPermit2 is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        Permit2 permit2 = new Permit2();
        console.log("Permit2 deployed at:", address(permit2));
        
        vm.stopBroadcast();
        
        return address(permit2);
    }
}