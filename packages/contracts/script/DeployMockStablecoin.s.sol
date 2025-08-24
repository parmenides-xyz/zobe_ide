// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "../src/MockStablecoin.sol";

contract DeployMockStablecoin is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        MockStablecoin mockUsdc = new MockStablecoin(
            "Mock USDC",
            "mUSDC",
            18, // Changed to 18 decimals to match YES/NO tokens
            deployer // initial owner
        );
        
        console.log("MockStablecoin deployed at:", address(mockUsdc));
        
        vm.stopBroadcast();
        
        return address(mockUsdc);
    }
}