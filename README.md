# Zobeide

Reference implementation of [Quantum Markets](https://www.paradigm.xyz/2025/06/quantum-markets)—a capital-efficient prediction market design for scaling futarchy. AI agents propose themselves as token candidates, and market forces determine who launches.

## Overview

Quantum Markets solves capital fragmentation in prediction markets.

1. Traders deposit once and receive virtual trading credits (vUSD) for all proposals
2. Each proposal creates YES/NO token pairs tradeable against vUSD
3. The proposal with the highest sustained YES price graduates and launches as a real token
4. All other proposals revert, returning capital to traders

## Architecture

**Smart Contracts (Solidity):**
- `Market.sol` - Proposal management, deposits, TWAP calculations
- `Tokens.sol` - YES/NO token implementation
- `MarketUtilsSwapHook.sol` - Uniswap V4 hook for trade validation
- `Bonding.sol` - Agent token launch via bonding curve (based on Virtuals Protocol)

**Backend (Python):**
- `start_swarm.py` - AI agent trading orchestration
- `trader_agent.py` - Individual trader logic
- `proposal_agent.py` - Proposal generation
- `server.py` - FastAPI server with WebSocket support

**Frontend:** Next.js + TypeScript with real-time WebSocket updates
