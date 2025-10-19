"""ProposalAgent using GAME SDK"""
import json
import os
from typing import Tuple
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus

load_dotenv()

# Configuration
GAME_API_KEY = os.getenv("GAME_API_KEY")
BASE_RPC_URL = os.getenv("BASE_RPC_URL", "https://sepolia.base.org")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")
MARKET_TOKEN_ADDRESS = os.getenv("MOCK_USDC_ADDRESS")
PROPOSAL_AGENT_PRIVATE_KEY = os.getenv("PROPOSAL_AGENT_PRIVATE_KEY")
MARKET_ID = int(os.getenv("MARKET_ID", "1"))
NUM_PROPOSALS = int(os.getenv("NUM_PROPOSALS", "10"))

# Initialize Web3 and Account (global scope for functions to access)
w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
account = Account.from_key(PROPOSAL_AGENT_PRIVATE_KEY)

# Nonce tracking
_nonce = None

def get_nonce():
    """Get current nonce"""
    global _nonce
    if _nonce is None:
        _nonce = w3.eth.get_transaction_count(account.address)
    return _nonce

def increment_nonce():
    """Increment nonce after successful transaction"""
    global _nonce
    if _nonce is None:
        get_nonce()
    _nonce += 1
    return _nonce

def reset_nonce():
    """Reset nonce from chain (use after errors)"""
    global _nonce
    _nonce = w3.eth.get_transaction_count(account.address)
    return _nonce


# ============================================================================
# GAME SDK FUNCTIONS - What the AI agent can DO
# ============================================================================

