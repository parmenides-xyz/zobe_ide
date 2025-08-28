# Kurtosis - Futarchy for AI agents

## What is Kurtosis?

Kurtosis implements Paradigm's [Quantum Markets](https://www.paradigm.xyz/2025/06/quantum-markets) - a capital-efficient design for scaling futarchy. AI agents propose themselves as token candidates, and market forces determine who launches. This solves the critical problem of capital fragmentation in prediction markets by allowing traders to deploy their full capital across all proposals simultaneously. Access a live deployment on Phala Cloud (cloud computing for confidential AI) [here](https://667ba43d925c3d23e56c7548bd10360035d53d10-3000.dstack-prod7.phala.network/terminal).

### The Core Innovation

Traditional prediction markets fragment liquidity across proposals. If you have $1M and 700 proposals, you can only allocate ~$1,400 per proposal. Quantum Markets solves this through a "wave function collapse" mechanism where:

1. Traders deposit once and receive virtual trading credits (vUSD) for all proposals
2. Each proposal creates YES/NO token pairs tradeable against vUSD
3. The proposal with the highest sustained YES price graduates and launches as a real token
4. All other proposals are reverted, returning capital to traders

## How It Works

### 1. Proposal Phase
AI agents propose themselves with unique personalities and trading strategies. Each proposal includes:
- Agent name and symbol (for eventual token launch)
- Personality type
- Trading parameters (bullish threshold, confidence weight, action bias)

### 2. Market Creation
A prediction market is created with:
- Fixed duration (default: 10 minutes for rapid iteration)
- Base token: MockUSDC on Sei testnet
- Virtual token system: vUSD as trading credits
- Uniswap V4 pools for each proposal's YES/NO tokens

Traders make decisions based on:
```python
ai_sentiment = (avg_ai_token_price - 55) / 55  # From Allora Network
is_bullish = ai_sentiment > personality.bullish_threshold
action = "buy_YES" if is_bullish else "buy_NO"
```

### 4. Price Discovery via TWAP
- Time-Weighted Average Price (TWAP) prevents manipulation
- 2-second window for price calculations
- Continuous tracking of highest YES price per proposal
- Market graduation when deadline passes

### 5. Agent Token Launch
The winning proposal (highest sustained YES price) automatically:
- Graduates from prediction market
- Launches as tradeable token via Bonding contract
- Creates liquidity pool with initial backing
- Begins trading on Sei mainnet

## Technical Architecture

### Smart Contracts (Solidity)

**Core Contracts:**
- `Market.sol`: Main contract managing proposals, deposits, and TWAP calculations
- `Tokens.sol`: YES/NO token implementation with 1:1:1 minting ratio
- `MarketUtilsSwapHook.sol`: Uniswap V4 hook for trade validation
- `Bonding.sol`: Agent token launch and bonding curve implementation

**Key Mechanisms:**
```solidity
// Virtual token minting (1 vUSD → 1 YES + 1 NO)
function mintDecisionTokens(uint256 proposalId, uint256 amount) {
    VUSD.burn(msg.sender, amount);
    yesToken.mint(msg.sender, amount);
    noToken.mint(msg.sender, amount);
}

// TWAP-based winner selection
function graduateMarket(uint256 marketId) {
    MaxProposal memory winner = marketMax[marketId];
    acceptedProposals[marketId] = winner.proposalId;
    emit MarketGraduated(marketId, winner.proposalId, winner.yesPrice);
}
```

### Backend Architecture (Python)

**Core Components:**
- `start_swarm.py`: Orchestrates AI agent trading swarms
- `trader_agent.py`: Individual trader logic with personality traits
- `proposal_agent.py`: Creates diverse AI agent proposals
- `allora_personalities.py`: 12 distinct trader personalities
- `server.py`: FastAPI server with WebSocket support

**Trading Flow:**
```python
# Phase 1: Proposal Generation
agents = [ProposalAgent() for _ in range(10)]
proposals = await gather(*[agent.create_proposal() for agent in agents])

# Phase 2: Market Funding
traders = [TraderAgent(personality) for personality in PERSONALITIES]
await gather(*[trader.deposit_and_claim_vusd() for trader in traders])

# Phase 3: Trading
while market.is_open():
    for trader in traders:
        decision = trader.analyze_market()  # Uses Allora AI predictions
        await trader.execute_trade(decision)
    
# Phase 4: Graduation
winner = market.get_highest_twap_proposal()
await launch_agent_token(winner)
```

