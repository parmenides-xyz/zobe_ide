// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import "../src/agent/AgentNftV2.sol";
import "../src/agent/AgentTokenV2.sol";
import "../src/agent/AgentVeTokenV2.sol";
import "../src/agent/AgentDAO.sol";
import "../src/agent/AgentFactoryV6.sol";
import "../src/agent/ERC6551Registry.sol";

contract DeployAgentInfrastructure is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        address mockUSDC = vm.envAddress("MOCK_USDC");

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy implementation contracts (these will be cloned by the factory)
        AgentTokenV2 tokenImpl = new AgentTokenV2();
        console.log("AgentTokenV2 implementation deployed at:", address(tokenImpl));

        AgentVeTokenV2 veTokenImpl = new AgentVeTokenV2();
        console.log("AgentVeTokenV2 implementation deployed at:", address(veTokenImpl));

        AgentDAO daoImpl = new AgentDAO();
        console.log("AgentDAO implementation deployed at:", address(daoImpl));

        // 2. Deploy ERC6551Registry (for token-bound accounts)
        ERC6551Registry tbaRegistry = new ERC6551Registry();
        console.log("ERC6551Registry deployed at:", address(tbaRegistry));

        // 3. Deploy AgentNftV2 (upgradeable)
        AgentNftV2 nftImpl = new AgentNftV2();
        bytes memory nftInitData = abi.encodeWithSelector(
            AgentNftV2.initialize.selector,
            deployer // admin
        );
        ERC1967Proxy nftProxy = new ERC1967Proxy(address(nftImpl), nftInitData);
        AgentNftV2 nft = AgentNftV2(address(nftProxy));
        console.log("AgentNftV2 proxy deployed at:", address(nft));

        // 4. Deploy AgentFactoryV6 (upgradeable)
        AgentFactoryV6 factoryImpl = new AgentFactoryV6();
        bytes memory factoryInitData = abi.encodeWithSelector(
            AgentFactoryV6.initialize.selector,
            address(tokenImpl),      // tokenImplementation_
            address(veTokenImpl),    // veTokenImplementation_
            address(daoImpl),        // daoImplementation_
            address(tbaRegistry),    // tbaRegistry_
            mockUSDC,                // assetToken_ (MockUSDC)
            address(nft),            // nft_
            deployer,                // vault_ (deployer will hold NFTs for now)
            0                        // nextId_ (start from 0)
        );
        ERC1967Proxy factoryProxy = new ERC1967Proxy(address(factoryImpl), factoryInitData);
        AgentFactoryV6 factory = AgentFactoryV6(address(factoryProxy));
        console.log("AgentFactoryV6 proxy deployed at:", address(factory));

        // 5. Grant MINTER_ROLE to factory on AgentNftV2
        bytes32 MINTER_ROLE = nft.MINTER_ROLE();
        nft.grantRole(MINTER_ROLE, address(factory));
        console.log("Granted MINTER_ROLE to factory");

        // 6. Set factory parameters
        // maturityDuration: 10 years = 315360000 seconds
        // uniswapRouter: Universal Router address
        // defaultDelegatee: deployer
        // tokenAdmin: deployer
        factory.setParams(
            315360000,                                    // 10 years maturity
            vm.envAddress("ROUTER_ADDRESS"),             // Uniswap router
            deployer,                                     // default delegatee
            deployer                                      // token admin
        );
        console.log("Factory params set");

        // 7. Set default token parameters
        // These are the default params for all agent tokens created by the factory
        factory.setTokenParams(
            1000000000 * 10**18,  // maxSupply: 1B tokens
            800000000 * 10**18,   // lpSupply: 800M for LP
            200000000 * 10**18,   // vaultSupply: 200M for vault
            1000000000 * 10**18,  // maxTokensPerWallet: 1B (no limit)
            1000000000 * 10**18,  // maxTokensPerTxn: 1B (no limit)
            0,                    // botProtectionDurationInSeconds: 0 (no bot protection)
            deployer,             // vault address
            100,                  // projectBuyTaxBasisPoints: 1%
            100,                  // projectSellTaxBasisPoints: 1%
            100,                  // taxSwapThresholdBasisPoints: 1%
            deployer              // projectTaxRecipient
        );
        console.log("Default token params set");

        vm.stopBroadcast();

        console.log("\n=== Deployment Summary ===");
        console.log("AgentTokenV2 implementation:", address(tokenImpl));
        console.log("AgentVeTokenV2 implementation:", address(veTokenImpl));
        console.log("AgentDAO implementation:", address(daoImpl));
        console.log("ERC6551Registry:", address(tbaRegistry));
        console.log("AgentNftV2:", address(nft));
        console.log("AgentFactoryV6:", address(factory));
    }
}
