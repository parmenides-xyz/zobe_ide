// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/MockAID.sol";
import "../src/agent/WSEI.sol";
import "../src/agent/FFactory.sol";
import "../src/agent/FRouter.sol";
import "../src/agent/Bonding.sol";

contract DeployBondingInfra is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);

        // Deploy MockAID first
        MockAID mockAID = new MockAID();
        console.log("MockAID deployed at:", address(mockAID));
        
        // Mint initial supply to deployer
        mockAID.mint(deployer, 10000000 * 10**18); // 10M MockAID
        console.log("Minted 10M MockAID to deployer");

        // Deploy WSEI (required by Bonding even if we use MockAID)
        WSEI wsei = new WSEI();
        console.log("WSEI deployed at:", address(wsei));

        // Deploy FFactory
        FFactory factory = new FFactory();
        console.log("FFactory deployed at:", address(factory));

        // Deploy FRouter
        FRouter router = new FRouter();
        console.log("FRouter deployed at:", address(router));

        // Deploy Bonding
        Bonding bonding = new Bonding();
        console.log("Bonding deployed at:", address(bonding));

        // Initialize FFactory with 0% taxes
        factory.initialize(
            deployer,  // taxVault (deployer address, taxes are 0 anyway)
            0,          // buyTax: 0%
            0,          // sellTax: 0%
            3           // multiplier: 3x for reduced volatility
        );
        console.log("FFactory initialized with 0% taxes");

        // Grant ADMIN_ROLE to deployer first
        bytes32 ADMIN_ROLE = keccak256("ADMIN_ROLE");
        factory.grantRole(ADMIN_ROLE, deployer);
        console.log("ADMIN_ROLE granted to deployer");

        // Set router in factory
        factory.setRouter(address(router));
        console.log("Router set in FFactory");

        // Grant CREATOR_ROLE to Bonding contract
        bytes32 CREATOR_ROLE = keccak256("CREATOR_ROLE");
        factory.grantRole(CREATOR_ROLE, address(bonding));
        console.log("CREATOR_ROLE granted to Bonding");

        // Initialize FRouter
        router.initialize(address(factory));
        console.log("FRouter initialized");

        // Grant ADMIN_ROLE to deployer for router
        router.grantRole(ADMIN_ROLE, deployer);
        console.log("ADMIN_ROLE granted to deployer for router");

        // Grant EXECUTOR_ROLE to Bonding contract
        bytes32 EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
        router.grantRole(EXECUTOR_ROLE, address(bonding));
        console.log("EXECUTOR_ROLE granted to Bonding");

        // Initialize Bonding with DragonSwap addresses
        bonding.initialize(
            address(factory),
            address(router),
            payable(address(wsei)),
            100 * 10**18,      // assetLaunchFee: 100 MockAID
            1 ether,           // seiLaunchFee: 1 SEI (not used)
            1000000 * 10**18,  // initialSupply: 1M tokens
            100,               // maxTx: 100% (no limit)
            5,                 // graduationSlippage: 5%
            100 ether,         // seiGradThreshold: 100 SEI (not used)
            100000 * 10**18,   // assetGradThreshold: 100k MockAID
            0,                 // dragonswapTaxBps: 0% tax post-graduation
            0xeE6Ad607238f8d2C63767245d78520F06c303D31, // DragonSwap Factory on Sei testnet
            0x527b42CA5e11370259EcaE68561C14dA415477C8  // DragonSwap Router on Sei testnet
        );
        console.log("Bonding initialized with DragonSwap integration");

        console.log("\n=== Deployment Complete ===");
        console.log("MockAID:", address(mockAID));
        console.log("WSEI:", address(wsei));
        console.log("FFactory:", address(factory));
        console.log("FRouter:", address(router));
        console.log("Bonding:", address(bonding));
        console.log("\nSave these addresses to your .env file!");

        vm.stopBroadcast();
    }
}