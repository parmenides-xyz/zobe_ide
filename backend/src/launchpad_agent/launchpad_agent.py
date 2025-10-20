"""
Agent Token Launchpad
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
    {"inputs":[{"name":"proposalId","type":"uint256"}],"name":"proposals","outputs":[{"name":"id","type":"uint256"},{"name":"marketId","type":"uint256"},{"name":"createdAt","type":"uint256"},{"name":"creator","type":"address"},{"name":"vUSD","type":"address"},{"name":"yesToken","type":"address"},{"name":"noToken","type":"address"},{"name":"yesPoolKey","type":"tuple","components":[{"name":"currency0","type":"address"},{"name":"currency1","type":"address"},{"name":"fee","type":"uint24"},{"name":"tickSpacing","type":"int24"},{"name":"hooks","type":"address"}]},{"name":"noPoolKey","type":"tuple","components":[{"name":"currency0","type":"address"},{"name":"currency1","type":"address"},{"name":"fee","type":"uint24"},{"name":"tickSpacing","type":"int24"},{"name":"hooks","type":"address"}]},{"name":"data","type":"bytes"}],"stateMutability":"view","type":"function"}
]''')

BONDING_ABI = json.loads('''[
    {"inputs":[{"name":"_name","type":"string"},{"name":"_ticker","type":"string"},{"name":"purchaseAmount","type":"uint256"},{"name":"assetToken","type":"address"}],"name":"launchWithAsset","outputs":[{"name":"","type":"address"},{"name":"","type":"address"},{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]''')

MOCK_USDC_ABI = json.loads('''[
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"faucet","outputs":[],"stateMutability":"nonpayable","type":"function"}
]''')

class AgentTokenLauncher:
    def __init__(self, private_key: str = None):
        """Initialize the agent token launcher"""
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))

        # Use provided private key or default to PRIVATE_KEY
        self.private_key = private_key or os.getenv('PRIVATE_KEY')
        self.account = Account.from_key(self.private_key)

        # Load contract addresses
        self.market_address = Web3.to_checksum_address(os.getenv('MARKET_ADDRESS'))
        self.bonding_address = Web3.to_checksum_address(os.getenv('BONDING_ADDRESS'))
        self.mock_usdc_address = Web3.to_checksum_address(os.getenv('MOCK_USDC_ADDRESS'))

        # Initialize contracts
        self.market = self.w3.eth.contract(address=self.market_address, abi=MARKET_ABI)
        self.bonding = self.w3.eth.contract(address=self.bonding_address, abi=BONDING_ABI)
        self.mock_usdc = self.w3.eth.contract(address=self.mock_usdc_address, abi=MOCK_USDC_ABI)

        # Launch configuration
        self.launch_fee = Web3.to_wei(100, 'ether')  # 100 MockUSDC
        self.initial_purchase = Web3.to_wei(10, 'ether')  # 10 MockUSDC initial purchase
        
    def get_winning_proposal(self, market_id: int) -> Optional[Dict]:
        """Get the winning proposal for a graduated market"""
        try:
            # Get accepted proposal ID
            proposal_id = self.market.functions.acceptedProposals(market_id).call()

            if proposal_id == 0:
                print(f"No accepted proposal for market {market_id}")
                return None

            # Get proposal data
            proposal = self.market.functions.proposals(proposal_id).call()

            # Proposal struct: (id, marketId, createdAt, creator, vUSD, yesToken, noToken,
            #                   yesPoolKey, noPoolKey, data)
            # data is bytes at index 9
            context_bytes = proposal[9]

            # Decode bytes to string
            context_str = context_bytes.decode('utf-8')

            # Parse JSON
            context_json = json.loads(context_str)

            return {
                'id': proposal_id,
                'marketId': market_id,
                'proposalId': proposal_id,
                'context': context_str,
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
        """Ensure launcher has enough MockUSDC for launch"""
        try:
            # Check MockUSDC balance
            balance = self.mock_usdc.functions.balanceOf(self.account.address).call()
            required = self.launch_fee + self.initial_purchase

            if balance < required:
                print(f"Insufficient MockUSDC. Have: {Web3.from_wei(balance, 'ether')}, Need: {Web3.from_wei(required, 'ether')}")

                # Call faucet to get MockUSDC (faucet gives 1000 USDC per call)
                print(f"Calling MockUSDC faucet...")

                nonce = self.w3.eth.get_transaction_count(self.account.address)
                tx = self.mock_usdc.functions.faucet().build_transaction({
                    'from': self.account.address,
                    'nonce': nonce,
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price
                })

                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status != 1:
                    print("Failed to get MockUSDC from faucet")
                    return False

                print(f"Got MockUSDC from faucet successfully: {tx_hash.hex()}")

            # Approve Bonding contract to spend MockUSDC
            print("Approving Bonding contract to spend MockUSDC...")
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            approve_amount = Web3.to_wei(1000000, 'ether')  # Approve 1M MockUSDC for multiple launches
            tx = self.mock_usdc.functions.approve(
                self.bonding_address,
                approve_amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                print("Failed to approve MockUSDC")
                return False

            print(f"Approved MockUSDC successfully: {tx_hash.hex()}")

            # Return the nonce that was just used so we can increment it
            return nonce + 1

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
            
            # Ensure we have funds and get the next nonce
            next_nonce = await self.ensure_launch_funds()
            if next_nonce is False:
                print("Failed to secure launch funds")
                return None

            # Launch token via Bonding contract
            purchase_amount = self.launch_fee + self.initial_purchase

            print(f"Launching with {Web3.from_wei(purchase_amount, 'ether')} MockUSDC...")

            nonce = next_nonce
            tx = self.bonding.functions.launchWithAsset(
                name,
                ticker,
                purchase_amount,
                self.mock_usdc_address
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 5000000,  # Much higher gas limit for token creation
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"Launch transaction sent: {tx_hash.hex()}")
            print("Waiting for confirmation...")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status != 1:
                print(f"Launch transaction failed")
                return None
            
            print(f"Agent token launched successfully!")
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