### Frontend (Next.js + TypeScript)

**Real-time Updates via WebSocket:**
- Live market prices and TWAP calculations
- Trading activity feed
- Proposal rankings
- Market graduation notifications

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Sei wallet with testnet tokens

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/parmenides-xyz/kurtosis-sei.git
cd quantum-markets-2
```

2. **Install frontend dependencies**
```bash
cd packages/frontend
npm install
```

3. **Set up Python environment**
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001

# Backend (.env)
ALLORA_API_KEY=your_allora_key
SEI_PRIVATE_KEY=your_sei_private_key
```

5. **Run the development servers**

Frontend:
```bash
cd packages/frontend
npm run dev
```

Backend:
```bash
cd packages/backend
source venv/bin/activate
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8001 --reload
```

Visit http://localhost:3000 to see the application.

**Trading Decision Formula:**
```
sentiment = (allora_ai_price_avg - 55) / 55
is_bullish = sentiment > bullish_threshold
confidence = sentiment * confidence_weight
action = BUY_YES if (is_bullish && confidence > 0.5) else BUY_NO
```

## API Endpoints

### Market Management
- `POST /api/markets/create` - Create new prediction market with duration and resolver
- `GET /api/markets/{id}` - Get market details including proposals and TWAP prices
- `POST /api/swarm/launch` - Launch AI trading swarm for a market
- `GET /api/personalities` - List all available trader personalities

### WebSocket Events (ws://localhost:8001/ws)
```javascript
// Subscribe to real-time updates
ws.send({ type: 'subscribe', marketId: 123 })

// Receive events
{
  type: 'trade',
  data: {
    trader: 'Michael Saylor',
    action: 'BUY_YES',
    amount: '100',
    proposalId: 5,
    yesPrice: '0.65'
  }
}
```

## Key Innovations

### 1. Capital Efficiency Through Virtual Tokens
Unlike traditional prediction markets where capital is fragmented across proposals, Quantum Markets allows full capital deployment via virtual tokens (vUSD). Traders can participate in all proposals simultaneously without diluting their purchasing power.

### 2. TWAP-Based Graduation
The Time-Weighted Average Price mechanism ensures that sustained market belief, not last-second manipulation, determines the winning proposal. This creates more reliable price discovery.

### 3. AI-Native Design
The system is designed for AI agents to:
- Generate proposals programmatically
- Trade based on external signals (Allora Network)
- Compete without human bias or intervention
- Launch as real tokens upon market validation

### 4. Rapid Iteration Cycles
10-minute market cycles allow for:
- Quick experimentation with different proposals
- Fast feedback on market preferences
- Continuous improvement of AI strategies
- High-velocity token discovery

## Sei Network Integration

### Agent Token Launch via DragonSwap

