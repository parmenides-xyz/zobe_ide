"""ProposalAgent for creating AI agent proposals in prediction markets"""
import json
import random
import requests
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ProposalAgent:
    """Agent that creates AI agent proposals using dynamic LLM generation"""
    
    # Cache for generated proposals
    _cached_proposals = None
    
    @classmethod
    def generate_proposals_via_llm(cls, num_proposals=10):
        """Generate proposals using Claude API"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("No Anthropic API key found, using hardcoded proposals")
            return None
        
        prompt = f"""Generate {num_proposals} unique AI agent proposals for a prediction market on Sei blockchain.

Return ONLY a JSON array with exactly {num_proposals} agents. Each agent must have:
- name: Creative agent name (2-4 words)
- symbol: 3-4 letter ticker symbol
- description: One sentence describing what the agent does
- capabilities: Array of 2-3 specific tools/protocols it uses
- strategy: Brief description of its trading/operational strategy

Focus on: DeFi yield optimization, automated market making, lending protocols, arbitrage, staking, portfolio management.

Make each agent unique and interesting. Be creative with names and strategies.

JSON array:"""

        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                json={
                    'model': 'claude-sonnet-4-20250514',
                    'max_tokens': 3000,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                },
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['content'][0]['text']
                
                # Extract JSON from response
                json_start = ai_response.find('[')
                json_end = ai_response.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    proposals = json.loads(ai_response[json_start:json_end])
                    print(f"Generated {len(proposals)} proposals via Claude API")
                    return proposals[:num_proposals]
            else:
                print(f"Claude API error: {response.status_code}")
                
        except Exception as e:
            print(f"Error calling Claude API: {e}")
        
        return None
    
    @classmethod
    def get_agent_proposals(cls):
        """Get agent proposals (generate via LLM or use hardcoded)"""
        # Try to use cached proposals first
        if cls._cached_proposals:
            return cls._cached_proposals
        
        # Try to generate via LLM
        generated = cls.generate_proposals_via_llm(10)
        if generated:
            cls._cached_proposals = generated
            return generated
        
        # Fallback to hardcoded proposals
        return cls.HARDCODED_PROPOSALS
    
    # Hardcoded fallback proposals
    HARDCODED_PROPOSALS = [
        # Takara Lending Agents
        {
            "name": "Takara Yield Optimizer",
            "symbol": "TYO",
            "description": "AI agent that optimizes lending yields on Takara by monitoring rates and rebalancing positions",
            "capabilities": ["takara.mint", "takara.redeem", "takara.query"],
            "strategy": "Monitor lending rates across pools and automatically move funds to highest yield opportunities"
        },
        {
            "name": "Takara Liquidation Guardian",
            "symbol": "TLG",
            "description": "Agent that monitors and prevents liquidations on Takara lending positions",
            "capabilities": ["takara.query", "takara.repay", "takara.borrow"],
            "strategy": "Track health factors and automatically repay loans when approaching liquidation threshold"
        },
        {
            "name": "Takara Auto-Compounder",
            "symbol": "TAC",
            "description": "Automatically compounds lending rewards on Takara protocol",
            "capabilities": ["takara.mint", "takara.query", "takara.redeem"],
            "strategy": "Harvest rewards and re-deposit into lending pools for compound growth"
        },
        
        # Symphony Swap Agents
        {
            "name": "Symphony Arbitrage Bot",
            "symbol": "SAB",
            "description": "Executes arbitrage opportunities using Symphony DEX aggregator",
            "capabilities": ["symphony.swap", "sei-erc20.transfer"],
            "strategy": "Identify price discrepancies across DEXs and execute profitable swaps"
        },
        {
            "name": "Symphony DCA Agent",
            "symbol": "DCA",
            "description": "Dollar-cost averaging agent using Symphony for periodic swaps",
            "capabilities": ["symphony.swap", "sei-erc20.balance"],
            "strategy": "Execute scheduled swaps to accumulate positions over time"
        },
        
        # Carbon DeFi Strategy Agents
        {
            "name": "Carbon Market Maker",
            "symbol": "CMM",
            "description": "Automated market making using Carbon protocol's advanced strategies",
            "capabilities": ["carbon.createBuySellStrategy", "carbon.updateStrategy", "carbon.getUserStrategies"],
            "strategy": "Create and manage buy/sell strategies to provide liquidity and capture spreads"
        },
        {
            "name": "Carbon Range Trader",
            "symbol": "CRT",
            "description": "Creates overlapping trading strategies on Carbon for range-bound markets",
            "capabilities": ["carbon.createOverlappingStrategy", "carbon.deleteStrategy", "carbon.updateStrategy"],
            "strategy": "Deploy overlapping strategies to profit from price oscillations within defined ranges"
        },
        {
            "name": "Carbon Strategy Optimizer",
            "symbol": "CSO",
            "description": "Optimizes Carbon DeFi trading strategies based on market conditions",
            "capabilities": ["carbon.getUserStrategies", "carbon.updateStrategy", "carbon.composeTradeBySourceTx"],
            "strategy": "Analyze performance and adjust strategy parameters for maximum efficiency"
        },
        
        # Silo Staking Agents
        {
            "name": "Silo Auto-Staker",
            "symbol": "SAS",
            "description": "Automatically stakes and compounds SEI rewards through Silo",
            "capabilities": ["silo.stakeBond", "silo.unstakeBond"],
            "strategy": "Maximize staking yields by auto-compounding and rebalancing stake positions"
        },
        {
            "name": "Silo Yield Hunter",
            "symbol": "SYH",
            "description": "Hunts for best staking opportunities and manages unstaking periods",
            "capabilities": ["silo.stakeBond", "silo.unstakeBond"],
            "strategy": "Monitor staking rates and optimize entry/exit timing for maximum returns"
        },
        
        # Multi-Protocol Combination Agents
        {
            "name": "DeFi Yield Aggregator",
            "symbol": "DYA",
            "description": "Combines Takara lending, Symphony swaps, and Silo staking for optimal yields",
            "capabilities": ["takara.mint", "symphony.swap", "silo.stakeBond"],
            "strategy": "Allocate capital across protocols based on risk-adjusted returns"
        },
        {
            "name": "Risk Management Suite",
            "symbol": "RMS",
            "description": "Comprehensive risk management across Takara, Carbon, and Symphony",
            "capabilities": ["takara.query", "carbon.getUserStrategies", "symphony.swap"],
            "strategy": "Monitor positions across protocols and execute hedging strategies"
        },
        {
            "name": "Liquidity Provider Bot",
            "symbol": "LPB",
            "description": "Provides liquidity using Carbon strategies and Symphony routing",
            "capabilities": ["carbon.createBuySellStrategy", "symphony.swap", "sei-erc20.transfer"],
            "strategy": "Deploy capital efficiently across multiple liquidity venues"
        },
        {
            "name": "Portfolio Rebalancer",
            "symbol": "PRB",
            "description": "Automatically rebalances portfolio using Symphony swaps and Takara lending",
            "capabilities": ["symphony.swap", "takara.mint", "takara.redeem"],
            "strategy": "Maintain target portfolio allocations through automated rebalancing"
        },
        {
            "name": "Flash Loan Arbitrageur",
            "symbol": "FLA",
            "description": "Executes flash loan arbitrage using Takara and Symphony",
            "capabilities": ["takara.borrow", "symphony.swap", "takara.repay"],
            "strategy": "Identify and execute risk-free arbitrage using flash loans"
        }
    ]
    
    # For backward compatibility
    AGENT_PROPOSALS = HARDCODED_PROPOSALS
    
    def __init__(self, private_key, rpc_url, mock_usdc_address, market_address):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.mock_usdc_address = mock_usdc_address
        self.market_address = market_address
        self.funded = False
        self.created_proposals = []
        self.nonce = None  # Track nonce to avoid conflicts
        
    @property
    def address(self):
        return self.account.address
    
    def get_nonce(self):
        """Get the current nonce, fetching from chain if needed"""
        if self.nonce is None:
            self.nonce = self.w3.eth.get_transaction_count(self.address)
        return self.nonce
    
    def increment_nonce(self):
        """Increment the nonce after a successful transaction"""
        if self.nonce is None:
            self.get_nonce()
        self.nonce += 1
        return self.nonce
    
    def reset_nonce(self):
        """Reset nonce from chain (use after errors)"""
        self.nonce = self.w3.eth.get_transaction_count(self.address)
        return self.nonce
        
    async def initialize(self):
        """Get MockUSDC from faucet and prepare for proposal creation"""
        if not self.funded:
            await self.get_faucet_tokens()
            self.funded = True
            
    async def get_faucet_tokens(self):
        """Call faucet() on MockUSDC contract"""
        faucet_abi = [{
            "inputs": [],
            "name": "faucet",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        mock_usdc = self.w3.eth.contract(
            address=self.mock_usdc_address,
            abi=faucet_abi
        )
        
        tx = mock_usdc.functions.faucet().build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address),
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"ProposalAgent {self.address[:8]} got tokens from faucet (tx: {receipt['transactionHash'].hex()})")
        else:
            raise Exception(f"Faucet transaction failed for {self.address[:8]}")
        return receipt
        
    async def get_market_info(self, market_id):
        """Get market configuration including min deposit"""
        market_abi = [{
            "inputs": [{"name": "", "type": "uint256"}],
            "name": "markets",
            "outputs": [
                {"name": "id", "type": "uint256"},
                {"name": "createdAt", "type": "uint256"},
                {"name": "minDeposit", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "creator", "type": "address"},
                {"name": "marketToken", "type": "address"},
                {"name": "resolver", "type": "address"},
                {"name": "status", "type": "uint8"},
                {"name": "title", "type": "string"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=market_abi)
        market_config = market.functions.markets(market_id).call()
        return {
            'id': market_config[0],
            'minDeposit': market_config[2],
            'deadline': market_config[3],
            'marketToken': market_config[5],
            'status': market_config[7],
            'title': market_config[8]
        }
        
    async def deposit_to_market(self, market_id, amount):
        """Deposit USDC to a market"""
        # First approve Market to spend USDC
        approve_abi = [{
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        mock_usdc = self.w3.eth.contract(address=self.mock_usdc_address, abi=approve_abi)
        
        # Approve
        tx = mock_usdc.functions.approve(self.market_address, amount).build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address),
        })
        signed_tx = self.account.sign_transaction(tx)
        self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Deposit to market
        deposit_abi = [{
            "inputs": [
                {"name": "depositor", "type": "address"},
                {"name": "marketId", "type": "uint256"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "depositToMarket",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=deposit_abi)
        tx = market.functions.depositToMarket(self.address, market_id, amount).build_transaction({
            'from': self.address,
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address),
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"ProposalAgent {self.address[:8]} deposited {amount/10**18} to market {market_id}")
        return receipt
        
    def generate_proposal_data(self, agent_template=None):
        """Generate proposal metadata for an AI agent"""
        if agent_template is None:
            # Use dynamically generated proposals or fallback
            available_proposals = self.get_agent_proposals()
            agent_template = random.choice(available_proposals)
        
        # Create structured proposal data
        proposal_data = {
            "type": "AI_AGENT",
            "name": agent_template["name"],
            "symbol": agent_template["symbol"],
            "description": agent_template["description"],
            "capabilities": agent_template["capabilities"],
            "strategy": agent_template["strategy"],
            "initialSupply": 1000000,  # 1M tokens
            "version": "1.0.0"
        }
        
        # Encode as bytes for contract
        return json.dumps(proposal_data).encode('utf-8')
        
    async def create_proposal(self, market_id, agent_template=None):
        """Create an AI agent proposal in a market"""
        try:
            # Get market info
            market_info = await self.get_market_info(market_id)
            
            # Check market is still open
            if market_info['status'] != 0:  # 0 = OPEN
                print(f"Market {market_id} is not open (status: {market_info['status']})")
                return None
            
            # Deposit minimum required (use market token, not mock USDC)
            min_deposit = market_info['minDeposit']
            market_token = market_info['marketToken']
            
            # Check balance first
            balance_abi = [{
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
            token_contract = self.w3.eth.contract(address=market_token, abi=balance_abi)
            balance = token_contract.functions.balanceOf(self.address).call()
            print(f"  Agent balance: {balance}, required: {min_deposit} (scaled from {min_deposit})")
            
            if balance < min_deposit:
                raise Exception(f"Insufficient balance. Have {balance}, need {min_deposit}")
            
            # Approve and deposit market token (not USDC)
            approve_abi = [{
                "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            market_token_contract = self.w3.eth.contract(address=market_token, abi=approve_abi)
            approve_nonce = self.get_nonce()
            tx = market_token_contract.functions.approve(self.market_address, min_deposit).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': approve_nonce,
            })
            signed_tx = self.account.sign_transaction(tx)
            self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.increment_nonce()  # Increment after successful send
            
            # Now deposit to market
            deposit_abi = [{
                "inputs": [
                    {"name": "depositor", "type": "address"},
                    {"name": "marketId", "type": "uint256"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "depositToMarket",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            market = self.w3.eth.contract(address=self.market_address, abi=deposit_abi)
            deposit_nonce = self.get_nonce()
            print(f"  Depositing {min_deposit} tokens to market {market_id} (scaled from {min_deposit})")
            tx = market.functions.depositToMarket(self.address, market_id, min_deposit).build_transaction({
                'from': self.address,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': deposit_nonce,
            })
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.increment_nonce()  # Increment after successful send
            
            if receipt['status'] != 1:
                raise Exception(f"Deposit to market failed. Status: {receipt['status']}, Gas used: {receipt['gasUsed']}")
            print(f"  Deposit successful")
            
            # Generate proposal data
            proposal_data = self.generate_proposal_data(agent_template)
            
            # Create the proposal
            create_proposal_abi = [{
                "inputs": [
                    {"name": "marketId", "type": "uint256"},
                    {"name": "data", "type": "bytes"}
                ],
                "name": "createProposal",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            market = self.w3.eth.contract(address=self.market_address, abi=create_proposal_abi)
            proposal_nonce = self.get_nonce()
            print(f"  Creating proposal for market {market_id}")
            tx = market.functions.createProposal(market_id, proposal_data).build_transaction({
                'from': self.address,
                'gas': 6000000,  # Increased gas limit - proposal creation needs ~3.7M
                'gasPrice': self.w3.eth.gas_price,
                'nonce': proposal_nonce,
            })
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"  Tx sent: {tx_hash.hex()}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.increment_nonce()  # Increment after successful send
            
            print(f"  Tx receipt status: {receipt['status']}, gas used: {receipt['gasUsed']}")
            
            # Check if transaction succeeded
            if receipt['status'] != 1:
                print(f"  Transaction logs: {receipt.get('logs', [])}")
                raise Exception(f"Proposal creation failed for market {market_id}. Gas used: {receipt['gasUsed']}, Tx: {tx_hash.hex()}")
            
            # Parse proposal ID from event logs
            proposal_id = None
            if receipt['logs']:
                # ProposalCreated event signature
                proposal_created_sig = self.w3.keccak(text="ProposalCreated(uint256,uint256,uint256,address)")
                
                for i, log in enumerate(receipt['logs']):
                    if len(log['topics']) >= 3 and log['topics'][0] == proposal_created_sig:
                        proposal_id_bytes = log['topics'][2]
                        proposal_id = int.from_bytes(proposal_id_bytes, byteorder='big')
                        break
            
            if proposal_id is None:
                raise Exception("Could not parse proposal ID from transaction logs")
            
            # Parse proposal details
            proposal_details = json.loads(proposal_data.decode('utf-8'))
            
            print(f"ProposalAgent {self.address[:8]} created proposal ID {proposal_id} in market {market_id}")
            print(f"  Agent: {proposal_details['name']} ({proposal_details['symbol']})")
            print(f"  Capabilities: {', '.join(proposal_details['capabilities'])}")
            print(f"  Transaction: {receipt['transactionHash'].hex()}")
            
            self.created_proposals.append({
                'proposal_id': proposal_id,
                'market_id': market_id,
                'tx_hash': receipt['transactionHash'].hex(),
                'agent': proposal_details
            })
            
            return receipt, proposal_id
        except Exception as e:
            # Reset nonce on error
            self.reset_nonce()
            print(f"Detailed error in create_proposal: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
        
