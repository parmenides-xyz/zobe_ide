// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import {Market} from "../src/Market.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CreateMarket is Script {
    function run() external {
        uint256 deployerPrivateKey = 0x3ba77d3e200829463be3a452927e78e70fdd92444967ac129b8ab92b2c5648b1;
        address marketAddress = 0x016946831AEfe6C3998f28957b902afFBC7FE75e;
        address mockUSDC = 0x80D32F6004f51b65d89abeCf0F744d22F491306f;
        
        vm.startBroadcast(deployerPrivateKey);
        
        Market market = Market(marketAddress);
        
        // Create a market
        uint256 minDeposit = 100 * 10**6; // 100 USDC
        uint256 deadline = block.timestamp + 7 days;
        address resolver = vm.addr(deployerPrivateKey); // Use deployer as resolver for testing
        
        console.log("Creating market...");
        console.log("Min deposit:", minDeposit);
        console.log("Deadline:", deadline);
        console.log("Resolver:", resolver);
        
        market.createMarket(
            vm.addr(deployerPrivateKey), // creator
            mockUSDC, // marketToken
            resolver, // resolver
            minDeposit, // minDeposit
            deadline, // deadline
            "Test Market: Will ETH reach $5000 by end of year?" // title
        );
        
        console.log("Market created successfully!");
        
        vm.stopBroadcast();
    }
}