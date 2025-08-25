#!/usr/bin/env python3
"""Start a swarm of AI proposal agents and traders on Kurtosis"""

import os
import asyncio
import random
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.traders.trader_agent import TraderAgent
from src.traders.proposal_agent import ProposalAgent
from src.traders.allora_personalities import get_trader_personality
from src.agent_token_launcher import AgentTokenLauncher

# Load environment variables
load_dotenv()

# Configuration
SEI_RPC_URL = os.getenv("SEI_RPC_URL", "https://evm-rpc-testnet.sei-apis.com")
MOCK_USDC_ADDRESS = os.getenv("MOCK_USDC_ADDRESS", "0x80D32F6004f51b65d89abeCf0F744d22F491306f")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")
MASTER_PRIVATE_KEY = os.getenv("MASTER_PRIVATE_KEY")
NUM_TRADERS = int(os.getenv("NUM_TRADERS", "20"))
NUM_PROPOSAL_AGENTS = int(os.getenv("NUM_PROPOSAL_AGENTS", "10"))

# Read MARKET_ID from file created by create_market.py
market_file = os.path.join(os.path.dirname(__file__), 'latest_market.txt')
if os.path.exists(market_file):
    with open(market_file, 'r') as f:
        MARKET_ID = int(f.read().strip())
else:
    raise ValueError(f"No market ID file found at {market_file}. Run create_market.py first!")

async def fund_with_gas(w3, master_account, trader_address, amount_ether="0.01", nonce=None):
    """Send gas (SEI) to a trader address"""
    if nonce is None:
        nonce = w3.eth.get_transaction_count(master_account.address)
    
    tx = {
        'from': master_account.address,
        'to': trader_address,
        'value': w3.to_wei(amount_ether, 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    }
    
    signed_tx = master_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash

async def create_trader():
    """Create a single trader with a new wallet and assigned personality"""
    # Generate new account
    account = Account.create()
    
    trader = TraderAgent(
        private_key=account.key.hex(),
        rpc_url=SEI_RPC_URL,
        mock_usdc_address=MOCK_USDC_ADDRESS,
        market_address=MARKET_ADDRESS
    )
    
    # Log the trader's personality
    personality = get_trader_personality(trader.address)
    print(f"  Created trader {trader.address[:8]}... → {personality['name']} ({personality['type']})")
    
    return trader

async def create_proposal_agent():
    """Create a single proposal agent with a new wallet"""
    # Generate new account
    account = Account.create()
    
    agent = ProposalAgent(
        private_key=account.key.hex(),
        rpc_url=SEI_RPC_URL,
        mock_usdc_address=MOCK_USDC_ADDRESS,
        market_address=MARKET_ADDRESS
    )
    
    return agent

async def initialize_agents(agents, master_w3, master_account, agent_type="trader"):
    """Fund agents with gas and get MockUSDC from faucet"""
    print(f"Funding {len(agents)} {agent_type}s with gas...")
    
    # Get starting nonce
    base_nonce = master_w3.eth.get_transaction_count(master_account.address)
    
    # Fund with gas in batches
    batch_size = 10
    nonce_offset = 0
    
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i+batch_size]
        tasks = []
        
        for j, agent in enumerate(batch):
            # Proposal agents need more gas for creating proposals
            gas_amount = "0.5" if agent_type == "proposal" else "0.01"
            # Use sequential nonces to avoid conflicts
            nonce = base_nonce + nonce_offset + j
            task = fund_with_gas(master_w3, master_account, agent.address, gas_amount, nonce)
            tasks.append(task)
            
        # Wait for batch to complete
        try:
            await asyncio.gather(*tasks)
            nonce_offset += len(batch)
            print(f"Successfully funded batch {i//batch_size + 1}")
        except Exception as e:
            print(f"ERROR funding batch: {e}")
            import traceback
            traceback.print_exc()
            # Re-sync nonce on error
            base_nonce = master_w3.eth.get_transaction_count(master_account.address)
            nonce_offset = 0
            raise e  # Don't continue if funding fails!
    
    print(f"Getting MockUSDC from faucet for {agent_type}s...")
    
    # Initialize agents (get MockUSDC)
    initialized = 0
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i+batch_size]
        tasks = [agent.initialize() for agent in batch]
        try:
            await asyncio.gather(*tasks)
            initialized += len(batch)
        except Exception as e:
            print(f"ERROR getting faucet tokens: {e}")
            raise e
    
    print(f"Successfully initialized {initialized} {agent_type}s")

