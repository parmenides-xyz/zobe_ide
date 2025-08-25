"""
Allora Network price prediction integration for trader agents with personality-based trading
"""
import os
import sys
import asyncio
import hashlib
from typing import Dict, Tuple, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from allora_sdk import AlloraAPIClient
from allora_sdk.v2.api_client import ChainSlug, SignatureFormat

# Trader personalities based on prominent crypto/tech founders
TRADER_PERSONALITIES = [
    {
        "name": "Illia Polosukhin",
        "type": "Founder of NEAR Protocol",
        "description": "AI-focused, technical approach to blockchain",
        "bullish_threshold": 0.0,  # Positive AI sentiment = bullish
        "confidence_weight": 0.7,   # Values AI predictions
        "action_bias": "aggressive"  # Believes in AI narrative
    },
    {
        "name": "Brian Armstrong",
        "type": "Founder of Coinbase",
        "description": "Regulatory-conscious, institutional approach",
        "bullish_threshold": 0.1,   # Needs clearer signals
        "confidence_weight": 0.8,    # High confidence required
        "action_bias": "cautious"   # Conservative, compliance-first
    },
    {
        "name": "Satoshi Nakamoto",
        "type": "Founder of Bitcoin",
        "description": "Only buys, never sells, maximum conviction",
        "bullish_threshold": -0.1,   # Always bullish
        "confidence_weight": 0.1,    # Doesn't need confidence
        "action_bias": "yolo"        # All in, always
    },
    {
        "name": "Michael Saylor",
        "type": "Founder of Strategy",
        "description": "All-in conviction trader, never sells",
        "bullish_threshold": -0.2,   # Always extremely bullish
        "confidence_weight": 0.0,    # Ignores short-term signals
        "action_bias": "yolo"        # Maximum conviction buys
    },
    {
        "name": "Vitalik Buterin",
        "type": "Founder of Ethereum",
        "description": "Balanced, technical approach to predictions",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.8,    # Values data quality
        "action_bias": "balanced"
    },
    {
        "name": "ZachXBT",
        "type": "On-chain Detective",
        "description": "Skeptical investigator, sells on red flags",
        "bullish_threshold": 0.2,    # Hard to convince
        "confidence_weight": 0.9,    # Needs strong evidence
        "action_bias": "strategic"   # Calculated, investigative
    },
    {
        "name": "Yat Siu",
        "type": "Founder of Animoca Brands",
        "description": "Gaming & metaverse bull, aggressive on trends",
        "bullish_threshold": -0.05,  # Optimistic on gaming/AI
        "confidence_weight": 0.4,    # Trend-focused
        "action_bias": "aggressive"  # Big on narrative plays
    },
    {
        "name": "Rune Christensen",
        "type": "Founder of MakerDAO",
        "description": "DeFi architect, systematic approach",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.7,    # Data-driven
        "action_bias": "balanced"    # Measured DeFi approach
    },
    {
        "name": "CZ",
        "type": "Founder of Binance",
        "description": "Conservative, builds positions slowly",
        "bullish_threshold": 0.02,   # Needs stronger signal
        "confidence_weight": 0.9,    # Very confidence-focused
        "action_bias": "cautious"    # Risk management first
    },
    {
        "name": "Larry Fink",
        "type": "Founder of BlackRock",
        "description": "Institutional accumulator, long-term focused",
        "bullish_threshold": 0.05,   # Quality threshold
        "confidence_weight": 0.8,    # Institutional standards
        "action_bias": "strategic"   # Systematic accumulation
    },
    {
        "name": "Jeff Yan",
        "type": "Founder of Hyperliquid",
        "description": "High-frequency trader, quick decisions",
        "bullish_threshold": 0.0,    # Neutral starting point
        "confidence_weight": 0.5,    # Speed over certainty
        "action_bias": "momentum"    # Fast execution on signals
    },
    {
        "name": "Justin Sun",
        "type": "Founder of TRON",
        "description": "Marketing genius, buys the hype",
        "bullish_threshold": -0.1,   # Easy to excite
        "confidence_weight": 0.2,    # Hype over fundamentals
        "action_bias": "aggressive"  # Big marketing plays
    }
]

# Initialize Allora client
client = AlloraAPIClient(
    chain_slug=ChainSlug.TESTNET,
    api_key=os.getenv("ALLORA_API_KEY", "UP-8cbc632a67a84ac1b4078661")
)

# AI Token topic mappings
AI_TOKEN_TOPICS = {
    31: "Virtual/USDT",
    32: "Aixbt/USDT", 
    34: "VaderAI/USDT",
    36: "Sekoia/USDT"
}

