import os
import random
import asyncio
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
try:
    from .swap_helper import (
        build_swap_transaction,
        encode_permit2_approve,
        calculate_amount_out_minimum
    )
except ImportError:
    from swap_helper import (
        build_swap_transaction,
        encode_permit2_approve,
        calculate_amount_out_minimum
    )

# Load environment variables
load_dotenv()

class TraderAgent:
    """Simple trader agent that trades on Quantum Markets proposals"""
    
    def __init__(self, private_key, rpc_url, mock_usdc_address, market_address, 
                 router_address=None, permit2_address=None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.mock_usdc_address = mock_usdc_address
        self.market_address = market_address
        self.router_address = router_address or "0xa8043E34305742Fec40f0af01d440d181E3f392E"  # PoolSwapTest contract
        self.permit2_address = permit2_address or "0x8121cFC4f59988B5398C68134a188A3bA8b2712C"
        self.funded = False
        self.approved_tokens = set()  # Track which tokens we've approved
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
        """Get MockUSDC from faucet"""
        if not self.funded:
            await self.get_faucet_tokens()
            self.funded = True
            
    async def get_faucet_tokens(self):
        """Call faucet() on MockUSDC contract"""
        # ABI for just the faucet function
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
        
        # Build transaction
        tx = mock_usdc.functions.faucet().build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address),
        })
        
        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"Trader {self.address} got tokens from faucet (tx: {receipt['transactionHash'].hex()})")
        else:
            raise Exception(f"Faucet transaction failed for {self.address}")
        
    async def deposit_to_market(self, market_id, amount):
        """Deposit USDC to a market"""
        try:
            # First approve Market to spend USDC
            approve_abi = [{
                "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            mock_usdc = self.w3.eth.contract(address=self.mock_usdc_address, abi=approve_abi)
            
            # Approve using tracked nonce
            approve_nonce = self.get_nonce()
            tx = mock_usdc.functions.approve(self.market_address, amount).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': approve_nonce,
            })
            signed_tx = self.account.sign_transaction(tx)
            self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.increment_nonce()  # Increment after successful send
            
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
            deposit_nonce = self.get_nonce()  # Get current nonce (already incremented)
            tx = market.functions.depositToMarket(self.address, market_id, amount).build_transaction({
                'from': self.address,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': deposit_nonce,
            })
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.increment_nonce()  # Increment after successful send
            return receipt
        except Exception as e:
            # Reset nonce on error
            self.reset_nonce()
            raise e
    
    async def claim_vusd(self, proposal_id):
        """Claim vUSD for a proposal"""
        claim_abi = [{
            "inputs": [
                {"name": "depositor", "type": "address"},
                {"name": "proposalId", "type": "uint256"}
            ],
            "name": "claimVirtualTokenForProposal",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=claim_abi)
        claim_nonce = self.get_nonce()
        tx = market.functions.claimVirtualTokenForProposal(self.address, proposal_id).build_transaction({
            'from': self.address,
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': claim_nonce,
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.increment_nonce()
        return receipt
    
    async def approve_token_to_permit2(self, token_address):
        """Approve a token to Permit2 if not already approved"""
        if token_address in self.approved_tokens:
            return
        
        # Standard ERC20 approve to Permit2
        approve_abi = [{
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        token = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=approve_abi)
        approve_nonce = self.get_nonce()
        tx = token.functions.approve(self.permit2_address, 2**256 - 1).build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': approve_nonce,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.increment_nonce()
        
        self.approved_tokens.add(token_address)
        print(f"Approved {token_address[:8]} to Permit2")
        return receipt
    
    async def set_permit2_allowance(self, token_address):
        """Set Permit2 allowance for SwapRouter"""
        # Build approve call data
        approve_data = encode_permit2_approve(
            token_address,
            self.router_address,
            2**160 - 1,  # max amount
            2**48 - 1    # max expiration
        )
        
        permit_nonce = self.get_nonce()
        tx = {
            'from': self.address,
            'to': self.permit2_address,
            'data': '0x' + approve_data.hex(),
            'gas': 150000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': permit_nonce,
        }
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.increment_nonce()
        
        print(f"Set Permit2 allowance for {token_address[:8]} to Router")
        return receipt
    
    async def get_proposal_data(self, proposal_id):
        """Get full proposal data including pool keys"""
        # Full proposal ABI with pool keys
        proposal_abi = [{
            "inputs": [{"name": "", "type": "uint256"}],
            "name": "proposals",
            "outputs": [
                {"name": "id", "type": "uint256"},
                {"name": "marketId", "type": "uint256"},
                {"name": "createdAt", "type": "uint256"},
                {"name": "creator", "type": "address"},
                {"name": "vUSD", "type": "address"},
                {"name": "yesToken", "type": "address"},
                {"name": "noToken", "type": "address"},
                {"name": "yesPoolKey", "type": "tuple", "components": [
                    {"name": "currency0", "type": "address"},
                    {"name": "currency1", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "tickSpacing", "type": "int24"},
                    {"name": "hooks", "type": "address"}
                ]},
                {"name": "noPoolKey", "type": "tuple", "components": [
                    {"name": "currency0", "type": "address"},
                    {"name": "currency1", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "tickSpacing", "type": "int24"},
                    {"name": "hooks", "type": "address"}
                ]},
                {"name": "data", "type": "bytes"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=proposal_abi)
        proposal = market.functions.proposals(proposal_id).call()
        
        return {
            'id': proposal[0],
            'marketId': proposal[1],
            'vUSD': proposal[4],
            'yesToken': proposal[5],
            'noToken': proposal[6],
            'yesPoolKey': {
                'currency0': proposal[7][0],
                'currency1': proposal[7][1],
                'fee': proposal[7][2],
                'tickSpacing': proposal[7][3],
                'hooks': proposal[7][4]
            },
            'noPoolKey': {
                'currency0': proposal[8][0],
                'currency1': proposal[8][1],
                'fee': proposal[8][2],
                'tickSpacing': proposal[8][3],
                'hooks': proposal[8][4]
            }
        }
    
    async def get_proposal_tokens(self, proposal_id):
        """Get token addresses for a proposal (backward compatibility)"""
        data = await self.get_proposal_data(proposal_id)
        return {
            'vUSD': data['vUSD'],
            'yesToken': data['yesToken'],
            'noToken': data['noToken']
        }
    
    async def execute_swap(self, pool_key, token_in, token_out, amount_in, is_selling_decision_token=True):
        """Execute a swap on Uniswap V4 through PoolSwapTest"""
        try:
            # Approve tokens directly to PoolSwapTest
            approve_abi = [{
                "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            token = self.w3.eth.contract(address=Web3.to_checksum_address(token_in), abi=approve_abi)
            approve_nonce = self.get_nonce()
            
            # Approve PoolSwapTest directly
            print(f"  Approving {token_in[:8]}... to PoolSwapTest at {self.router_address[:8]}...")
            tx = token.functions.approve(self.router_address, 2**256 - 1).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': approve_nonce,
            })
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.increment_nonce()
            
            if receipt['status'] == 1:
                print(f"  ✓ Approved {token_in[:8]}... to PoolSwapTest (tx: {receipt['transactionHash'].hex()[:10]}...)")
            else:
                print(f"  ✗ Approval FAILED for {token_in[:8]}...")
                return None
            
            # Determine if this is a zero_for_one swap
            # token0 is the smaller address
            token0 = pool_key['currency0']
            token1 = pool_key['currency1']
            zero_for_one = token_in.lower() == token0.lower()
            
            # Calculate minimum output with slippage
            amount_out_minimum = calculate_amount_out_minimum(
                amount_in, 
                is_selling_decision_token, 
                slippage_bps=100  # 1% slippage
            )
            
            # Build the swap transaction
            swap_tx = build_swap_transaction(
                pool_key=pool_key,
                zero_for_one=zero_for_one,
                amount_in=amount_in,
                amount_out_minimum=amount_out_minimum,
                router_address=self.router_address
            )
            
            # Add transaction parameters
            swap_nonce = self.get_nonce()
            swap_tx.update({
                'from': self.address,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': swap_nonce,
            })
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(swap_tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.increment_nonce()
            
            print(f"  Swap tx: {receipt['transactionHash'].hex()}")
            return receipt
            
        except Exception as e:
            print(f"  Swap failed: {e}")
            self.reset_nonce()
            return None
    
    async def mint_yes_no(self, proposal_id, amount):
        """Mint YES/NO tokens with vUSD"""
        mint_abi = [{
            "inputs": [
                {"name": "proposalId", "type": "uint256"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "mintYesNo",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=mint_abi)
        mint_nonce = self.get_nonce()
        tx = market.functions.mintYesNo(proposal_id, amount).build_transaction({
            'from': self.address,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': mint_nonce,
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.increment_nonce()
        return receipt
    
    async def trade(self, proposal_id, market_id):
        """Execute a trade on a proposal"""
        try:
            import random
            
            # Check if we need to deposit and claim vUSD (do this once per proposal)
            if not hasattr(self, f'claimed_proposal_{proposal_id}'):
                # Deposit if not done for this market
                if not hasattr(self, f'deposited_{market_id}'):
                    deposit_amount = 1000 * 10**18  # Deposit 1000 USDC (enough for many trades)
                    print(f"Trader {self.address[:8]} depositing {deposit_amount/10**18:.0f} USDC to market {market_id}")
                    await self.deposit_to_market(market_id, deposit_amount)
                    setattr(self, f'deposited_{market_id}', True)
                
                # Claim ALL vUSD for this proposal at once
                print(f"Trader {self.address[:8]} claiming ALL vUSD for proposal {proposal_id}")
                await self.claim_vusd(proposal_id)
                setattr(self, f'claimed_proposal_{proposal_id}', True)
                
                # Track that we have vUSD available for this proposal
                setattr(self, f'vusd_available_{proposal_id}', 1000 * 10**18)
            
            # Get token addresses
            tokens = await self.get_proposal_tokens(proposal_id)
            
            # First approve vUSD to Market for minting YES/NO
            vusd_address = tokens['vUSD']
            await self.approve_token_to_permit2(vusd_address)
            
            # Also approve vUSD to Market contract for mintYesNo
            approve_abi = [{
                "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            vusd_contract = self.w3.eth.contract(address=Web3.to_checksum_address(vusd_address), abi=approve_abi)
            vusd_nonce = self.get_nonce()
            tx = vusd_contract.functions.approve(self.market_address, 2**256 - 1).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': vusd_nonce,
            })
            signed_tx = self.account.sign_transaction(tx)
            self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.increment_nonce()
            
            # Get full proposal data with pool keys
            proposal_data = await self.get_proposal_data(proposal_id)
            
            # Decide trading strategy
            is_bullish = random.random() > 0.5
            action = random.choice(['buy', 'sell'])  # Randomly choose to buy or sell
            
            if action == 'sell':
                # Mint YES/NO tokens first
                mint_amount = random.randint(10, 100) * 10**18  # Use some of our vUSD to mint
                print(f"Trader {self.address[:8]} minting {mint_amount/10**18:.0f} vUSD worth of YES/NO for proposal {proposal_id}")
                await self.mint_yes_no(proposal_id, mint_amount)
                
                if is_bullish:
                    # Bullish - sell NO tokens (we don't believe it will fail)
                    print(f"Trader {self.address[:8]} selling {mint_amount/10**18:.0f} NO tokens (bullish on proposal {proposal_id})")
                    await self.execute_swap(
                        pool_key=proposal_data['noPoolKey'],
                        token_in=proposal_data['noToken'],
                        token_out=proposal_data['vUSD'],
                        amount_in=mint_amount,
                        is_selling_decision_token=True
                    )
                else:
                    # Bearish - sell YES tokens (we don't believe it will succeed)
                    print(f"Trader {self.address[:8]} selling {mint_amount/10**18:.0f} YES tokens (bearish on proposal {proposal_id})")
                    await self.execute_swap(
                        pool_key=proposal_data['yesPoolKey'],
                        token_in=proposal_data['yesToken'],
                        token_out=proposal_data['vUSD'],
                        amount_in=mint_amount,
                        is_selling_decision_token=True
                    )
            else:
                # Buy tokens with vUSD (no minting needed)
                buy_amount = random.randint(10, 100) * 10**18  # Use some of our vUSD to buy
                
                if is_bullish:
                    # Bullish - BUY YES tokens (push YES price up)
                    print(f"Trader {self.address[:8]} buying YES tokens with {buy_amount/10**18:.0f} vUSD (bullish on proposal {proposal_id})")
                    await self.execute_swap(
                        pool_key=proposal_data['yesPoolKey'],
                        token_in=proposal_data['vUSD'],
                        token_out=proposal_data['yesToken'],
                        amount_in=buy_amount,
                        is_selling_decision_token=False
                    )
                else:
                    # Bearish - BUY NO tokens (believe it will fail)
                    print(f"Trader {self.address[:8]} buying NO tokens with {buy_amount/10**18:.0f} vUSD (bearish on proposal {proposal_id})")
                    await self.execute_swap(
                        pool_key=proposal_data['noPoolKey'],
                        token_in=proposal_data['vUSD'],
                        token_out=proposal_data['noToken'],
                        amount_in=buy_amount,
                        is_selling_decision_token=False
                    )
            
        except Exception as e:
            print(f"Trade error for {self.address[:8]}: {e}")
        
    def get_balance(self):
        """Get MockUSDC balance"""
        # Simple ERC20 balanceOf ABI
        balance_abi = [{
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        mock_usdc = self.w3.eth.contract(
            address=self.mock_usdc_address,
            abi=balance_abi
        )
        
        balance = mock_usdc.functions.balanceOf(self.address).call()
        return balance
    
    async def graduate_market(self, market_id):
        """Call graduateMarket to end the market and select winning proposal"""
        graduate_abi = [{
            "inputs": [{"name": "marketId", "type": "uint256"}],
            "name": "graduateMarket",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=graduate_abi)
        
        try:
            tx = market.functions.graduateMarket(market_id).build_transaction({
                'from': self.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.get_nonce(),
            })
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.increment_nonce()
            print(f"Market {market_id} graduated successfully! (tx: {receipt['transactionHash'].hex()})")
            return receipt
        except Exception as e:
            self.reset_nonce()
            print(f"Failed to graduate market: {e}")
            raise e
    
    def check_market_status(self, market_id):
        """Check if market is still open for trading"""
        markets_abi = [{
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
        
        market = self.w3.eth.contract(address=self.market_address, abi=markets_abi)
        market_data = market.functions.markets(market_id).call()
        status = market_data[7]
        deadline = market_data[3]
        import time
        current_time = int(time.time())
        
        if current_time > deadline and status == 0:
            return False
        return status == 0
    
    def check_winning_proposal(self, market_id):
        """Get the winning proposal after market graduation"""
        abi = [{
            "inputs": [{"name": "", "type": "uint256"}],
            "name": "acceptedProposals",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=abi)
        winning_proposal = market.functions.acceptedProposals(market_id).call()
        return winning_proposal
    
    def check_market_max(self, market_id):
        """Check current market max price and proposal"""
        market_abi = [{
            "inputs": [{"name": "", "type": "uint256"}],
            "name": "marketMax",
            "outputs": [
                {"name": "yesPrice", "type": "uint256"},
                {"name": "proposalId", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        market = self.w3.eth.contract(address=self.market_address, abi=market_abi)
        max_data = market.functions.marketMax(market_id).call()
        return {"yesPrice": max_data[0], "proposalId": max_data[1]}
    
    # Agent token functions removed - will be handled separately
    # The market now only handles graduation, not token launches