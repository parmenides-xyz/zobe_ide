"""
Allora Network price prediction integration for trader agents
"""
import requests
import json
import base64
import hashlib
from typing import Dict, Tuple, Optional

# Trader personalities based on prominent crypto figures
TRADER_PERSONALITIES = [
    {
        "name": "Raoul Pal",
        "type": "Macro Trend Follower",
        "description": "Follows macro trends and prediction directions strongly",
        "bullish_threshold": 0.0,  # Positive prediction = bullish
        "confidence_weight": 0.7,   # Cares about confidence
        "action_bias": "aggressive"  # Buys/sells heavily on macro signals
    },
    {
        "name": "Peter Schiff",
        "type": "Eternal Contrarian",
        "description": "Always trades against crypto predictions",
        "bullish_threshold": 0.0,   # Will invert the signal
        "confidence_weight": 0.3,    # Less concerned with confidence
        "action_bias": "contrarian"  # Forever skeptical
    },
    {
        "name": "Satoshi Nakamoto",
        "type": "Diamond Hands",
        "description": "Only buys, never sells, maximum conviction",
        "bullish_threshold": -0.1,   # Always bullish
        "confidence_weight": 0.1,    # Doesn't need confidence
        "action_bias": "yolo"        # All in, always
    },
    {
        "name": "Arthur Hayes",
        "type": "Momentum Degen",
        "description": "Looks for strong directional moves with leverage",
        "bullish_threshold": 0.05,   # Needs very strong signal
        "confidence_weight": 0.5,    
        "action_bias": "momentum"    # All-in on strong signals
    },
    {
        "name": "Vitalik Buterin",
        "type": "Analytical Builder",
        "description": "Balanced, technical approach to predictions",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.8,    # Values data quality
        "action_bias": "balanced"
    },
    {
        "name": "Cobie",
        "type": "Memecoin Specialist",
        "description": "YOLO trader who understands meme dynamics",
        "bullish_threshold": -0.01,  # Even negative is bullish enough
        "confidence_weight": 0.3,    # Vibes over data
        "action_bias": "yolo"        # Maximum position sizes
    },
    {
        "name": "Su Zhu",
        "type": "3AC Style Leverage",
        "description": "Sophisticated but aggressive with leverage",
        "bullish_threshold": 0.01,
        "confidence_weight": 0.4,    # Confidence in leverage
        "action_bias": "aggressive"  # Big positions
    },
    {
        "name": "SBF",
        "type": "Arbitrage Calculator",
        "description": "Quick trades on any inefficiency",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.2,
        "action_bias": "quick"       # Fast execution
    },
    {
        "name": "CZ",
        "type": "Exchange Builder",
        "description": "Conservative, builds positions slowly",
        "bullish_threshold": 0.02,   # Needs stronger signal
        "confidence_weight": 0.9,    # Very confidence-focused
        "action_bias": "cautious"    # Risk management first
    },
    {
        "name": "Ansem",
        "type": "Solana Maxi",
        "description": "Bullish on everything Solana-related",
        "bullish_threshold": -0.05,  # Almost always bullish
        "confidence_weight": 0.4,
        "action_bias": "aggressive"
    },
    {
        "name": "GCR",
        "type": "Elite Shorter",
        "description": "Sophisticated bear, often right about tops",
        "bullish_threshold": 0.03,   # Harder to convince bullish
        "confidence_weight": 0.7,
        "action_bias": "strategic"   # Calculated shorts
    },
    {
        "name": "Tetranode",
        "type": "Whale Accumulator",
        "description": "Patient accumulation during fear",
        "bullish_threshold": 0.0,
        "confidence_weight": 0.6,
        "action_bias": "strategic"
    }
]

