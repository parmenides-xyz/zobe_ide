"""
Agent Token Launcher via Bonding Contracts
Launches agent tokens when markets graduate
"""
import os
import json
from web3 import Web3
from eth_account import Account
from typing import Dict, Optional, Tuple
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Contract ABIs
MARKET_ABI = json.loads('''[
    {"inputs":[{"name":"marketId","type":"uint256"}],"name":"acceptedProposals","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"proposalId","type":"uint256"}],"name":"proposals","outputs":[{"name":"id","type":"uint256"},{"name":"marketId","type":"uint256"},{"name":"proposalId","type":"uint256"},{"name":"proposer","type":"address"},{"name":"vUSD","type":"address"},{"name":"yesToken","type":"address"},{"name":"noToken","type":"address"},{"name":"yesPoolKey","type":"tuple","components":[{"name":"currency0","type":"address"},{"name":"currency1","type":"address"},{"name":"fee","type":"uint24"},{"name":"tickSpacing","type":"int24"},{"name":"hooks","type":"address"}]},{"name":"noPoolKey","type":"tuple","components":[{"name":"currency0","type":"address"},{"name":"currency1","type":"address"},{"name":"fee","type":"uint24"},{"name":"tickSpacing","type":"int24"},{"name":"hooks","type":"address"}]},{"name":"amount","type":"uint256"},{"name":"liquidity","type":"uint256"},{"name":"lowerTick","type":"int24"},{"name":"upperTick","type":"int24"},{"name":"context","type":"string"}],"stateMutability":"view","type":"function"}
]''')

BONDING_ABI = json.loads('''[
    {"inputs":[{"name":"_name","type":"string"},{"name":"_ticker","type":"string"},{"name":"purchaseAmount","type":"uint256"},{"name":"assetToken","type":"address"}],"name":"launchWithAsset","outputs":[{"name":"","type":"address"},{"name":"","type":"address"},{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]''')

MOCK_AID_ABI = json.loads('''[
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"}
]''')