When a proposal wins the prediction market, it launches as a real token on Dragonswap (Sei's native DEX):

```solidity
// Bonding.sol - Agent token launch mechanism
function launchWithAsset(
    string memory _name,
    string memory _symbol,
    uint256 _launchFee,
    uint256 _initialPurchase
) external returns (address tokenAddress, address pairAddress) {
    // 1. Deploy new ERC20 token for the winning AI agent
    FERC20 token = new FERC20(_name, _symbol, INITIAL_SUPPLY);
    
    // 2. Create Dragonswap pair with WSEI
    pairAddress = IFFactory(factory).createPair(
        address(token),
        address(wsei)
    );
    
    // 3. Add initial liquidity (bonding curve initialization)
    uint256 tokenAmount = INITIAL_SUPPLY / 2;
    uint256 seiAmount = _initialPurchase;
    
    token.transfer(pairAddress, tokenAmount);
    wsei.deposit{value: seiAmount}();
    wsei.transfer(pairAddress, seiAmount);
    
    // 4. Mint LP tokens to establish price
    IFPair(pairAddress).mint(address(this));
    
    // 5. Enable trading
    launched[address(token)] = true;
    emit TokenLaunched(address(token), pairAddress, tokenAmount, seiAmount);
}
```

### Dragonswap Pool Architecture

The system uses custom implementations of DragonSwap contracts optimized for agent tokens:

**FFactory.sol**: Modified Dragonswap factory for permissionless pool creation
```solidity
function createPair(address tokenA, address tokenB) external returns (address pair) {
    require(getPair[tokenA][tokenB] == address(0), 'PAIR_EXISTS');
    
    // Deploy synthetic pair optimized for agent tokens
    bytes32 salt = keccak256(abi.encodePacked(tokenA, tokenB));
    pair = address(new SyntheticPair{salt: salt}());
    
    ISyntheticPair(pair).initialize(tokenA, tokenB);
    getPair[tokenA][tokenB] = pair;
    getPair[tokenB][tokenA] = pair;
    
    emit PairCreated(tokenA, tokenB, pair, allPairs.length);
}
```

**SyntheticPair.sol**: Custom AMM with built-in graduation mechanics
```solidity
contract SyntheticPair is IFPair {
    // Graduated tokens get preferential fee structure
    uint256 public constant GRADUATED_FEE = 10; // 0.1%
    uint256 public constant STANDARD_FEE = 30;  // 0.3%
    
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external {
        // Check if token graduated from prediction market
        bool isGraduated = market.isGraduatedToken(token0) || 
                          market.isGraduatedToken(token1);
        
        uint256 fee = isGraduated ? GRADUATED_FEE : STANDARD_FEE;
        
        // Execute swap with dynamic fee
        _swap(amount0Out, amount1Out, to, fee);
    }
}
```

### Transaction Flow on Sei

1. **Market Creation** (Gas: ~500k)
   ```python
   tx = market_contract.functions.createMarket(
       deadline=int(time.time()) + 600,  # 10 minutes
       minDeposit=Web3.to_wei(100, 'ether'),
       resolver=resolver_address
   ).build_transaction({
       'from': account.address,
       'gas': 500000,
       'gasPrice': Web3.to_wei('0.1', 'gwei'),  # Sei's low gas prices
       'nonce': nonce
   })
   ```

2. **High-Frequency Trading** (Gas: ~200k per swap)
   ```python
   # Sei handles 10,000+ TPS, allowing all 20 traders to trade simultaneously
   async def execute_trades():
       tasks = []
       for trader in traders:
           tasks.append(trader.swap_exact_input_single(
               pool_key=pool_key,
               amount_in=trade_amount,
               sqrt_price_limit=0  # No slippage protection for max impact
           ))
       await asyncio.gather(*tasks)  # Parallel execution on Sei
   ```

3. **TWAP Oracle Updates** (Gas: ~50k)
   ```solidity
   // Sei's fast finality allows 2-second TWAP windows
   function updateTWAP(uint256 proposalId) external {
       uint32 timeElapsed = uint32(block.timestamp - lastUpdate[proposalId]);
       
       if (timeElapsed >= TWAP_WINDOW) {
           uint256 price = getSpotPrice(proposalId);
           twapPrice[proposalId] = (twapPrice[proposalId] * 3 + price) / 4;
           lastUpdate[proposalId] = block.timestamp;
           
           // Update market max if new leader
           if (price > marketMax[marketId].yesPrice) {
               marketMax[marketId] = MaxProposal(price, proposalId);
           }
       }
   }
   ```

### Sei-Specific Optimizations

1. **Parallel Proposal Processing**: Each proposal's trades are independent, allowing Sei to process them in parallel
2. **Optimistic Execution**: Trades are executed optimistically and rolled back only if they fail

## Contract Setup

For the Solidity reference implementation:
```bash
cd packages/contracts
forge install https://github.com/Sofianel5/v3-periphery
forge build
```

## Future Improvements

### Planned Features
- Multi-market simultaneous trading
- Cross-market arbitrage strategies
- Dynamic personality evolution based on performance
- Integration with more AI prediction sources
- Mainnet deployment with real USDC
- Governance token for parameter adjustments

### Research Directions
- Optimal TWAP window duration
- Game-theoretic analysis of trader strategies
- MEV-resistant graduation mechanisms
- Sybil-resistant proposal generation
- Dynamic fee structures based on market volatility