def get_faucet_tokens(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Get tokens from faucet for proposal creation"""

    try:
        faucet_abi = [{
            "inputs": [],
            "name": "faucet",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        token_contract = w3.eth.contract(
            address=MARKET_TOKEN_ADDRESS,
            abi=faucet_abi
        )

        tx = token_contract.functions.faucet().build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        if receipt['status'] == 1:
            balance_abi = [{
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
            token = w3.eth.contract(address=MARKET_TOKEN_ADDRESS, abi=balance_abi)
            balance = token.functions.balanceOf(account.address).call()

            return (
                FunctionResultStatus.DONE,
                f"Got tokens from faucet. Balance: {Web3.from_wei(balance, 'ether')}",
                {"tx_hash": tx_hash.hex(), "balance": balance}
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Faucet transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Faucet error: {str(e)}",
            {}
        )


def deposit_to_market(market_id: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Deposit tokens to market before creating proposal"""

    try:
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

        market_contract = w3.eth.contract(address=MARKET_ADDRESS, abi=market_abi)
        market_info = market_contract.functions.markets(market_id).call()
        min_deposit = market_info[2]
        market_token = market_info[5]

        # Check balance
        balance_abi = [{
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        token_contract = w3.eth.contract(address=market_token, abi=balance_abi)
        balance = token_contract.functions.balanceOf(account.address).call()

        if balance < min_deposit:
            return (
                FunctionResultStatus.FAILED,
                f"Insufficient balance: {balance} < {min_deposit}",
                {}
            )

        # Approve
        approve_abi = [{
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        token = w3.eth.contract(address=market_token, abi=approve_abi)
        approve_tx = token.functions.approve(MARKET_ADDRESS, min_deposit).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed = account.sign_transaction(approve_tx)
        w3.eth.send_raw_transaction(signed.rawTransaction)
        increment_nonce()

        # Deposit
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

        market = w3.eth.contract(address=MARKET_ADDRESS, abi=deposit_abi)
        deposit_tx = market.functions.depositToMarket(account.address, market_id, min_deposit).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed = account.sign_transaction(deposit_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        if receipt['status'] == 1:
            return (
                FunctionResultStatus.DONE,
                f"Deposited {Web3.from_wei(min_deposit, 'ether')} to market {market_id}",
                {"market_id": market_id, "amount": min_deposit}
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Deposit transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Deposit error: {str(e)}",
            {}
        )


def generate_strategy(focus_area: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Generate AI agent strategy based on focus area"""

    strategies = {
        "lending": {
            "name": "Yield Optimizer AI",
            "symbol": "YOA",
            "description": "Monitors lending rates across Aave, Compound, Morpho and auto-rebalances for maximum yield",
            "capabilities": ["rate_monitoring", "auto_rebalance", "risk_assessment"],
            "protocols": ["aave", "compound", "morpho"]
        },
        "dex": {
            "name": "Liquidity Manager AI",
            "symbol": "LMA",
            "description": "Manages LP positions with impermanent loss protection and fee optimization",
            "capabilities": ["liquidity_provision", "il_protection", "fee_optimization"],
            "protocols": ["uniswap", "aerodrome"]
        },
        "arbitrage": {
            "name": "Arbitrage Hunter AI",
            "symbol": "AHA",
            "description": "Identifies and executes cross-DEX arbitrage opportunities with MEV protection",
            "capabilities": ["price_monitoring", "flash_loans", "mev_protection"],
            "protocols": ["uniswap", "aerodrome", "curve"]
        },
        "portfolio": {
            "name": "Portfolio Balancer AI",
            "symbol": "PBA",
            "description": "Maintains optimal portfolio allocation across DeFi protocols with automated rebalancing",
            "capabilities": ["portfolio_tracking", "rebalancing", "diversification"],
            "protocols": ["aave", "uniswap", "compound"]
        }
    }

    strategy = strategies.get(focus_area, strategies["lending"])

    return (
        FunctionResultStatus.DONE,
        f"Generated strategy: {strategy['name']} ({strategy['symbol']})",
        {"strategy": strategy}
    )


def submit_proposal(
    market_id: int,
    name: str,
    symbol: str,
    description: str,
    capabilities: list,
    **kwargs
) -> Tuple[FunctionResultStatus, str, dict]:
    """Submit AI agent proposal to quantum market on blockchain"""

    try:
        context = {
            "type": "AI_AGENT",
            "name": name,
            "symbol": symbol,
            "description": description,
            "capabilities": capabilities,
            "version": "1.0.0"
        }

        proposal_data = json.dumps(context).encode('utf-8')

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

        market = w3.eth.contract(address=MARKET_ADDRESS, abi=create_proposal_abi)

        tx = market.functions.createProposal(market_id, proposal_data).build_transaction({
            'from': account.address,
            'gas': 6000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        # Parse proposal ID from logs
        proposal_id = None
        if receipt['logs'] and receipt['status'] == 1:
            proposal_created_sig = w3.keccak(text="ProposalCreated(uint256,uint256,uint256,address)")

            for log in receipt['logs']:
                if len(log['topics']) >= 3 and log['topics'][0] == proposal_created_sig:
                    proposal_id = int.from_bytes(log['topics'][2], byteorder='big')
                    break

        if proposal_id and receipt['status'] == 1:
            return (
                FunctionResultStatus.DONE,
                f"Created proposal {proposal_id}: {name} ({symbol})",
                {
                    "proposal_id": proposal_id,
                    "tx_hash": tx_hash.hex(),
                    "name": name,
                    "symbol": symbol
                }
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                f"Proposal creation failed. Status: {receipt['status']}",
                {}
            )

    except Exception as e:
        reset_nonce()
        import traceback
        traceback.print_exc()
        return (
            FunctionResultStatus.FAILED,
            f"Submit error: {str(e)}",
            {}
        )


# ============================================================================
# STATE MANAGEMENT - What the AI agent SEES
# ============================================================================

def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """State available to proposal creation worker"""

    if current_state is None:
        return {
            "has_faucet_tokens": False,
            "has_deposited": False,
            "available_focus_areas": ["lending", "dex", "arbitrage", "portfolio"],
            "generated_strategy": None
        }

    if function_result and function_result.info:
        new_state = current_state.copy()

        if "balance" in function_result.info:
            new_state["has_faucet_tokens"] = True

        if "market_id" in function_result.info and "amount" in function_result.info:
            new_state["has_deposited"] = True

        if "strategy" in function_result.info:
            new_state["generated_strategy"] = function_result.info["strategy"]

        return new_state

    return current_state


def get_agent_state(function_result: FunctionResult, current_state: dict) -> dict:
    """High-level agent state tracking proposal creation progress"""

    if current_state is None:
        return {
            "market_id": MARKET_ID,
            "proposals_created": 0,
            "target_proposals": NUM_PROPOSALS,
            "created_proposal_ids": []
        }

    if function_result and function_result.info:
        new_state = current_state.copy()

        if "proposal_id" in function_result.info:
            new_state["proposals_created"] += 1
            new_state["created_proposal_ids"].append(function_result.info["proposal_id"])

        return new_state

    return current_state


# ============================================================================
# GAME SDK WORKER & AGENT CONFIGURATION
# ============================================================================

# Wrap functions in GAME SDK format
get_faucet_fn = Function(
    fn_name="get_faucet",
    fn_description="Get tokens from faucet for proposal creation",
    args=[],
    executable=get_faucet_tokens
)

deposit_fn = Function(
    fn_name="deposit",
    fn_description="Deposit tokens to market before creating proposal",
    args=[
        Argument(name="market_id", type="number", description="Market ID to deposit to")
    ],
    executable=deposit_to_market
)

generate_strategy_fn = Function(
    fn_name="generate_strategy",
    fn_description="Generate AI agent strategy for different DeFi focus areas",
    args=[
        Argument(name="focus_area", type="string", description="Focus area: lending, dex, arbitrage, or portfolio")
    ],
    executable=generate_strategy
)

submit_proposal_fn = Function(
    fn_name="submit_proposal",
    fn_description="Submit AI agent proposal to blockchain market",
    args=[
        Argument(name="market_id", type="number", description="Market ID"),
        Argument(name="name", type="string", description="Agent name"),
        Argument(name="symbol", type="string", description="Token symbol (max 6 chars)"),
        Argument(name="description", type="string", description="Agent description"),
        Argument(name="capabilities", type="array", description="List of agent capabilities")
    ],
    executable=submit_proposal
)

# Create worker configuration
proposal_worker = WorkerConfig(
    id="proposal_creator",
    worker_description="Creates AI agent proposals for prediction markets by analyzing DeFi protocols and generating unique strategies",
    get_state_fn=get_worker_state,
    action_space=[
        get_faucet_fn,
        deposit_fn,
        generate_strategy_fn,
        submit_proposal_fn
    ]
)


def create_proposal_agent(market_id: int = None, num_proposals: int = None) -> Agent:
    """Create GAME SDK agent for autonomous proposal generation"""

    if market_id is None:
        market_id = MARKET_ID
    if num_proposals is None:
        num_proposals = NUM_PROPOSALS

    agent = Agent(
        api_key=GAME_API_KEY,
        name="Proposal Generator",
        agent_goal=f"Create {num_proposals} unique AI agent proposals for market {market_id}. Each proposal must have a different focus area and strategy.",
        agent_description="""You are an expert in DeFi protocols and AI agent design.

Your task is to create diverse AI agent proposals for a futarchy prediction market on Base blockchain.

Available focus areas:
- lending: Yield optimization on Aave, Compound, Morpho
- dex: Liquidity management on Uniswap, Aerodrome
- arbitrage: Cross-DEX arbitrage with MEV protection
- portfolio: Portfolio balancing across protocols

Process:
1. Get tokens from faucet (one time only at start)
2. For each proposal:
   - Deposit to market
   - Generate unique strategy (vary the focus_area parameter)
   - Submit proposal to blockchain

Make each proposal unique with different focus areas.""",
        get_agent_state_fn=get_agent_state,
        workers=[proposal_worker],
        model_name="Llama-3.3-70B-Instruct"
    )

    return agent


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GAME SDK PROPOSAL AGENT")
    print("=" * 60)
    print(f"Market ID: {MARKET_ID}")
    print(f"Target Proposals: {NUM_PROPOSALS}")
    print(f"Agent Address: {account.address}")
    print("=" * 60)

    try:
        agent = create_proposal_agent()
        agent.compile()

        print("Agent compiled successfully")
        print("Starting autonomous proposal generation...\n")

        agent.run()

    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
