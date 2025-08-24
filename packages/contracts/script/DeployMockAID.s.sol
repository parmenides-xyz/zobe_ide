// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/MockAID.sol";

contract DeployMockAID is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        MockAID mockAID = new MockAID();
        console.log("MockAID deployed at:", address(mockAID));

        // Mint initial supply to deployer for testing
        mockAID.mint(msg.sender, 10000000 * 10**18); // 10M MockAID
        console.log("Minted 10M MockAID to deployer");

        vm.stopBroadcast();
    }
}