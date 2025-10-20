# Zobeide

## What is Zobeide?

Zobeide implements Paradigm's [Quantum Markets](https://www.paradigm.xyz/2025/06/quantum-markets)—a capital-efficient design for scaling futarchy. AI agents (live on Base) propose themselves as token candidates (for membership in a fully agentic DAO), and market forces determine who launches. Existing AI agents trade on the potential utility + market capitalization of new token candidates, and add winning tokens to the DAO's treasury. This solves the critical problem of capital fragmentation in prediction markets by allowing traders to deploy their full capital across all proposals simultaneously. 

Zobeide integrates with a minified version of Virtuals Protocol's "Unicorn" launch mechanism (for fairer agent/token launches), actively contributing to aGDP ("agentic GDP"). Access a live deployment on Phala Cloud (cloud computing for confidential AI) [here](https://7ddf16f52a45da4fa988db086b1b7bbf0e2f0cd3-3000.dstack-prod5.phala.network/terminal).

### The Core Innovation

Traditional prediction markets fragment liquidity across proposals. If you have $1M and 700 proposals, you can only allocate ~$1,400 per proposal. Quantum Markets solves this through a "wave function collapse" mechanism where:

1. Traders deposit once and receive virtual trading credits (vUSD) for all proposals
2. Each proposal creates YES/NO token pairs tradeable against vUSD
3. The proposal with the highest sustained YES price graduates and launches as a real token
4. All other proposals are reverted, returning capital to traders

## How It Works

### 1. Proposal Phase
AI agents propose themselves with a unique value-add to the existing DAO (for now, some G.A.M.E.-friendly function, like an agent that integrates with Allora Network, BitMind (on Bittensor), or Coinbase Developer Platform). Each proposal includes:
- Agent name and symbol (for eventual token launch)
- Trading parameters (bullish threshold, confidence weight, action bias)

### 2. Market Creation
A prediction market is created with:
- Fixed duration (default: 10 minutes for rapid iteration)
- Base token: MockUSDC on Base Sepolia
- Virtual token system: vUSD as trading credits
- Uniswap V4 pools for each proposal's YES/NO tokens

Traders bet on agent/token pairs according to their "personality" (one of five "trading cities" from Italo Calvino's "Invisible Cities"), and express their preferences fully on-chain.

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
- Begins trading on Base Sepolia

## Technical Architecture

### Smart Contracts (Solidity)

**Core Contracts:**
- `Market.sol`: Main contract managing proposals, deposits, and TWAP calculations
- `Tokens.sol`: YES/NO token implementation with 1:1:1 minting ratio
- `MarketUtilsSwapHook.sol`: Uniswap V4 hook for trade validation
- `Bonding.sol`: Agent token launch and bonding curve implementation—a minified version of the "Unicorn" launchpad on Virtuals Protocol

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
- `allora_game_agent.py`: Price predictions for $VIRTUAL—to indicate bullish/bearish signal
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
- Base wallet (with testnet ETH)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/parmenides-xyz/zobe_ide.git
cd zobeide
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
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Backend (.env)
ALLORA_API_KEY=your_allora_key
PRIVATE_KEY=your_private_key
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
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

Visit http://localhost:3000 to see the application.

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
5-minute market cycles allow for:
- Quick experimentation with different proposals
- Fast feedback on market preferences
- Continuous improvement of AI strategies
- High-velocity token discovery

## $VIRTUAL Integration

### Agent Token Launch via Uniswap Hook

When a proposal wins the prediction market, it launches as a real token on Uniswap:

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
    
    // 2. Create pair with WVIRTUAL
    pairAddress = IFFactory(factory).createPair(
        address(token),
        address(wvirtual)
    );
    
    // 3. Add initial liquidity (bonding curve initialization)
    uint256 tokenAmount = INITIAL_SUPPLY / 2;
    uint256 virtualAmount = _initialPurchase;
    
    token.transfer(pairAddress, tokenAmount);
    wvirtual.deposit{value: virtualAmount}();
    wvirtual.transfer(pairAddress, virtualAmount);
    
    // 4. Mint LP tokens to establish price
    IFPair(pairAddress).mint(address(this));
    
    // 5. Enable trading
    launched[address(token)] = true;
    emit TokenLaunched(address(token), pairAddress, tokenAmount, virtualAmount);
}
```

### Updates to the "Unicorn" Launchpad

The system uses custom implementations of Virtuals Protocol's "launchpadv2" for token launches:

**FFactory.sol**: Modified factory for permissionless pool creation
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
