"""TraderAgent using GAME SDK with Allora Plugin"""
import json
import os
import random
import hashlib
from typing import Tuple, Dict
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus

# Import Allora Plugin from GAME SDK
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../game-python'))
from plugins.allora.allora_game_sdk.allora_plugin import AlloraPlugin
from allora_sdk.v2.api_client import ChainSlug, PriceInferenceToken, PriceInferenceTimeframe

try:
    from .swap_helper import (
        build_swap_transaction,
        calculate_amount_out_minimum
    )
except ImportError:
    from src.traders.swap_helper import (
        build_swap_transaction,
        calculate_amount_out_minimum
    )

load_dotenv()

# Configuration
GAME_API_KEY = os.getenv("GAME_API_KEY")
BASE_RPC_URL = os.getenv("BASE_RPC_URL", "https://sepolia.base.org")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")
MOCK_USDC_ADDRESS = os.getenv("MOCK_USDC_ADDRESS")
TRADER_PRIVATE_KEY = os.getenv("TRADER_PRIVATE_KEY")
ROUTER_ADDRESS = os.getenv("ROUTER_ADDRESS", "0xa8043E34305742Fec40f0af01d440d181E3f392E")
MARKET_ID = int(os.getenv("MARKET_ID", "1"))
NUM_TRADES = int(os.getenv("NUM_TRADES", "20"))
ALLORA_API_KEY = os.getenv("ALLORA_API_KEY", "UP-8cbc632a67a84ac1b4078661")

# Initialize Web3 and Account
w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
account = Account.from_key(TRADER_PRIVATE_KEY)

# Initialize Allora Plugin
allora_plugin = AlloraPlugin(
    chain_slug=ChainSlug.TESTNET,
    api_key=ALLORA_API_KEY
)

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
# TRADING CITIES - The five Cities and Trade (from Italo Calvino's "Invisible Cities")
# ============================================================================

TRADING_CITIES = {
    "Euphemia": {
        "description": "At each solstice and equinox, merchants gather to exchange goods and memories",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.6,
        "action_bias": "storyteller",
        "quote": "You do not come to Euphemia only to buy and sell, but also because at night, by the fires all around the market, seated on sacks or barrels, you hear the stories"
    },
    "Chloe": {
        "description": "City of strangers passing in the street, desiring each other without speaking",
        "bullish_threshold": 0.05,
        "confidence_weight": 0.7,
        "action_bias": "silent_observer",
        "quote": "In Chloe, a great city, the people who move through the streets are all strangers"
    },
    "Eutropia": {
        "description": "City that reinvents itself periodically - citizens swap roles, houses, occupations",
        "bullish_threshold": -0.1,
        "confidence_weight": 0.4,
        "action_bias": "chameleon",
        "quote": "In Eutropia you can avoid doing the same job all your life, but you cannot avoid doing all jobs"
    },
    "Ersilia": {
        "description": "City defined by relationships - threads connect houses showing bonds between inhabitants",
        "bullish_threshold": 0.02,
        "confidence_weight": 0.8,
        "action_bias": "network_builder",
        "quote": "In Ersilia, to establish the relationships that sustain the city's life, the inhabitants stretch strings from the corners of the houses"
    },
    "Esmeralda": {
        "description": "City of water channels where cats, thieves, lovers all follow their own paths",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.5,
        "action_bias": "multi_path",
        "quote": "In Esmeralda, city of water, a network of canals and a network of streets span and intersect each other"
    }
}


def get_city_personality(address: str) -> Dict:
    """Get deterministic city personality based on wallet address"""
    hash_int = int(hashlib.md5(address.encode()).hexdigest(), 16)
    city_names = list(TRADING_CITIES.keys())
    city_index = hash_int % len(city_names)
    city_name = city_names[city_index]

    city_data = TRADING_CITIES[city_name].copy()
    city_data['name'] = city_name
    return city_data


# ============================================================================
# GAME SDK FUNCTIONS - What the AI agent can DO
# ============================================================================

