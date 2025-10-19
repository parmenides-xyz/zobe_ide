// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MockAID is ERC20, Ownable {
    constructor() ERC20("Mock AID", "MockAID") Ownable(msg.sender) {}

    // Anyone can mint for testing purposes
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }

    // Owner can mint
    function ownerMint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    // Mint to self
    function mintToSelf(uint256 amount) public {
        _mint(msg.sender, amount);
    }
}