# Cache for AI predictions (fetch once at startup)
_ai_predictions_cache = None
_cache_timestamp = None

async def get_ai_token_predictions(force_refresh: bool = False) -> Dict[str, float]:
    """
    Get price predictions for all AI tokens (cached after first fetch)
    Returns dict of token_name -> price prediction
    """
    global _ai_predictions_cache
    
    # Return cached predictions if available and not forcing refresh
    if _ai_predictions_cache is not None and not force_refresh:
        return _ai_predictions_cache
    
    # Fetch fresh predictions
    predictions = {}
    print("Fetching AI token predictions from Allora Network (one-time)...")
    
    for topic_id, name in AI_TOKEN_TOPICS.items():
        try:
            inference = await client.get_inference_by_topic_id(
                topic_id=topic_id,
                signature_format=SignatureFormat.ETHEREUM_SEPOLIA
            )
            price = float(inference.inference_data.network_inference_normalized)
            predictions[name] = price
            print(f"  {name}: ${price:.2f}")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            # Use reasonable defaults based on typical values
            defaults = {
                "Virtual/USDT": 20.0,
                "Aixbt/USDT": 52.0,
                "VaderAI/USDT": 51.0,
                "Sekoia/USDT": 100.0
            }
            predictions[name] = defaults.get(name, 50.0)
    
    # Cache the predictions
    _ai_predictions_cache = predictions
    return predictions

def calculate_ai_market_sentiment(predictions: Dict[str, float]) -> float:
    """
    Calculate overall AI market sentiment from token predictions
    Returns a value between -1 (very bearish) and 1 (very bullish)
    """
    if not predictions:
        return 0.0
    
    # Simple average for now, could weight by market cap later
    avg_price = sum(predictions.values()) / len(predictions)
    
    # Normalize to sentiment score
    # Assuming average AI token price of ~50 USDT as neutral
    sentiment = (avg_price - 50) / 50  # -1 to 1 range
    return max(-1, min(1, sentiment))

def get_trader_personality(address: str) -> Dict:
    """Get deterministic personality based on wallet address"""
    hash_int = int(hashlib.md5(address.encode()).hexdigest(), 16)
    personality_index = hash_int % len(TRADER_PERSONALITIES)
    return TRADER_PERSONALITIES[personality_index]

def interpret_ai_market_prediction(ai_predictions: Dict[str, float], personality: Dict) -> Tuple[bool, str, float]:
    """
    Interpret AI token 8-hour price predictions based on trader personality
    
    Args:
        ai_predictions: Dict of AI token prices (8h predictions)
        personality: Trader personality dict
    
    Returns:
        Tuple of (is_bullish, action, confidence_score)
    """
    try:
        # Calculate market sentiment from AI token prices
        avg_price = sum(ai_predictions.values()) / len(ai_predictions) if ai_predictions else 50
        
        # Key thresholds for AI tokens
        # Virtual ~$20, Aixbt ~$52, VaderAI ~$51, Sekoia ~$100
        # Average ~$55 is neutral, above is bullish, below is bearish
        sentiment_score = (avg_price - 55) / 55  # Normalize to -1 to 1
        
        # Calculate confidence based on consistency of predictions
        prices = list(ai_predictions.values())
        if len(prices) > 1:
            price_variance = max(prices) - min(prices)
            # Lower variance = higher confidence
            confidence_score = max(0.3, min(1.0, 1 - (price_variance / 100)))
        else:
            confidence_score = 0.5
        
        # Base bullish/bearish decision based on AI market sentiment
        is_bullish = sentiment_score > personality["bullish_threshold"]
        
        # Apply personality-specific interpretation
        if personality["action_bias"] == "contrarian":
            is_bullish = not is_bullish  # Invert signal
        elif personality["action_bias"] == "cautious":
            # Only trade if confidence is high
            if confidence_score < personality["confidence_weight"]:
                # Too uncertain, default to slight bearish
                is_bullish = False
                confidence_score *= 0.5
        elif personality["action_bias"] == "momentum":
            # Amplify strong AI market moves
            if abs(sentiment_score) > 0.2:  # Strong move in AI tokens
                confidence_score = min(1.0, confidence_score * 1.5)
        elif personality["action_bias"] == "yolo":
            # Always max confidence on AI narrative
            confidence_score = 1.0
            is_bullish = avg_price > 40  # Any decent AI price is bullish
        
        # Determine action based on personality and confidence
        if personality["action_bias"] in ["aggressive", "yolo", "momentum"]:
            action = "buy" if is_bullish else "sell"
        elif personality["action_bias"] in ["cautious", "conservative"]:
            # More likely to sell (take profits) when uncertain
            if confidence_score < 0.5:
                action = "sell"
            else:
                action = "buy" if is_bullish else "sell"
        elif personality["action_bias"] == "contrarian":
            action = "sell" if is_bullish else "buy"  # Do opposite
        else:
            # Balanced approach
            action = "buy" if (is_bullish and confidence_score > 0.3) else "sell"
        
        return is_bullish, action, confidence_score
        
    except Exception as e:
        print(f"Error interpreting prediction: {e}")
        # Default to slightly bearish on error
        return False, "sell", 0.3