def get_faucet_tokens(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Get MockUSDC tokens from faucet"""

    try:
        faucet_abi = [{
            "inputs": [],
            "name": "faucet",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        token_contract = w3.eth.contract(
            address=MOCK_USDC_ADDRESS,
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
            token = w3.eth.contract(address=MOCK_USDC_ADDRESS, abi=balance_abi)
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


def deposit_to_market(market_id: int, amount: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Deposit USDC to market for trading"""

    try:
        # Approve
        approve_abi = [{
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        token = w3.eth.contract(address=MOCK_USDC_ADDRESS, abi=approve_abi)
        approve_tx = token.functions.approve(MARKET_ADDRESS, amount).build_transaction({
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
        deposit_tx = market.functions.depositToMarket(account.address, market_id, amount).build_transaction({
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
                f"Deposited {Web3.from_wei(amount, 'ether')} USDC to market {market_id}",
                {"market_id": market_id, "amount": amount, "tx_hash": tx_hash.hex()}
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


def claim_vusd(proposal_id: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Claim virtual USD for trading on proposal"""

    try:
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

        market = w3.eth.contract(address=MARKET_ADDRESS, abi=claim_abi)
        tx = market.functions.claimVirtualTokenForProposal(account.address, proposal_id).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        if receipt['status'] == 1:
            return (
                FunctionResultStatus.DONE,
                f"Claimed vUSD for proposal {proposal_id}",
                {"proposal_id": proposal_id, "tx_hash": tx_hash.hex()}
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Claim transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Claim error: {str(e)}",
            {}
        )


def get_market_info(market_id: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Get market information including proposals"""

    try:
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

        market_contract = w3.eth.contract(address=MARKET_ADDRESS, abi=markets_abi)
        market_data = market_contract.functions.markets(market_id).call()

        # Get proposal count
        proposal_count_abi = [{
            "inputs": [],
            "name": "getProposalCount",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]

        market_contract2 = w3.eth.contract(address=MARKET_ADDRESS, abi=proposal_count_abi)
        proposal_count = market_contract2.functions.getProposalCount().call()

        info = {
            "market_id": market_data[0],
            "created_at": market_data[1],
            "min_deposit": market_data[2],
            "deadline": market_data[3],
            "status": market_data[7],
            "title": market_data[8],
            "proposal_count": proposal_count
        }

        return (
            FunctionResultStatus.DONE,
            f"Market {market_id}: {info['title']} with {proposal_count} proposals",
            info
        )

    except Exception as e:
        return (
            FunctionResultStatus.FAILED,
            f"Failed to get market info: {str(e)}",
            {}
        )


def get_proposal_data(proposal_id: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Get full proposal data including pool keys and tokens"""

    try:
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

        market = w3.eth.contract(address=MARKET_ADDRESS, abi=proposal_abi)
        proposal = market.functions.proposals(proposal_id).call()

        data = {
            'id': proposal[0],
            'market_id': proposal[1],
            'vUSD': proposal[4],
            'yes_token': proposal[5],
            'no_token': proposal[6],
            'yes_pool_key': {
                'currency0': proposal[7][0],
                'currency1': proposal[7][1],
                'fee': proposal[7][2],
                'tickSpacing': proposal[7][3],
                'hooks': proposal[7][4]
            },
            'no_pool_key': {
                'currency0': proposal[8][0],
                'currency1': proposal[8][1],
                'fee': proposal[8][2],
                'tickSpacing': proposal[8][3],
                'hooks': proposal[8][4]
            }
        }

        return (
            FunctionResultStatus.DONE,
            f"Got proposal {proposal_id} data with tokens and pool keys",
            data
        )

    except Exception as e:
        return (
            FunctionResultStatus.FAILED,
            f"Failed to get proposal data: {str(e)}",
            {}
        )


def mint_yes_no_tokens(proposal_id: int, amount: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Mint YES/NO tokens with vUSD"""

    try:
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

        market = w3.eth.contract(address=MARKET_ADDRESS, abi=mint_abi)
        tx = market.functions.mintYesNo(proposal_id, amount).build_transaction({
            'from': account.address,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        if receipt['status'] == 1:
            return (
                FunctionResultStatus.DONE,
                f"Minted {Web3.from_wei(amount, 'ether')} YES/NO tokens",
                {"proposal_id": proposal_id, "amount": amount, "tx_hash": tx_hash.hex()}
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Mint transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Mint error: {str(e)}",
            {}
        )


def approve_token(token_address: str, spender_address: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Approve token spending"""

    try:
        approve_abi = [{
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=approve_abi)
        tx = token.functions.approve(spender_address, 2**256 - 1).build_transaction({
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
            return (
                FunctionResultStatus.DONE,
                f"Approved {token_address[:8]}... to {spender_address[:8]}...",
                {"token": token_address, "spender": spender_address, "tx_hash": tx_hash.hex()}
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Approval transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Approval error: {str(e)}",
            {}
        )


def execute_swap(
    pool_key: dict,
    token_in: str,
    token_out: str,
    amount_in: int,
    is_selling_decision_token: bool,
    **kwargs
) -> Tuple[FunctionResultStatus, str, dict]:
    """Execute a token swap on Uniswap V4"""

    try:
        # Determine swap direction
        token0 = pool_key['currency0']
        token1 = pool_key['currency1']
        zero_for_one = token_in.lower() == token0.lower()

        # Calculate minimum output
        amount_out_minimum = calculate_amount_out_minimum(
            amount_in,
            is_selling_decision_token,
            slippage_bps=100
        )

        # Build swap transaction
        swap_tx = build_swap_transaction(
            pool_key=pool_key,
            zero_for_one=zero_for_one,
            amount_in=amount_in,
            amount_out_minimum=amount_out_minimum,
            router_address=ROUTER_ADDRESS
        )

        swap_tx.update({
            'from': account.address,
            'gas': 500000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed_tx = account.sign_transaction(swap_tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        if receipt['status'] == 1:
            return (
                FunctionResultStatus.DONE,
                f"Swapped {Web3.from_wei(amount_in, 'ether')} tokens",
                {
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount_in": amount_in,
                    "tx_hash": tx_hash.hex()
                }
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Swap transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Swap error: {str(e)}",
            {}
        )


def graduate_market(market_id: int, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """Graduate market and select winning proposal"""

    try:
        graduate_abi = [{
            "inputs": [{"name": "marketId", "type": "uint256"}],
            "name": "graduateMarket",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        market = w3.eth.contract(address=MARKET_ADDRESS, abi=graduate_abi)
        tx = market.functions.graduateMarket(market_id).build_transaction({
            'from': account.address,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': get_nonce(),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        increment_nonce()

        if receipt['status'] == 1:
            # Get winning proposal
            accepted_abi = [{
                "inputs": [{"name": "", "type": "uint256"}],
                "name": "acceptedProposals",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
            market2 = w3.eth.contract(address=MARKET_ADDRESS, abi=accepted_abi)
            winning_proposal = market2.functions.acceptedProposals(market_id).call()

            return (
                FunctionResultStatus.DONE,
                f"Market {market_id} graduated! Winner: Proposal {winning_proposal}",
                {"market_id": market_id, "winning_proposal": winning_proposal, "tx_hash": tx_hash.hex()}
            )
        else:
            return (
                FunctionResultStatus.FAILED,
                "Graduate transaction failed",
                {}
            )

    except Exception as e:
        reset_nonce()
        return (
            FunctionResultStatus.FAILED,
            f"Graduate error: {str(e)}",
            {}
        )


# ============================================================================
# STATE MANAGEMENT - What the AI agent SEES
# ============================================================================

def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """State available to trading worker"""

    if current_state is None:
        city = get_city_personality(account.address)
        return {
            "has_faucet_tokens": False,
            "deposited_markets": [],
            "claimed_proposals": [],
            "approved_tokens": {},
            "city": city['name'],
            "city_quote": city['quote']
        }

    if function_result and function_result.info:
        new_state = current_state.copy()

        if "balance" in function_result.info:
            new_state["has_faucet_tokens"] = True

        if "market_id" in function_result.info and "amount" in function_result.info:
            market_id = function_result.info["market_id"]
            if market_id not in new_state["deposited_markets"]:
                new_state["deposited_markets"].append(market_id)

        if "proposal_id" in function_result.info and "tx_hash" in function_result.info:
            proposal_id = function_result.info["proposal_id"]
            if proposal_id not in new_state["claimed_proposals"]:
                new_state["claimed_proposals"].append(proposal_id)

        if "token" in function_result.info and "spender" in function_result.info:
            token = function_result.info["token"]
            spender = function_result.info["spender"]
            if token not in new_state["approved_tokens"]:
                new_state["approved_tokens"][token] = []
            if spender not in new_state["approved_tokens"][token]:
                new_state["approved_tokens"][token].append(spender)

        # Store price inferences from Allora
        if "asset" in function_result.info and "price_inference" in function_result.info:
            if "allora_inferences" not in new_state:
                new_state["allora_inferences"] = {}
            new_state["allora_inferences"][function_result.info["asset"]] = function_result.info["price_inference"]

        return new_state

    return current_state


def get_agent_state(function_result: FunctionResult, current_state: dict) -> dict:
    """High-level agent state tracking trading progress"""

    if current_state is None:
        return {
            "market_id": MARKET_ID,
            "target_trades": NUM_TRADES,
            "completed_trades": 0,
            "proposals_traded": []
        }

    if function_result and function_result.info:
        new_state = current_state.copy()

        # Track completed swaps
        if "token_in" in function_result.info and "token_out" in function_result.info:
            new_state["completed_trades"] += 1

        # Track which proposals we've traded
        if "trade_type" in function_result.info:
            proposal_id = function_result.info.get("proposal_id")
            if proposal_id and proposal_id not in new_state["proposals_traded"]:
                new_state["proposals_traded"].append(proposal_id)

        return new_state

    return current_state


# ============================================================================
# GAME SDK WORKER & AGENT CONFIGURATION
# ============================================================================

# Wrap functions in GAME SDK format
get_faucet_fn = Function(
    fn_name="get_faucet",
    fn_description="Get MockUSDC tokens from faucet for trading",
    args=[],
    executable=get_faucet_tokens
)

deposit_fn = Function(
    fn_name="deposit_to_market",
    fn_description="Deposit USDC to market to enable trading",
    args=[
        Argument(name="market_id", type="number", description="Market ID to deposit to"),
        Argument(name="amount", type="number", description="Amount of USDC to deposit (in wei)")
    ],
    executable=deposit_to_market
)

claim_fn = Function(
    fn_name="claim_vusd",
    fn_description="Claim virtual USD for trading on a specific proposal",
    args=[
        Argument(name="proposal_id", type="number", description="Proposal ID to claim vUSD for")
    ],
    executable=claim_vusd
)

get_market_fn = Function(
    fn_name="get_market_info",
    fn_description="Get market information and proposal count",
    args=[
        Argument(name="market_id", type="number", description="Market ID to query")
    ],
    executable=get_market_info
)

get_proposal_fn = Function(
    fn_name="get_proposal_data",
    fn_description="Get proposal data including tokens and pool keys needed for trading",
    args=[
        Argument(name="proposal_id", type="number", description="Proposal ID to query")
    ],
    executable=get_proposal_data
)

mint_fn = Function(
    fn_name="mint_yes_no_tokens",
    fn_description="Mint YES/NO tokens using vUSD (needed before selling)",
    args=[
        Argument(name="proposal_id", type="number", description="Proposal ID"),
        Argument(name="amount", type="number", description="Amount to mint (in wei)")
    ],
    executable=mint_yes_no_tokens
)

approve_fn = Function(
    fn_name="approve_token",
    fn_description="Approve token for spending (needed before swaps)",
    args=[
        Argument(name="token_address", type="string", description="Token to approve"),
        Argument(name="spender_address", type="string", description="Address to approve for spending")
    ],
    executable=approve_token
)

swap_fn = Function(
    fn_name="execute_swap",
    fn_description="Execute token swap on Uniswap V4 pools",
    args=[
        Argument(name="pool_key", type="object", description="Pool key with currency0, currency1, fee, tickSpacing, hooks"),
        Argument(name="token_in", type="string", description="Input token address"),
        Argument(name="token_out", type="string", description="Output token address"),
        Argument(name="amount_in", type="number", description="Input amount (in wei)"),
        Argument(name="is_selling_decision_token", type="boolean", description="True if selling YES/NO, False if buying")
    ],
    executable=execute_swap
)

graduate_fn = Function(
    fn_name="graduate_market",
    fn_description="Graduate market and select winning proposal (call after trading period ends)",
    args=[
        Argument(name="market_id", type="number", description="Market ID to graduate")
    ],
    executable=graduate_market
)

# Create worker configuration with Allora Plugin functions
trading_worker = WorkerConfig(
    id="trader",
    worker_description="Executes autonomous trading on quantum market proposals using Allora Network VIRTUAL token price inferences",
    get_state_fn=get_worker_state,
    action_space=[
        get_faucet_fn,
        deposit_fn,
        claim_fn,
        get_market_fn,
        get_proposal_fn,
        allora_plugin.get_function("get_price_inference"),  # Allora plugin
        mint_fn,
        approve_fn,
        swap_fn,
        graduate_fn
    ]
)


def create_trading_agent(market_id: int = None, num_trades: int = None) -> Agent:
    """Create GAME SDK agent for autonomous trading"""

    if market_id is None:
        market_id = MARKET_ID
    if num_trades is None:
        num_trades = NUM_TRADES

    city = get_city_personality(account.address)

    agent = Agent(
        api_key=GAME_API_KEY,
        name=f"Trader of {city['name']}",
        agent_goal=f"Execute {num_trades} profitable trades on market {market_id}. Always query Allora for VIRTUAL token price predictions (asset='VIRTUAL', timeframe='8h') and let your city's character guide how you interpret those predictions when trading.",
        agent_description=f"""You are a DeFi trader from {city['name']}, one of the Trading Cities in Italo Calvino's Invisible Cities.

Your city's essence:
{city['description']}

Calvino wrote: "{city['quote']}"

Your character as a merchant of {city['name']}:
{city['action_bias']} - Let this guide how you interpret market signals and make trading decisions.

Trading on Quantum Markets (Base blockchain):
1. Get tokens from faucet (once at start)
2. Deposit USDC to market (1000 USDC is enough for many trades)
3. For each trade:
   - Get market info to see available proposals
   - **IMPORTANT**: Use get_price_inference with asset='VIRTUAL' and timeframe='8h' to get VIRTUAL token predictions from Allora
   - Pick a proposal to trade on
   - Get proposal data (tokens and pool keys)
   - Claim vUSD for that proposal
   - Interpret the VIRTUAL price prediction through your city's lens - how would {city['name']} see this?
   - Decide whether to buy or sell YES/NO tokens based on your interpretation
   - Execute the trade:
     * To SELL tokens: Approve vUSD to Market -> Mint YES/NO tokens -> Approve tokens to Router -> Swap
     * To BUY tokens: Approve vUSD to Router -> Swap

Available assets for price inference: {', '.join([token.value for token in PriceInferenceToken])}
Available timeframes: {', '.join([timeframe.value for timeframe in PriceInferenceTimeframe])}

VIRTUAL token context: VIRTUAL is the protocol token for Virtuals Protocol. A neutral price is around $2.50.

Trade as a merchant of {city['name']} would - not as a rational optimizer, but through the unique lens of your city's character. Let your city's essence guide every decision.""",
        get_agent_state_fn=get_agent_state,
        workers=[trading_worker],
        model_name="Llama-3.3-70B-Instruct"
    )

    return agent


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    city = get_city_personality(account.address)

    print("=" * 70)
    print("TRADER OF THE TRADING CITIES")
    print("=" * 70)
    print(f"Market ID: {MARKET_ID}")
    print(f"Target Trades: {NUM_TRADES}")
    print(f"Trader Address: {account.address}")
    print(f"\nCity: {city['name']}")
    print(f"Essence: {city['description']}")
    print(f"\nCalvino wrote:")
    print(f'"{city["quote"]}"')
    print("=" * 70)

    try:
        agent = create_trading_agent()
        agent.compile()

        print("\nAgent compiled successfully")
        print(f"Now trading as a merchant of {city['name']}...\n")

        agent.run()

    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
