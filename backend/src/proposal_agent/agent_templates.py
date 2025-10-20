"""
AI Agent Proposal Templates for Virtuals Protocol
Based on GAME SDK plugins: Allora, CDP, Bittensor, Twitter, Telegram, etc.
"""

HARDCODED_PROPOSALS = [
    # Allora Network Agents
    {
        "name": "Allora Price Oracle",
        "symbol": "APO",
        "description": "AI agent that fetches real-time price inferences from Allora Network for trading decisions",
        "capabilities": ["allora.get_price_inference", "allora.get_inference_by_topic_id"],
        "strategy": "Query Allora Network for BTC, ETH, and Virtual price predictions across multiple timeframes"
    },
    {
        "name": "Allora Sentiment Analyzer",
        "symbol": "ASA",
        "description": "Analyzes market sentiment using Allora's AI-powered price predictions",
        "capabilities": ["allora.get_all_topics", "allora.get_inference_by_topic_id"],
        "strategy": "Track sentiment changes across multiple AI tokens and crypto assets"
    },

    # CDP (Coinbase Developer Platform) Agents
    {
        "name": "CDP Trading Bot",
        "symbol": "CTB",
        "description": "Automated trading agent using Coinbase CDP for ETH/USDC pairs",
        "capabilities": ["cdp.trade", "cdp.get_balance", "cdp.request_faucet_funds"],
        "strategy": "Execute trades on Base network with gasless USDC transfers"
    },
    {
        "name": "CDP Wallet Manager",
        "symbol": "CWM",
        "description": "Multi-wallet management agent for Base network operations",
        "capabilities": ["cdp.create_wallet", "cdp.transfer", "cdp.get_transfer_history"],
        "strategy": "Create and manage multiple wallets for diversified trading strategies"
    },
    {
        "name": "CDP Yield Optimizer",
        "symbol": "CYO",
        "description": "Optimizes yields by monitoring and rebalancing positions on Base",
        "capabilities": ["cdp.get_balance", "cdp.trade", "cdp.transfer"],
        "strategy": "Monitor wallet balances and execute profitable arbitrage opportunities"
    },

    # Bittensor Agents
    {
        "name": "Bittensor AI Detector",
        "symbol": "BAD",
        "description": "Detects AI-generated images using Bittensor subnet 34",
        "capabilities": ["bittensor.call_subnet", "bittensor.image_detection"],
        "strategy": "Verify authenticity of NFTs and digital content before trading"
    },
    {
        "name": "Bittensor Content Validator",
        "symbol": "BCV",
        "description": "Validates content authenticity across social media and marketplaces",
        "capabilities": ["bittensor.call_subnet"],
        "strategy": "Screen AI-generated content to protect against deepfakes and fraud"
    },

    # Twitter Plugin Agents
    {
        "name": "Twitter Sentiment Bot",
        "symbol": "TSB",
        "description": "Tracks crypto Twitter sentiment and engagement metrics",
        "capabilities": ["twitter.post_tweet", "twitter.search_tweets", "twitter.get_mentions"],
        "strategy": "Analyze social sentiment to predict market movements"
    },
    {
        "name": "Twitter Alpha Hunter",
        "symbol": "TAH",
        "description": "Monitors crypto Twitter for alpha and early signals",
        "capabilities": ["twitter.search_tweets", "twitter.get_user_tweets"],
        "strategy": "Track influencer activity and viral trends for trading edge"
    },

    # Telegram Plugin Agents
    {
        "name": "Telegram Alert Bot",
        "symbol": "TAB",
        "description": "Sends real-time trading alerts via Telegram",
        "capabilities": ["telegram.send_message", "telegram.create_group"],
        "strategy": "Notify users of price movements, whale transactions, and opportunities"
    },
    {
        "name": "Telegram Signal Aggregator",
        "symbol": "TSA",
        "description": "Aggregates trading signals from multiple Telegram channels",
        "capabilities": ["telegram.get_messages", "telegram.send_message"],
        "strategy": "Compile and analyze signals from top crypto Telegram groups"
    },

    # Image Generation Agents
    {
        "name": "NFT Art Generator",
        "symbol": "NAG",
        "description": "Generates unique AI art for NFT collections",
        "capabilities": ["imagegen.generate", "imagegen.style_transfer"],
        "strategy": "Create distinctive NFT artwork using AI image generation"
    },

    # Multi-Plugin Combination Agents
    {
        "name": "Virtual Ecosystem Monitor",
        "symbol": "VEM",
        "description": "Monitors Virtual protocol ecosystem using Allora + Twitter + CDP",
        "capabilities": ["allora.get_price_inference", "twitter.search_tweets", "cdp.get_balance"],
        "strategy": "Track Virtual token price, social sentiment, and execute trades"
    },
    {
        "name": "Cross-Chain Arbitrage Bot",
        "symbol": "CAB",
        "description": "Executes arbitrage across chains using CDP and price oracles",
        "capabilities": ["cdp.trade", "allora.get_price_inference", "cdp.transfer"],
        "strategy": "Identify and execute profitable cross-chain arbitrage opportunities"
    },
    {
        "name": "Social Trading Alpha",
        "symbol": "STA",
        "description": "Combines social signals with trading execution",
        "capabilities": ["twitter.search_tweets", "telegram.get_messages", "cdp.trade"],
        "strategy": "Execute trades based on aggregated social sentiment"
    }
]

# For backward compatibility
AGENT_PROPOSALS = HARDCODED_PROPOSALS
