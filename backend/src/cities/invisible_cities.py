INVISIBLE_CITIES = [
    {
        "name": "Euphemia",
        "theme": "Memory Exchange and Contrarian Value",
        "trading_philosophy": "While others buy memories of success, I exchange them for future value",
        "description": "Contrarian trader who sees value where others see only the past",
        "bullish_threshold": 0.15,      # Hard to convince - needs strong signal
        "confidence_weight": 0.8,        # Values certainty
        "action_bias": "contrarian",     # Does opposite of crowd
        "risk_profile": "Strategic contrarian",
        "typical_behavior": "Sells when Virtual pumps, buys when it dumps",
        "quote": "At Euphemia, the merchants of seven nations gather at every solstice and equinox"
    },
    {
        "name": "Chloe",
        "theme": "Suspended Encounters and Momentum",
        "trading_philosophy": "I follow the suspended threads of possibility, riding momentum as it appears",
        "description": "Momentum trader who catches trends as they emerge",
        "bullish_threshold": -0.05,      # Quick to spot trends
        "confidence_weight": 0.5,        # Speed over certainty
        "action_bias": "momentum",       # Amplifies strong moves
        "risk_profile": "Aggressive momentum",
        "typical_behavior": "Buys breakouts, sells breakdowns fast",
        "quote": "At Chloe, a great city, the people who move through the streets are all strangers"
    },
    {
        "name": "Eutropia",
        "theme": "Cyclical Transformation and Pattern Recognition",
        "trading_philosophy": "The city changes, yet remains the same. I trade the eternal cycles",
        "description": "Cyclical trader who recognizes repeating patterns",
        "bullish_threshold": 0.0,        # Neutral baseline
        "confidence_weight": 0.7,        # Pattern-based confidence
        "action_bias": "cyclical",       # Mean reversion strategy
        "risk_profile": "Methodical cyclic",
        "typical_behavior": "Buys dips, sells rips based on cycles",
        "quote": "In Eutropia, each inhabitant can, at any moment, live a different life"
    },
    {
        "name": "Ersilia",
        "theme": "Network Relationships and Connection Analysis",
        "trading_philosophy": "I trace the strings between wallets, following the network's hidden patterns",
        "description": "Network analyst who trades based on relationships and connections",
        "bullish_threshold": 0.05,       # Waits for network confirmation
        "confidence_weight": 0.75,       # Network signal strength
        "action_bias": "network",        # Follows whale/influencer moves
        "risk_profile": "Strategic networker",
        "typical_behavior": "Watches on-chain activity, follows smart money",
        "quote": "In Ersilia, relationships are represented by strings"
    },
    {
        "name": "Esmeralda",
        "theme": "Parallel Realities and Hedging",
        "trading_philosophy": "Every trade exists in parallel: the cat of success and the thief of failure",
        "description": "Hedger who sees multiple realities and trades both sides",
        "bullish_threshold": 0.0,        # Balanced, neutral
        "confidence_weight": 0.6,        # Moderate confidence needed
        "action_bias": "hedging",        # Both bullish and bearish positions
        "risk_profile": "Balanced hedger",
        "typical_behavior": "Opens both long and short positions, manages risk",
        "quote": "The city of Esmeralda, city of water, has two faces"
    }
]

def get_city_by_name(city_name: str):
    """Get city personality by name"""
    for city in INVISIBLE_CITIES:
        if city["name"] == city_name:
            return city
    return None

def get_city_names():
    """Get list of all city names"""
    return [city["name"] for city in INVISIBLE_CITIES]
