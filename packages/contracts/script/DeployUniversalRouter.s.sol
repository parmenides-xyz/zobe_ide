// SPDX-License-Identifier: All Rights Reserved
pragma solidity ^0.8.26;

import "forge-std/Script.sol";
import "@uniswap/universal-router/contracts/UniversalRouter.sol";
import "@uniswap/universal-router/contracts/types/RouterParameters.sol";

contract DeployUniversalRouter is Script {
    function run() external returns (address) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address permit2Address = vm.envAddress("PERMIT2_ADDRESS");
        address poolManagerAddress = vm.envAddress("POOL_MANAGER_ADDRESS");
        address positionManagerAddress = vm.envAddress("POSITION_MANAGER_ADDRESS");
        address weth9Address = vm.envOr("WETH9_ADDRESS", address(0));
        
        vm.startBroadcast(deployerPrivateKey);
        
        RouterParameters memory params = RouterParameters({
            permit2: permit2Address,
            weth9: weth9Address,
            v2Factory: address(0),
            v3Factory: address(0),
            pairInitCodeHash: bytes32(0),
            poolInitCodeHash: bytes32(0),
            v4PoolManager: poolManagerAddress,
            v3NFTPositionManager: address(0),
            v4PositionManager: positionManagerAddress
        });
        
        UniversalRouter router = new UniversalRouter(params);
        console.log("UniversalRouter deployed at:", address(router));
        
        vm.stopBroadcast();
        
        return address(router);
    }
}