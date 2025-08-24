"""
Simple LLM Engine for generating agent proposals using Claude API
"""
import os
import json
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

def generate_agent_proposals(num_proposals: int = 15) -> List[Dict]:
    """
    Generate agent proposals using Claude API
    
    Returns:
        List of proposal dictionaries
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("No Anthropic API key found, using hardcoded proposals")
        return get_hardcoded_proposals()[:num_proposals]
    
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
                'max_tokens': 2000,
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
            json_match = ai_response[ai_response.find('['):ai_response.rfind(']')+1]
            if json_match:
                proposals = json.loads(json_match)
                print(f"Generated {len(proposals)} proposals via Claude API")
                return proposals[:num_proposals]
        else:
            print(f"Claude API error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error calling Claude API: {e}")
    
    return get_hardcoded_proposals()[:num_proposals]

def get_hardcoded_proposals() -> List[Dict]:
    """Fallback hardcoded proposals if API fails"""
    return [
        {
            "name": "Yield Hunter Pro",
            "symbol": "YHP",
            "description": "Automatically finds and captures the highest yields across DeFi protocols",
            "capabilities": ["yield.scan", "auto.compound", "risk.assess"],
            "strategy": "Continuously scan protocols and reallocate funds to highest risk-adjusted yields"
        },
        {
            "name": "Liquidation Shield",
            "symbol": "LQSH",
            "description": "Protects lending positions from liquidation through automated repayments",
            "capabilities": ["health.monitor", "flash.loan", "auto.repay"],
            "strategy": "Monitor health factors and execute defensive actions before liquidation"
        },
        {
            "name": "Arbitrage Scanner",
            "symbol": "ARBX",
            "description": "Identifies and executes cross-DEX arbitrage opportunities",
            "capabilities": ["price.compare", "route.optimize", "flash.execute"],
            "strategy": "Scan price differences across venues and execute profitable trades"
        },
        {
            "name": "Market Maker Bot",
            "symbol": "MMB",
            "description": "Provides liquidity through automated market making strategies",
            "capabilities": ["order.create", "spread.manage", "inventory.balance"],
            "strategy": "Maintain bid-ask spreads and rebalance positions based on volatility"
        },
        {
            "name": "DCA Accumulator",
            "symbol": "DCA",
            "description": "Executes dollar-cost averaging strategies for long-term accumulation",
            "capabilities": ["schedule.buy", "price.track", "portfolio.monitor"],
            "strategy": "Execute periodic buys to accumulate positions over time"
        },
        {
            "name": "Range Order Bot",
            "symbol": "RANG",
            "description": "Executes range-bound trading strategies with limit orders",
            "capabilities": ["range.define", "order.place", "position.manage"],
            "strategy": "Profit from price oscillations within defined ranges"
        },
        {
            "name": "Staking Optimizer",
            "symbol": "SOPT",
            "description": "Optimizes staking rewards across different validators and protocols",
            "capabilities": ["validator.analyze", "stake.delegate", "reward.compound"],
            "strategy": "Distribute stake for optimal rewards while maintaining decentralization"
        },
        {
            "name": "Flash Loan Expert",
            "symbol": "FLEX",
            "description": "Executes complex flash loan strategies for arbitrage and liquidations",
            "capabilities": ["flash.borrow", "multi.execute", "profit.calculate"],
            "strategy": "Chain multiple operations within flash loans for capital-efficient trades"
        },
        {
            "name": "Portfolio Rebalancer",
            "symbol": "PBAL",
            "description": "Maintains target portfolio allocations through automated rebalancing",
            "capabilities": ["allocation.track", "drift.detect", "rebalance.execute"],
            "strategy": "Monitor portfolio drift and execute rebalancing trades at optimal times"
        },
        {
            "name": "MEV Protector",
            "symbol": "MEVP",
            "description": "Protects transactions from MEV attacks and sandwich trades",
            "capabilities": ["mempool.hide", "route.private", "timing.optimize"],
            "strategy": "Use private mempools and optimized routing to avoid MEV extraction"
        },
        {
            "name": "Yield Aggregator",
            "symbol": "YAGG",
            "description": "Aggregates yield opportunities across all Sei DeFi protocols",
            "capabilities": ["protocol.scan", "yield.compare", "capital.deploy"],
            "strategy": "Continuously scan and reallocate capital to highest yielding opportunities"
        },
        {
            "name": "Liquidity Sniper",
            "symbol": "LSNP",
            "description": "Identifies and captures new liquidity opportunities instantly",
            "capabilities": ["pool.detect", "liquidity.provide", "position.hedge"],
            "strategy": "Monitor for new pool deployments and be first to provide liquidity"
        },
        {
            "name": "Bridge Arbitrageur",
            "symbol": "XBRG",
            "description": "Executes cross-chain arbitrage through bridge protocols",
            "capabilities": ["bridge.monitor", "price.compare", "route.execute"],
            "strategy": "Find optimal bridging routes and execute cross-chain arbitrage"
        },
        {
            "name": "Options Hedger",
            "symbol": "OHDG",
            "description": "Creates synthetic options positions for portfolio hedging",
            "capabilities": ["option.create", "greek.calculate", "hedge.adjust"],
            "strategy": "Build and manage options strategies using DeFi primitives"
        },
        {
            "name": "Momentum Trader",
            "symbol": "MOMT",
            "description": "Follows market trends using momentum indicators",
            "capabilities": ["trend.detect", "signal.generate", "position.size"],
            "strategy": "Identify and ride strong trends while managing risk"
        }
    ]

if __name__ == "__main__":
    # Test the generation
    proposals = generate_agent_proposals(5)
    print(json.dumps(proposals, indent=2))