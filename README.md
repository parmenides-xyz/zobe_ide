# Kurtosis - Futarchy for AI agents

Futarchy for AI. Live on Sei.

## Overview

Kurtosis implements Quantum Markets, a capital-efficient design for scaling futarchy (by Paradigm). 

### Key Features

- **12 Unique AI Traders** - 
- **Real-Time Price Predictions** - Powered by Allora Network's decentralized AI inference
- **WebSocket Updates** - Live market data and trading activity
- **Glassmorphic UI** - Beautiful, modern interface with smooth animations

## Architecture

```
kurtosis-sei/
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
git clone https://github.com/yourusername/kurtosis-sei.git
cd kurtosis-sei
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
- Proposal outcomes

## Contract Setup

For the Solidity reference implementation:
```bash
cd packages/contracts
forge install https://github.com/Sofianel5/v3-periphery
forge build
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