async def launch_proposals(proposal_agents, market_id):
    """Have proposal agents create diverse AI agent proposals"""
    print(f"\nLaunching proposals from {len(proposal_agents)} agents...")
    
    proposal_ids = []
    for i, agent in enumerate(proposal_agents):
        try:
            # Each agent creates one unique proposal
            receipt, proposal_id = await agent.create_proposal(market_id)
            if receipt and receipt['status'] == 1:
                proposal_ids.append(proposal_id)
                print(f"  ProposalAgent {i+1} created proposal ID {proposal_id}")
            else:
                print(f"  ProposalAgent {i+1} transaction failed")
        except Exception as e:
            print(f"  ProposalAgent {i+1} failed: {e}")
    
    print(f"Created {len(proposal_ids)} proposals with IDs: {proposal_ids}")
    return proposal_ids

async def trading_loop(traders, proposal_ids):
    """Main trading loop - traders randomly trade on proposals"""
    print(f"Starting trading activity with {len(traders)} traders on {len(proposal_ids)} proposals...")
    
    market_id = MARKET_ID
    
    # First, have traders deposit to the market (match E2E test amounts)
    print("\nTraders depositing to market...")
    deposit_tasks = []
    for i, trader in enumerate(traders):  # All traders (now 20)
        # First 5 traders deposit 3000 USDC (like Alice in E2E), rest deposit 1500 USDC
        deposit_amount = (3000 if i < 5 else 1500) * 10**18
        deposit_tasks.append(trader.deposit_to_market(market_id, deposit_amount))
    
    # Execute deposits in batches
    for i in range(0, len(deposit_tasks), 10):
        batch = deposit_tasks[i:i+10]
        try:
            await asyncio.gather(*batch)
        except Exception as e:
            print(f"Deposit batch error: {e}")
    
    print("Starting continuous trading...")
    
    # Track trading metrics
    total_trades = 0
    failed_trades = 0
    consecutive_failures = 0
    last_yes_trade_time = {}  # Track last YES trade time per proposal
    
    # Focus on just 2-3 proposals to concentrate liquidity impact
    focus_proposals = proposal_ids[:min(3, len(proposal_ids))]
    print(f"\nFocusing initial trades on proposals: {focus_proposals}")
    
    # Initial trades to establish observations (buy YES tokens like E2E test)
    print("Executing initial YES token purchases to establish price observations...")
    for proposal_id in focus_proposals:
        if traders:
            trader = traders[0]
            try:
                # Get proposal data
                proposal_data = await trader.get_proposal_data(proposal_id)
                
                # Claim vUSD
                await trader.claim_vusd(proposal_id)
                vusd_address = proposal_data['vUSD']
                
                # Buy YES tokens with 100 vUSD (like E2E test)
                # Note: execute_swap will handle approval to UniversalRouter internally
                buy_amount = 10 * 10**18  # Small amount for 333 token pools
                print(f"  Buying YES tokens with {buy_amount/10**18:.0f} vUSD for proposal {proposal_id}")
                
                await trader.execute_swap(
                    pool_key=proposal_data['yesPoolKey'],
                    token_in=proposal_data['vUSD'],
                    token_out=proposal_data['yesToken'],
                    amount_in=buy_amount,
                    is_selling_decision_token=False
                )
                
                last_yes_trade_time[proposal_id] = asyncio.get_event_loop().time()
                total_trades += 1
                print(f"  Initial YES purchase completed for proposal {proposal_id}")
            except Exception as e:
                print(f"Initial trade error: {e}")
    
    print("\nWaiting 3 seconds for TWAP window...")
    await asyncio.sleep(3)
    
    print("Executing large follow-up trades to trigger TWAP and move price...")
    for i, proposal_id in enumerate(focus_proposals):
        if traders and len(traders) > i:
            trader = traders[i]
            try:
                # Get proposal data for direct YES pool trading with larger amounts
                proposal_data = await trader.get_proposal_data(proposal_id)
                
                # Claim more vUSD for larger trade
                await trader.claim_vusd(proposal_id)
                vusd_address = proposal_data['vUSD']
                
                # No need for Permit2 approval - minting uses direct approval below
                
                # Mint a large amount of YES/NO tokens
                large_mint = 30 * 10**18  # Small amount for 333 token pools
                print(f"  Minting {large_mint/10**18:.0f} vUSD worth of YES/NO for proposal {proposal_id}")
                
                # Approve vUSD to Market contract
                from web3 import Web3
                approve_abi = [{
                    "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
                vusd_contract = trader.w3.eth.contract(address=Web3.to_checksum_address(vusd_address), abi=approve_abi)
                tx = vusd_contract.functions.approve(trader.market_address, 2**256 - 1).build_transaction({
                    'from': trader.address,
                    'gas': 100000,
                    'gasPrice': trader.w3.eth.gas_price,
                    'nonce': trader.get_nonce(),
                })
                signed_tx = trader.account.sign_transaction(tx)
                trader.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                trader.increment_nonce()
                
                await trader.mint_yes_no(proposal_id, large_mint)
                
                # Buy YES tokens with vUSD to directly push YES price up (like E2E test)
                # First need to get more vUSD to buy with
                buy_amount = 20 * 10**18  # Small amount for 333 token pools
                print(f"  Buying YES tokens with {buy_amount/10**18:.0f} vUSD to drive up price for proposal {proposal_id}")
                
                # Buy YES tokens (vUSD -> YES)
                # Note: execute_swap will handle approval to UniversalRouter internally
                await trader.execute_swap(
                    pool_key=proposal_data['yesPoolKey'],
                    token_in=proposal_data['vUSD'],
                    token_out=proposal_data['yesToken'],
                    amount_in=buy_amount,
                    is_selling_decision_token=False  # We're buying decision tokens
                )
                total_trades += 1
                print(f"  Large trade completed for proposal {proposal_id}")
            except Exception as e:
                print(f"Follow-up trade error: {e}")
    
    # Check if TWAP is now active
    market_max = traders[0].check_market_max(market_id)
    if market_max['proposalId'] > 0:
        print(f"\n✓ TWAP ACTIVATED! MarketMax: Proposal {market_max['proposalId']} with price {market_max['yesPrice']}")
    else:
        print(f"\n✗ TWAP still not active. MarketMax still 0.")
    
    print("\nContinuing with regular trading...")
    
    while True:
        # Check if market is still open
        if not traders[0].check_market_status(market_id):
            print(f"\n{'='*50}")
            print(f"Market {market_id} deadline has passed. Graduating market...")
            
            # Graduate the market to finalize the winner
            try:
                await traders[0].graduate_market(market_id)
                print("Market graduated successfully!")
            except Exception as e:
                if "already graduated" in str(e).lower() or "proposal_accepted" in str(e).lower():
                    print("Market already graduated")
                else:
                    print(f"Failed to graduate market: {e}")
            
            print(f"Final stats:")
            print(f"  Total successful trades: {total_trades}")
            print(f"  Failed trades: {failed_trades}")
            
            # Now check the winning proposal after graduation
            winning_proposal = traders[0].check_winning_proposal(market_id)
            print(f"\nWinning proposal: {winning_proposal}")
            
            if winning_proposal > 0:
                print(f"Market graduated with winning proposal: {winning_proposal}")
                
                # Launch agent token
                print("\n🚀 Launching agent token...")
                launcher = AgentTokenLauncher()
                launch_result = await launcher.launch_agent_token(market_id)
                
                if launch_result:
                    print(f"✅ Agent token launched successfully!")
                    print(f"  Token: {launch_result['agent_name']} ({launch_result['ticker']})")
                    print(f"  Transaction: {launch_result['tx_hash']}")
                else:
                    print("❌ Failed to launch agent token")
            break
        
        # Pick random trader and proposal (70% chance to pick focus proposals)
        trader = random.choice(traders)
        if random.random() < 0.7 and focus_proposals:
            proposal_id = random.choice(focus_proposals)
        else:
            proposal_id = random.choice(proposal_ids)
        
        # Execute trade
        try:
            await trader.trade(proposal_id, market_id)
            total_trades += 1
            consecutive_failures = 0  # Reset on success
            
            # Check marketMax every 10 trades
            if total_trades % 10 == 0:
                market_max = traders[0].check_market_max(market_id)
                if market_max['proposalId'] > 0:
                    print(f"  MarketMax updated: Proposal {market_max['proposalId']} with price {market_max['yesPrice']}")
                else:
                    print(f"  MarketMax still 0 after {total_trades} trades")
        except Exception as e:
            print(f"Trade error: {e}")
            failed_trades += 1
            consecutive_failures += 1
        
        # Check if we should graduate the market
        if consecutive_failures > 20 or (total_trades > 100 and failed_trades > total_trades * 0.5):
            print(f"\n{'='*50}")
            print(f"Trading appears to be exhausted:")
            print(f"  Total trades: {total_trades}")
            print(f"  Failed trades: {failed_trades}")
            print(f"  Consecutive failures: {consecutive_failures}")
            
            # Check collective balance
            total_balance = 0
            for t in traders:
                balance = t.get_balance()
                total_balance += balance
            
            readable_balance = total_balance / 10**18  # Assuming 18 decimals
            print(f"  Total USDC balance across all traders: {readable_balance:.2f}")
            
            if consecutive_failures > 20 or readable_balance < 100:
                print(f"\nAttempting to graduate market {market_id}...")
                try:
                    # Use first trader to graduate the market
                    await traders[0].graduate_market(market_id)
                    print("Market graduated successfully! Trading ended.")
                    
                    # Verify agent token launch
                    winning_proposal = traders[0].check_winning_proposal(market_id)
                    print(f"\nWinning proposal: {winning_proposal}")
                    
                    # Launch agent token
                    if winning_proposal > 0:
                        print(f"Market graduated with winning proposal: {winning_proposal}")
                        
                        print("\nLaunching agent token...")
                        launcher = AgentTokenLauncher()
                        launch_result = await launcher.launch_agent_token(market_id)
                        
                        if launch_result:
                            print(f"Agent token launched successfully!")
                            print(f"  Token: {launch_result['agent_name']} ({launch_result['ticker']})")
                            print(f"  Transaction: {launch_result['tx_hash']}")
                        else:
                            print("Failed to launch agent token")
                    break
                except Exception as e:
                    print(f"Failed to graduate market: {e}")
                    if "deadline not yet reached" in str(e):
                        print("Market deadline hasn't passed yet. Waiting...")
                        await asyncio.sleep(5)
                    else:
                        break
        
        # Wait a bit before next trade (10 trades per second)
        await asyncio.sleep(0.1)

async def main():
    """Main function to start the swarm"""
    print("Starting Kurtosis AI Agent Swarm")
    print("="*50)
    
    # Show AI market conditions that will influence trading
    print("\n📊 AI Market Analysis (from Allora Network):")
    from src.traders.allora_personalities import get_ai_token_predictions
    try:
        ai_predictions = await get_ai_token_predictions()
        for token, price in ai_predictions.items():
            token_name = token.split('/')[0]
            print(f"  {token_name}: ${price:.2f}")
        avg_price = sum(ai_predictions.values()) / len(ai_predictions) if ai_predictions else 0
        market_condition = 'Strong' if avg_price > 55 else 'Weak' if avg_price < 45 else 'Neutral'
        print(f"  Average: ${avg_price:.2f} ({market_condition} market)")
        print(f"  → Traders will be {'bullish' if avg_price > 55 else 'bearish' if avg_price < 45 else 'mixed'} on AI agent proposals")
    except Exception as e:
        print(f"  Error fetching AI predictions: {e}")
        print("  Traders will use default strategies")
    print("="*50)
    
    # Initialize master wallet
    if not MASTER_PRIVATE_KEY:
        print("ERROR: MASTER_PRIVATE_KEY not set in .env")
        return
        
    master_w3 = Web3(Web3.HTTPProvider(SEI_RPC_URL))
    master_account = Account.from_key(MASTER_PRIVATE_KEY)
    
    print(f"\nMaster wallet: {master_account.address}")
    balance = master_w3.eth.get_balance(master_account.address)
    print(f"Master balance: {master_w3.from_wei(balance, 'ether')} SEI")
    
    # Phase 1: Create Proposal Agents
    print(f"\nPhase 1: Creating {NUM_PROPOSAL_AGENTS} Proposal Agents...")
    proposal_agents = []
    for i in range(NUM_PROPOSAL_AGENTS):
        agent = await create_proposal_agent()
        proposal_agents.append(agent)
        print(f"  Created ProposalAgent {i+1}: {agent.address[:8]}...")
    
    # Initialize proposal agents
    await initialize_agents(proposal_agents, master_w3, master_account, "proposal")
    
    # Phase 2: Launch Proposals
    print(f"\nPhase 2: Launching AI Agent Proposals...")
    proposal_ids = await launch_proposals(proposal_agents, MARKET_ID)
    
    if not proposal_ids:
        print("No proposals created. Check market status and configuration.")
        return
    
    # Phase 3: Create Trading Agents
    print(f"\nPhase 3: Creating {NUM_TRADERS} Trading Agents with Diverse Personalities...")
    traders = []
    personality_counts = {}
    
    for i in range(NUM_TRADERS):
        trader = await create_trader()
        traders.append(trader)
        
        # Track personality distribution
        personality = get_trader_personality(trader.address)
        personality_key = personality['name']
        personality_counts[personality_key] = personality_counts.get(personality_key, 0) + 1
        
        if i % 100 == 0 and i > 0:
            print(f"  Created {i} traders...")
    
    # Show personality distribution
    print(f"\n📊 Trader Personality Distribution:")
    for name, count in sorted(personality_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {count} trader{'s' if count > 1 else ''}")
    
    # Initialize all traders
    await initialize_agents(traders, master_w3, master_account, "trader")
    
    # Phase 4: Start Trading
    print(f"\nPhase 4: Starting Trading Activity...")
    print(f"  Market ID: {MARKET_ID}")
    print(f"  Active Proposals: {len(proposal_ids)}")
    print(f"  Active Traders: {len(traders)}")
    print("="*50)
    
    # Start trading
    await trading_loop(traders, proposal_ids)

if __name__ == "__main__":
    asyncio.run(main())