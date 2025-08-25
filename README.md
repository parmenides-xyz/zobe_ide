# Kurtosis - AI-Powered Futarchy Markets

<div align="center">
  <img src="packages/frontend/public/bg-fire.png" alt="Kurtosis Logo" width="120" />
  
  **Futarchy for AI agents. Live on Sei.**
  
  [![Built on Sei](https://img.shields.io/badge/Built%20on-Sei-00D4AA?style=for-the-badge)](https://sei.io)
  [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
</div>

## Overview

Kurtosis implements Quantum Markets, a capital-efficient design for scaling futarchy (by Paradigm). 

### Key Features

- **12 Unique AI Traders** - 
- **Real-Time Price Predictions** - Powered by Allora Network's decentralized AI inference
- **WebSocket Updates** - Live market data and trading activity
- **Glassmorphic UI** - Beautiful, modern interface with smooth animations

## Architecture

```
quantum-markets-2/
├── packages/
│   ├── frontend/          # Next.js 14 app with TypeScript
│   ├── backend/           # Python FastAPI server with AI agents
│   └── contracts/         # Solidity smart contracts (Sei EVM)
└── docker-compose.yml     # Container orchestration
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Sei wallet with testnet tokens

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/quantum-markets-2.git
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

## API Endpoints

### REST API (http://localhost:8001)

- `GET /api/markets` - Get all active prediction markets
- `GET /api/markets/{id}` - Get specific market details
- `POST /api/markets` - Create new prediction market
- `GET /api/personalities` - Get all AI trader personalities
- `GET /api/swarm/status` - Get trading swarm status

### WebSocket (ws://localhost:8001/ws)

Real-time updates for:
- Market price changes
- New trades
- AI agent decisions
- Proposal outcomes

## UI Features

### Glassmorphic Design System
- Backdrop blur effects
- Gradient overlays
- Animated cards with hover effects
- Neon text accents
- Floating animations

## Technology Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development

### Backend
- **FastAPI** - High-performance Python web framework
- **Asyncio** - Asynchronous trading operations
- **Allora SDK** - AI price predictions
- **Sei SDK** - Blockchain interactions
- **WebSockets** - Real-time communication

### Smart Contracts
- **Solidity** - EVM-compatible contracts
- **Foundry** - Development framework
- **OpenZeppelin** - Security standards

## Sei Integration

The platform leverages Sei's unique features:
- Sub-second finality
- EVM compatibility
- Native order matching
- Built-in price oracles

## Contract Setup

For the Solidity reference implementation:
```bash
cd packages/contracts
forge install https://github.com/Sofianel5/v3-periphery
forge build
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
