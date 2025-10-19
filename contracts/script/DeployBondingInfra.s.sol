// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/agent/WVIRTUAL.sol";
import "../src/agent/FFactory.sol";
import "../src/agent/FRouter.sol";
import "../src/agent/Bonding.sol";

contract DeployBondingInfra is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        // Get already deployed MockUSDC address from .env
        address mockUSDC = vm.envAddress("MOCK_USDC");
        console.log("Using MockUSDC at:", mockUSDC);

        vm.startBroadcast(deployerPrivateKey);

        // Deploy WVIRTUAL
        WVIRTUAL wvirtual = new WVIRTUAL();
        console.log("WVIRTUAL deployed at:", address(wvirtual));

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

        // Initialize Bonding with Uniswap addresses
        bonding.initialize(
            address(factory),
            address(router),
            payable(address(wvirtual)),
            100 * 10**18,      // assetLaunchFee: 100 MockUSDC
            1 ether,           // virtualLaunchFee: 1 VIRTUAL (not used for now)
            1000000 * 10**18,  // initialSupply: 1M tokens
            100,               // maxTx: 100% (no limit)
            5,                 // graduationSlippage: 5%
            100 ether,         // virtualGradThreshold: 100 VIRTUAL (not used for now)
            100000 * 10**18,   // assetGradThreshold: 100k MockUSDC
            0,                 // uniswapTaxBps: 0% tax post-graduation
            0x7Ae58f10f7849cA6F5fB71b7f45CB416c9204b1e, // Uniswap V2 Factory on Base Sepolia
            0x1689E7B1F10000AE47eBfE339a4f69dECd19F602  // Uniswap V2 Router on Base Sepolia
        );
        console.log("Bonding initialized with Uniswap integration");

        console.log("\n=== Deployment Complete ===");
        console.log("MockUSDC:", mockUSDC);
        console.log("WVIRTUAL:", address(wvirtual));
        console.log("FFactory:", address(factory));
        console.log("FRouter:", address(router));
        console.log("Bonding:", address(bonding));
        console.log("\nSave these addresses to your .env file!");

        vm.stopBroadcast();
    }
}