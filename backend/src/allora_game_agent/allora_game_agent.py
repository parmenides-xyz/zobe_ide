"""
GAME Worker for Allora Network price prediction - Virtual/USDT only
"""
import os
import sys
import asyncio
import hashlib
from typing import Dict, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from allora_sdk import AlloraAPIClient
from allora_sdk.api_client import ChainID, SignatureFormat
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, FunctionResultStatus
from src.cities import INVISIBLE_CITIES

# Initialize Allora client
allora_client = AlloraAPIClient(
    chain_id=ChainID.TESTNET,
    api_key=os.getenv("ALLORA_API_KEY", "UP-220d05d2c2cd4685ae1ef6b8")
)

# Virtual/USDT topic ID on Allora Network
VIRTUAL_TOPIC_ID = 31

# Cache for Virtual price (refresh every minute)
_virtual_price_cache = None
_cache_timestamp = None

def create_allora_worker(api_key: str = None) -> Worker:
    """
    Create a GAME Worker that fetches Virtual/USDT price from Allora Network

    Args:
        api_key: GAME API key for the worker

    Returns:
        Configured GAME Worker
    """
    if api_key is None:
        api_key = os.getenv("GAME_API_KEY_1")  # Use first API key

    def get_virtual_price_impl(**kwargs) -> Tuple[FunctionResultStatus, str, Dict]:
        """Fetch Virtual/USDT 8h price prediction from Allora Network"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()

            inference = loop.run_until_complete(
                allora_client.get_inference_by_topic_id(
                    topic_id=VIRTUAL_TOPIC_ID,
                    signature_format=SignatureFormat.ETHEREUM_SEPOLIA
                )
            )

            price = float(inference.inference_data.network_inference_normalized)

            # Determine sentiment based on price
            if price > 25:
                sentiment = "VERY_BULLISH"
            elif price > 20:
                sentiment = "BULLISH"
            elif price > 15:
                sentiment = "NEUTRAL"
            elif price > 10:
                sentiment = "BEARISH"
            else:
                sentiment = "VERY_BEARISH"

            message = f"Virtual/USDT 8h prediction: ${price:.2f} ({sentiment})"

            return (
                FunctionResultStatus.DONE,
                message,
                {
                    "price": price,
                    "sentiment": sentiment,
                    "token": "Virtual/USDT"
                }
            )

        except Exception as e:
            # Default to $20 (neutral) on error
            return (
                FunctionResultStatus.FAILED,
                f"Failed to fetch Virtual price: {e}. Using default $20",
                {"price": 20.0, "sentiment": "NEUTRAL", "token": "Virtual/USDT"}
            )

    # Create GAME function
    virtual_price_function = Function(
        fn_name="get_virtual_price",
        fn_description="Get Virtual/USDT 8-hour price prediction from Allora Network",
        args=[],
        executable=get_virtual_price_impl
    )

    # Create and return Worker
    worker = Worker(
        api_key=api_key,
        description="Allora Network price oracle for Virtual/USDT token predictions",
        action_space=[virtual_price_function],
        get_state_fn=lambda: {"status": "ready"}
    )

    return worker


async def get_virtual_price() -> float:
    """
    Get Virtual/USDT price prediction (with caching)

    Returns:
        Virtual price in USDT
    """
    global _virtual_price_cache, _cache_timestamp

    import time
    current_time = time.time()

    # Use cache if available and fresh (< 60 seconds old)
    if _virtual_price_cache is not None and _cache_timestamp is not None:
        if current_time - _cache_timestamp < 60:
            return _virtual_price_cache

    try:
        inference = await allora_client.get_inference_by_topic_id(
            topic_id=VIRTUAL_TOPIC_ID,
            signature_format=SignatureFormat.ETHEREUM_SEPOLIA
        )
        price = float(inference.inference_data.network_inference_normalized)

        # Update cache
        _virtual_price_cache = price
        _cache_timestamp = current_time

        return price
    except Exception as e:
        print(f"Error fetching Virtual price: {e}")
        # Return cached value if available, else default to $20
        return _virtual_price_cache if _virtual_price_cache is not None else 20.0


def get_trader_personality(address: str) -> Dict:
    """Get deterministic Invisible City personality based on wallet address"""
    hash_int = int(hashlib.md5(address.encode()).hexdigest(), 16)
    personality_index = hash_int % len(INVISIBLE_CITIES)
    return INVISIBLE_CITIES[personality_index]


def interpret_virtual_price(virtual_price: float, personality: Dict) -> Tuple[bool, str, float]:
    """
    Interpret Virtual/USDT price based on Invisible City personality

    Args:
        virtual_price: Virtual token price in USDT
        personality: Invisible City personality dict

    Returns:
        Tuple of (is_bullish, action, confidence_score)
    """
    try:
        # Baseline: $20 is neutral for Virtual
        # Above $20 = bullish sentiment, below = bearish
        sentiment_score = (virtual_price - 20) / 20  # Normalize to -1 to 1

        # Confidence based on distance from neutral
        # Further from $20 = higher confidence
        confidence_score = min(1.0, abs(sentiment_score) * 2 + 0.3)

        # Base bullish/bearish decision
        is_bullish = sentiment_score > personality["bullish_threshold"]

        # Apply personality-specific interpretation
        action_bias = personality["action_bias"]

        if action_bias == "contrarian":
            # Euphemia: Do opposite of market
            is_bullish = not is_bullish
            action = "sell" if is_bullish else "buy"

        elif action_bias == "momentum":
            # Chloe: Amplify strong moves
            if abs(sentiment_score) > 0.2:  # Strong move
                confidence_score = min(1.0, confidence_score * 1.5)
            action = "buy" if is_bullish else "sell"

        elif action_bias == "cyclical":
            # Eutropia: Mean reversion - buy dips, sell rips
            if virtual_price < 15:  # Deep dip
                is_bullish = True
                action = "buy"
            elif virtual_price > 25:  # Overbought
                is_bullish = False
                action = "sell"
            else:
                action = "buy" if is_bullish else "sell"

        elif action_bias == "network":
            # Ersilia: Wait for confirmation, slightly cautious
            if confidence_score < personality["confidence_weight"]:
                # Uncertain, default to sell
                is_bullish = False
                action = "sell"
            else:
                action = "buy" if is_bullish else "sell"

        elif action_bias == "hedging":
            # Esmeralda: Both sides - but pick one for this trade
            # Alternates based on price position
            if virtual_price % 2 < 1:  # Simple alternation logic
                action = "buy" if is_bullish else "sell"
            else:
                action = "sell" if is_bullish else "buy"
        else:
            # Default balanced approach
            action = "buy" if is_bullish else "sell"

        return is_bullish, action, confidence_score

    except Exception as e:
        print(f"Error interpreting Virtual price: {e}")
        # Default to slightly bearish on error
        return False, "sell", 0.3


async def get_trading_decision(address: str, proposal_data: Dict = None) -> Tuple[bool, str]:
    """
    Make a trading decision based on Virtual price and Invisible City personality

    Args:
        address: Trader's wallet address (determines personality)
        proposal_data: The proposal being traded (optional context)

    Returns:
        Tuple of (is_bullish, action)
    """
    personality = get_trader_personality(address)

    # Get Virtual/USDT 8-hour price prediction
    virtual_price = await get_virtual_price()

    is_bullish, action, confidence = interpret_virtual_price(virtual_price, personality)

    # Determine market strength
    if virtual_price > 25:
        market_strength = "Very Strong"
    elif virtual_price > 20:
        market_strength = "Strong"
    elif virtual_price > 15:
        market_strength = "Neutral"
    elif virtual_price > 10:
        market_strength = "Weak"
    else:
        market_strength = "Very Weak"

    # Extract proposal name
    proposal_name = "AI Agent"
    if proposal_data and 'name' in proposal_data:
        proposal_name = proposal_data['name']

    # Log personality-specific trading strategy
    print(f"\n  {personality['name']} ({personality['theme']}):")
    print(f"    Proposal: {proposal_name}")
    print(f"    Virtual Price: ${virtual_price:.2f} ({market_strength})")
    print(f"    Philosophy: {personality['trading_philosophy']}")

    # Personality-specific interpretation
    city_name = personality['name']

    if city_name == "Euphemia":
        print(f"    → Contrarian: {'Selling into strength' if is_bullish else 'Buying the dip'}")
    elif city_name == "Chloe":
        print(f"    → Momentum: {'Riding the trend up' if is_bullish else 'Following breakdown'}")
    elif city_name == "Eutropia":
        print(f"    → Cyclical: {'Waiting for cycle turn' if abs(virtual_price - 20) < 5 else 'Trading the cycle'}")
    elif city_name == "Ersilia":
        print(f"    → Network: {'Following smart money' if is_bullish else 'Network signals bearish'}")
    elif city_name == "Esmeralda":
        print(f"    → Hedging: {'Opening long position' if is_bullish else 'Opening short position'}")

    # Trading action on YES/NO tokens
    if is_bullish:
        if action == 'buy':
            print(f"    Decision: BUY YES tokens (bullish on {proposal_name})")
        else:
            print(f"    Decision: SELL NO tokens (doesn't believe it will fail)")
    else:
        if action == 'buy':
            print(f"    Decision: BUY NO tokens (bearish on {proposal_name})")
        else:
            print(f"    Decision: SELL YES tokens (skeptical of success)")
    print(f"    Confidence: {confidence:.0%}")

    return is_bullish, action


# Test function
if __name__ == "__main__":
    async def test_virtual_price():
        print("Testing Virtual/USDT Price Prediction from Allora Network")
        print("="*60)

        price = await get_virtual_price()
        print(f"Virtual/USDT 8h Prediction: ${price:.2f}")

        if price > 25:
            print("Market Sentiment: VERY BULLISH")
        elif price > 20:
            print("Market Sentiment: BULLISH")
        elif price > 15:
            print("Market Sentiment: NEUTRAL")
        elif price > 10:
            print("Market Sentiment: BEARISH")
        else:
            print("Market Sentiment: VERY BEARISH")

        return price

    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        virtual_price = loop.run_until_complete(test_virtual_price())
    finally:
        loop.close()

    # Test trading decisions for different addresses (map to 5 cities)
    print("\nTesting Invisible Cities Trading Decisions:")
    print("="*60)
    test_addresses = [
        "0x1111111111111111111111111111111111111111",  # Euphemia
        "0x2222222222222222222222222222222222222222",  # Chloe
        "0x3333333333333333333333333333333333333333",  # Eutropia
        "0x4444444444444444444444444444444444444444",  # Ersilia
        "0x5555555555555555555555555555555555555555",  # Esmeralda
    ]

    async def test_trading():
        for addr in test_addresses:
            print(f"\nTesting address: {addr[:8]}...")
            personality = get_trader_personality(addr)
            is_bullish, action = await get_trading_decision(addr)
            print(f"  Final: {personality['name']} -> {action.upper()}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_trading())
    finally:
        loop.close()