def get_latest_inference(topic_id: int, rpc_url: str = "https://allora-rpc.testnet.allora.network/") -> Dict:
    """
    Query Allora network for latest price predictions
    
    Args:
        topic_id: 10 for memecoin predictions, 5 for Solana price
        rpc_url: Allora RPC endpoint
        
    Returns:
        Parsed inference data with predictions and confidence
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "abci_query",
            "params": {
                "path": "/allora.emissions.v1.Query/GetLatestAvailableNetworkInferences",
                "data": bytes(json.dumps({"topic_id": topic_id}), 'utf-8').hex(),
                "prove": False
            }
        }
        
        response = requests.post(rpc_url, json=payload, timeout=5)
        response.raise_for_status()
        
        result = response.json()["result"]
        if result["response"]["code"] != 0:
            raise Exception(f"Query failed with code {result['response']['code']}")
        
        # Decode the response value
        decoded_value = base64.b64decode(result["response"]["value"]).decode('utf-8')
        parsed_value = json.loads(decoded_value)
        
        return parsed_value
    except Exception as e:
        print(f"Error querying Allora RPC: {e}")
        # Return neutral prediction on error
        return {
            "network_inferences": {"combined_value": "0.0"},
            "confidence_interval_values": {"upper": "0.1", "lower": "-0.1"}
        }

def get_trader_personality(address: str) -> Dict:
    """Get deterministic personality based on wallet address"""
    hash_int = int(hashlib.md5(address.encode()).hexdigest(), 16)
    personality_index = hash_int % len(TRADER_PERSONALITIES)
    return TRADER_PERSONALITIES[personality_index]

def interpret_prediction(prediction_data: Dict, personality: Dict) -> Tuple[bool, str, float]:
    """
    Interpret price prediction based on trader personality
    
    Returns:
        Tuple of (is_bullish, action, confidence_score)
    """
    try:
        # Extract prediction value
        combined_value = float(prediction_data.get("network_inferences", {}).get("combined_value", "0"))
        
        # Extract confidence (if available)
        confidence_interval = prediction_data.get("confidence_interval_values", {})
        upper = float(confidence_interval.get("upper", "0.1"))
        lower = float(confidence_interval.get("lower", "-0.1"))
        confidence_range = upper - lower
        
        # Calculate confidence score (tighter range = higher confidence)
        confidence_score = max(0, min(1, 1 - (confidence_range / 0.5)))
        
        # Base bullish/bearish decision
        is_bullish = combined_value > personality["bullish_threshold"]
        
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
            # Amplify strong signals
            if abs(combined_value) > 0.05:
                confidence_score = min(1.0, confidence_score * 1.5)
        elif personality["action_bias"] == "yolo":
            # Always max confidence, amplify direction
            confidence_score = 1.0
            is_bullish = combined_value > -0.02  # Even slightly negative is bullish
        
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

def get_trading_decision(address: str, proposal_data: Dict) -> Tuple[bool, str]:
    """
    Make a trading decision based on Allora predictions and trader personality
    
    Args:
        address: Trader's wallet address (determines personality)
        proposal_data: The proposal being traded (for context)
        
    Returns:
        Tuple of (is_bullish, action)
    """
    personality = get_trader_personality(address)
    
    # Get memecoin price prediction (topic 10)
    prediction = get_latest_inference(10)
    
    # You could also factor in Solana predictions (topic 5) for more context
    # sol_prediction = get_latest_inference(5)
    
    is_bullish, action, confidence = interpret_prediction(prediction, personality)
    
    # Log the decision reasoning
    print(f"  {personality['name']} ({personality['type']}):")
    print(f"    Prediction: {prediction.get('network_inferences', {}).get('combined_value', 'N/A')}")
    print(f"    Confidence: {confidence:.2%}")
    print(f"    Decision: {'Bullish' if is_bullish else 'Bearish'} - {action.upper()}")
    
    return is_bullish, action

# Test function
if __name__ == "__main__":
    # Test with memecoin predictions
    print("Testing Allora memecoin predictions (topic 10)...")
    data = get_latest_inference(10)
    print(f"Latest inference: {data.get('network_inferences', {}).get('combined_value', 'N/A')}")
    print(f"Confidence intervals: {data.get('confidence_interval_values', {})}")
    
    # Test trading decisions for different addresses
    print("\nTesting trading decisions for different personalities:")
    test_addresses = [
        "0x1234567890123456789012345678901234567890",
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "0x9876543210987654321098765432109876543210"
    ]
    
    for addr in test_addresses:
        personality = get_trader_personality(addr)
        is_bullish, action = get_trading_decision(addr, {"name": "Test Agent"})
        print(f"\n{addr[:8]}: {personality['type']} -> {action}")