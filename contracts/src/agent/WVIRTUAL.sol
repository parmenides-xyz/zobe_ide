// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract WVIRTUAL is ERC20 {
    constructor() ERC20("Wrapped VIRTUAL", "WVIRTUAL") {}

    receive() external payable {
        deposit();
    }

    function deposit() public payable {
        require(msg.value > 0, "Must send VIRTUAL to wrap");
        _mint(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) public {

        require(balanceOf(msg.sender) >= amount, "Insufficient WVIRTUAL balance");

        _burn(msg.sender, amount);

        // payable(msg.sender).transfer(amount);
        (bool success, ) = payable(msg.sender).call{value: amount}("");

        // if it is not success, throw error
        require(success, "Transfer failed!");
    }
}