async def get_trading_decision(address: str, proposal_data: Dict = None) -> Tuple[bool, str]:
    """
    Make a trading decision based on AI token 8h predictions and trader personality
    
    Args:
        address: Trader's wallet address (determines personality)
        proposal_data: The proposal being traded (optional context)
        
    Returns:
        Tuple of (is_bullish, action)
    """
    personality = get_trader_personality(address)
    
    # Get AI token 8-hour price predictions (now properly async)
    ai_predictions = await get_ai_token_predictions()
    
    is_bullish, action, confidence = interpret_ai_market_prediction(ai_predictions, personality)
    
    # Calculate market metrics
    avg_price = sum(ai_predictions.values()) / len(ai_predictions) if ai_predictions else 0
    market_strength = "Strong" if avg_price > 55 else "Weak" if avg_price < 45 else "Neutral"
    
    # Extract proposal name
    proposal_name = "AI Agent"
    if proposal_data and 'name' in proposal_data:
        proposal_name = proposal_data['name']
    
    # Log personality-specific trading strategy
    print(f"\n  {personality['name']} ({personality['type']}):")
    print(f"    Proposal: {proposal_name}")
    print(f"    AI Market: ${avg_price:.2f} ({market_strength})")
    
    # Personality-specific interpretation
    if personality['name'] == "Michael Saylor":
        print(f"    → Always bullish, buying YES regardless of AI prices")
    elif personality['name'] == "ZachXBT":
        print(f"    → Skeptical of AI hype, needs strong evidence")
    elif personality['name'] == "Illia Polosukhin":
        print(f"    → AI founder: {market_strength} market = {'bullish opportunity' if is_bullish else 'wait for better entry'}")
    elif personality['name'] == "Justin Sun":
        print(f"    → {'FOMO buying YES' if avg_price > 50 else 'Waiting for hype'}")
    elif personality['name'] == "Larry Fink":
        print(f"    → Institutional: {'Quality met, accumulating' if is_bullish else 'Below standards'}")
    elif personality['name'] == "Brian Armstrong":
        print(f"    → {'Proceeding with caution' if confidence > 0.7 else 'Regulatory concerns'}")
    elif personality['name'] == "Jeff Yan":
        print(f"    → High-freq: {'Momentum detected' if abs(avg_price - 55) > 10 else 'Waiting for signal'}")
    elif personality['name'] == "Yat Siu":
        print(f"    → Gaming/AI bull: {'Perfect narrative play' if is_bullish else 'Temporary weakness'}")
    elif personality['name'] == "Vitalik Buterin":
        print(f"    → Technical analysis: {confidence:.0%} confidence in signal")
    else:
        print(f"    → {personality['description']}")
    
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
    async def test_ai_predictions():
        print("Fetching AI Token 8-Hour Price Predictions...")
        print("="*50)
        
        predictions = await get_ai_token_predictions()
        for token, price in predictions.items():
            print(f"{token}: ${price:.2f}")
        
        avg_price = sum(predictions.values()) / len(predictions) if predictions else 0
        print(f"\nAverage AI Token Price: ${avg_price:.2f}")
        sentiment = "BULLISH" if avg_price > 55 else "BEARISH" if avg_price < 45 else "NEUTRAL"
        print(f"Market Sentiment: {sentiment}")
        
        return predictions
    
    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ai_preds = loop.run_until_complete(test_ai_predictions())
    finally:
        loop.close()
    
    # Test trading decisions for different addresses
    print("\nTesting trading decisions for different personalities:")
    print("="*50)
    test_addresses = [
        "0x1234567890123456789012345678901234567890",
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "0x9876543210987654321098765432109876543210"
    ]
    
    async def test_trading():
        for addr in test_addresses:
            print(f"\nAddress: {addr[:8]}...")
            personality = get_trader_personality(addr)
            is_bullish, action = await get_trading_decision(addr)
            print(f"  Final: {personality['type']} -> {action.upper()}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_trading())
    finally:
        loop.close()