class AgentTokenLauncher:
    def __init__(self, private_key: str = None):
        """Initialize the agent token launcher"""
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('SEI_RPC_URL')))
        
        # Use provided private key or default to master key
        self.private_key = private_key or os.getenv('MASTER_PRIVATE_KEY')
        self.account = Account.from_key(self.private_key)
        
        # Load contract addresses
        self.market_address = Web3.to_checksum_address(os.getenv('MARKET_ADDRESS'))
        self.bonding_address = Web3.to_checksum_address(os.getenv('BONDING_ADDRESS'))
        self.mock_aid_address = Web3.to_checksum_address(os.getenv('MOCK_AID_ADDRESS'))
        
        # Initialize contracts
        self.market = self.w3.eth.contract(address=self.market_address, abi=MARKET_ABI)
        self.bonding = self.w3.eth.contract(address=self.bonding_address, abi=BONDING_ABI)
        self.mock_aid = self.w3.eth.contract(address=self.mock_aid_address, abi=MOCK_AID_ABI)
        
        # Launch configuration
        self.launch_fee = Web3.to_wei(100, 'ether')  # 100 MockAID
        self.initial_purchase = Web3.to_wei(10, 'ether')  # 10 MockAID initial purchase
        
    def get_winning_proposal(self, market_id: int) -> Optional[Dict]:
        """Get the winning proposal for a graduated market"""
        try:
            # Get accepted proposal ID
            proposal_id = self.market.functions.acceptedProposals(market_id).call()
            
            if proposal_id == 0:
                print(f"No accepted proposal for market {market_id}")
                return None
            
            # Try to decode proposal directly, fall back to raw call if ABI fails
            try:
                proposal = self.market.functions.proposals(proposal_id).call()
                context = proposal[13]  # context is at index 13
            except Exception:
                # Fall back to raw call and manual parsing
                data = self.market.encodeABI(fn_name='proposals', args=[proposal_id])
                result = self.w3.eth.call({'to': self.market_address, 'data': data})
                
                # Find the JSON string in the raw bytes
                result_str = result.hex()
                if '7b2274797065223a' in result_str:  # {"type": in hex
                    json_start = result_str.index('7b2274797065223a')
                    json_bytes = bytes.fromhex(result_str[json_start:])
                    # Find the end of JSON
                    json_str = json_bytes.decode('utf-8', errors='ignore')
                    json_end = json_str.find('}') + 1
                    context = json_str[:json_end]
                else:
                    print("Could not find JSON data in proposal")
                    return None
            
            # Parse context JSON to get agent details
            context_json = json.loads(context) if isinstance(context, str) else context
            
            return {
                'id': proposal_id,
                'marketId': market_id,
                'proposalId': proposal_id,
                'context': context if isinstance(context, str) else json.dumps(context),
                'agentName': context_json.get('name', 'Unknown Agent'),
                'description': context_json.get('description', ''),
                'symbol': context_json.get('symbol', ''),
                'type': context_json.get('type', 'AI_AGENT')
            }
        except Exception as e:
            print(f"Error getting winning proposal: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def prepare_token_metadata(self, proposal: Dict) -> Tuple[str, str]:
        """Prepare token name and ticker from proposal"""
        # Use agent name and symbol from proposal
        agent_name = proposal['agentName']
        
        # Use symbol if available, otherwise create from name
        if proposal.get('symbol'):
            ticker = proposal['symbol'].upper()[:6]
        else:
            # Create ticker (max 6 chars, uppercase)
            ticker = agent_name.upper()[:6] if agent_name else "AGENT"
        
        # Ensure ticker is alphanumeric only
        ticker = ''.join(c for c in ticker if c.isalnum())
        
        return agent_name, ticker
    
    async def ensure_launch_funds(self) -> bool:
        """Ensure launcher has enough MockAID for launch"""
        try:
            # Check MockAID balance
            balance = self.mock_aid.functions.balanceOf(self.account.address).call()
            required = self.launch_fee + self.initial_purchase
            
            if balance < required:
                print(f"Insufficient MockAID. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(required, 'ether')}")
                
                # Mint more MockAID (for testing)
                mint_amount = required - balance + Web3.to_wei(100, 'ether')  # Extra buffer
                print(f"Minting {Web3.from_wei(mint_amount, 'ether')} MockAID...")
                
                nonce = self.w3.eth.get_transaction_count(self.account.address)
                tx = self.mock_aid.functions.mint(
                    self.account.address,
                    mint_amount
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': nonce,
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price
                })
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status != 1:
                    print("Failed to mint MockAID")
                    return False
                
                print(f"Minted MockAID successfully: {tx_hash.hex()}")
            
            # Approve Bonding contract to spend MockAID (approve large amount for multiple launches)
            print("Approving Bonding contract to spend MockAID...")
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            approve_amount = Web3.to_wei(1000000, 'ether')  # Approve 1M MockAID for multiple launches
            tx = self.mock_aid.functions.approve(
                self.bonding_address,
                approve_amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status != 1:
                print("Failed to approve MockAID")
                return False
            
            print(f"Approved MockAID successfully: {tx_hash.hex()}")
            return True
            
        except Exception as e:
            print(f"Error ensuring launch funds: {e}")
            return False
    
    async def launch_agent_token(self, market_id: int) -> Optional[Dict]:
        """Launch an agent token for a graduated market"""
        try:
            # Get winning proposal
            proposal = self.get_winning_proposal(market_id)
            if not proposal:
                print(f"No winning proposal found for market {market_id}")
                return None
            
            print(f"Launching token for agent: {proposal['agentName']}")
            
            # Prepare token metadata
            name, ticker = self.prepare_token_metadata(proposal)
            print(f"Token: {name} ({ticker})")
            
            # Ensure we have funds
            if not await self.ensure_launch_funds():
                print("Failed to secure launch funds")
                return None
            
            # Launch token via Bonding contract
            purchase_amount = self.launch_fee + self.initial_purchase
            
            print(f"Launching with {Web3.from_wei(purchase_amount, 'ether')} MockAID...")
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = self.bonding.functions.launchWithAsset(
                name,
                ticker,
                purchase_amount,
                self.mock_aid_address
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 5000000,  # Much higher gas limit for token creation
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"Launch transaction sent: {tx_hash.hex()}")
            print("Waiting for confirmation...")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status != 1:
                print(f"Launch transaction failed")
                return None
            
            print(f"✅ Agent token launched successfully!")
            print(f"Transaction: {tx_hash.hex()}")
            
            # Parse events to get token address (would need event ABI)
            # For now, return transaction info
            return {
                'market_id': market_id,
                'agent_name': name,
                'ticker': ticker,
                'tx_hash': tx_hash.hex(),
                'block': receipt.blockNumber
            }
            
        except Exception as e:
            print(f"Error launching agent token: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def monitor_and_launch(self, market_id: int):
        """Monitor a market and launch token when it graduates"""
        print(f"Monitoring market {market_id} for graduation...")
        
        while True:
            try:
                # Check if market has a winner
                proposal_id = self.market.functions.acceptedProposals(market_id).call()
                
                if proposal_id > 0:
                    print(f"Market {market_id} has graduated! Winner: Proposal {proposal_id}")
                    
                    # Launch the token
                    result = await self.launch_agent_token(market_id)
                    
                    if result:
                        print(f"Successfully launched token for market {market_id}")
                        return result
                    else:
                        print(f"Failed to launch token for market {market_id}")
                        return None
                
                # Wait before checking again
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Error monitoring market: {e}")
                await asyncio.sleep(10)


async def main():
    """Test agent token launcher"""
    launcher = AgentTokenLauncher()
    
    # Check market 1 for graduation
    market_id = 1
    
    # Try to launch immediately (if already graduated)
    proposal_id = launcher.market.functions.acceptedProposals(market_id).call()
    
    if proposal_id > 0:
        print(f"Market {market_id} already graduated. Launching token...")
        result = await launcher.launch_agent_token(market_id)
        print(f"Launch result: {result}")
    else:
        print(f"Market {market_id} not yet graduated. Monitoring...")
        result = await launcher.monitor_and_launch(market_id)
        print(f"Launch result: {result}")


if __name__ == "__main__":
    asyncio.run(main())