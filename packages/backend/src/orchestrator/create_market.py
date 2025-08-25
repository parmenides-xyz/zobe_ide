#!/usr/bin/env python3
"""Create the first market for AI agent proposals"""

import os
import asyncio
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configuration
SEI_RPC_URL = os.getenv("SEI_RPC_URL", "https://evm-rpc-testnet.sei-apis.com")
MOCK_USDC_ADDRESS = os.getenv("MOCK_USDC_ADDRESS")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")
RESOLVER_ADDRESS = os.getenv("RESOLVER_ADDRESS")
MASTER_PRIVATE_KEY = os.getenv("MASTER_PRIVATE_KEY")

async def create_market():
    """Create a new market for AI agent proposals"""
    
    if not MASTER_PRIVATE_KEY:
        print("ERROR: MASTER_PRIVATE_KEY not set in .env")
        return
    
    if not MARKET_ADDRESS:
        print("ERROR: MARKET_ADDRESS not set in .env")
        return
        
    if not MOCK_USDC_ADDRESS:
        print("ERROR: MOCK_USDC_ADDRESS not set in .env")
        return
    
    # Initialize web3 and account
    w3 = Web3(Web3.HTTPProvider(SEI_RPC_URL))
    account = Account.from_key(MASTER_PRIVATE_KEY)
    
    print(f"Creating market from account: {account.address}")
    balance = w3.eth.get_balance(account.address)
    print(f"Account balance: {w3.from_wei(balance, 'ether')} SEI")
    
    # Market creation ABI
    create_market_abi = [{
        "inputs": [
            {"name": "creator", "type": "address"},
            {"name": "marketToken", "type": "address"},
            {"name": "resolver", "type": "address"},
            {"name": "minDeposit", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "title", "type": "string"}
        ],
        "name": "createMarket",
        "outputs": [{"name": "marketId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }]
    
    # Create market contract instance
    market_contract = w3.eth.contract(address=MARKET_ADDRESS, abi=create_market_abi)
    
    # Market parameters
    creator = account.address
    market_token = MOCK_USDC_ADDRESS
    resolver = RESOLVER_ADDRESS if RESOLVER_ADDRESS != "0x0000000000000000000000000000000000000000" else account.address
    min_deposit = 1000 * 10**18  # 1000 MockUSDC (18 decimals)
    deadline = int((datetime.now() + timedelta(minutes=10)).timestamp())
    title = "AI Agent Launch Market"
    
    print("\nMarket Parameters:")
    print(f"  Creator: {creator}")
    print(f"  Market Token (MockUSDC): {market_token}")
    print(f"  Resolver: {resolver}")
    print(f"  Min Deposit: 1000 tokens")
    print(f"  Deadline: {datetime.fromtimestamp(deadline)} ({deadline})")
    print(f"  Title: {title}")
    
    # Build transaction
    tx = market_contract.functions.createMarket(
        creator,
        market_token,
        resolver,
        min_deposit,
        deadline,
        title
    ).build_transaction({
        'from': account.address,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    
    # Sign and send transaction
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"\nTransaction sent: {tx_hash.hex()}")
    print("Waiting for confirmation...")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print(f"Market created successfully!")
        print(f"Transaction hash: {receipt['transactionHash'].hex()}")
        print(f"Gas used: {receipt['gasUsed']}")
        
        if receipt['logs']:
            # First topic is the event signature, second is the indexed marketId
            market_id = int(receipt['logs'][0]['topics'][1].hex(), 16)
            print(f"Market ID: {market_id}")
            
            # Save market ID to a file for other scripts to use
            market_file = os.path.join(os.path.dirname(__file__), 'latest_market.txt')
            with open(market_file, 'w') as f:
                f.write(str(market_id))
            print(f"✓ Saved market ID to: {market_file}")
            
            # Also show the env var format for backwards compatibility
            print(f"\n(Optional) Add to .env file: MARKET_ID={market_id}")
    else:
        print(f"Transaction failed!")
        print(f"Receipt: {receipt}")

if __name__ == "__main__":
    asyncio.run(create_market())