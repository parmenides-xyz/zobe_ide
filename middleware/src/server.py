#!/usr/bin/env python3
"""
Backend API
Middleware for interacting with Zobeide
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend directory to path for imports
backend_path = str(Path(__file__).parent.parent.parent / "backend")
sys.path.append(backend_path)

# Import local modules with correct paths
from src.trading_agent.trader_agent import TraderAgent
from src.proposal_agent.proposal_agent import ProposalAgent
from src.allora_game_agent.allora_game_agent import get_trader_personality
from src.cities.invisible_cities import INVISIBLE_CITIES
from src.launchpad_agent.launchpad_agent import AgentTokenLauncher

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Zobeide API",
    description="API for managing agentic futarchy on Virtuals Protocol",
    version="1.0.0"
)

# Configure CORS - use environment variable for production
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
class AppState:
    def __init__(self):
        self.active_markets = {}
        self.active_traders = {}
        self.active_proposals = {}
        self.websocket_connections = []
        self.trading_tasks = {}
        self.swarm_processes = {}

state = AppState()

# WebSocket manager for broadcasting
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections.remove(conn)

ws_manager = WebSocketManager()

# Pydantic models for request/response
class CreateMarketRequest(BaseModel):
    title: str = "AI Agent Launch Market"
    min_deposit: float = 1000.0
    duration_minutes: int = 2
    resolver_address: Optional[str] = None

class CreateMarketResponse(BaseModel):
    market_id: int
    transaction_hash: str
    deadline: int
    title: str
    status: str

class LaunchSwarmRequest(BaseModel):
    market_id: Optional[int] = None
    num_traders: int = 20
    num_proposal_agents: int = 10

class SwarmStatus(BaseModel):
    market_id: int
    active_traders: int
    active_proposals: List[int]
    total_trades: int
    is_running: bool
    process_id: Optional[str] = None
    leading_proposal: Optional[int] = None
    leading_price: Optional[float] = None

class ProposalRequest(BaseModel):
    market_id: int
    agent_name: str
    symbol: str
    description: str
    capabilities: List[str]
    strategy: str

class TraderInfo(BaseModel):
    address: str
    balance: float
    personality: Optional[Dict[str, Any]]
    trades_executed: int

class MarketInfo(BaseModel):
    market_id: int
    title: str
    deadline: int
    is_graduated: bool
    winning_proposal: Optional[int]
    total_volume: Optional[float]

class MarketStats(BaseModel):
    market_id: int
    title: str
    deadline: int
    is_graduated: bool
    winning_proposal: Optional[int]
    total_volume: Optional[float]
    traders_count: int
    proposals_count: int
    status: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    active_markets: int
    active_connections: int

# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check and status endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        active_markets=len(state.active_markets),
        active_connections=len(ws_manager.active_connections)
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        active_markets=len(state.active_markets),
        active_connections=len(ws_manager.active_connections)
    )

@app.post("/api/markets/create", response_model=CreateMarketResponse)
async def create_market(request: CreateMarketRequest, background_tasks: BackgroundTasks):
    """Create a new prediction market for AI agent proposals"""
    try:
        async def create_market_task():
            try:
                # Broadcast start
                await ws_manager.broadcast({
                    "type": "market_creation",
                    "status": "started",
                    "message": f"Creating market: {request.title}"
                })

                # Initialize web3 and account
                w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL", "https://sepolia.base.org")))
                account = Account.from_key(os.getenv("PRIVATE_KEY"))

                # Market creation logic
                market_address = os.getenv("MARKET_ADDRESS")
                mock_usdc_address = os.getenv("MOCK_USDC_ADDRESS", "0xaF26B96096D3a989D2f31ffbdd686Fa23cbE9b42")

                # Calculate deadline
                deadline = int((datetime.now() + timedelta(minutes=request.duration_minutes)).timestamp())

                # Create market contract instance
                create_market_abi = [{
                    "inputs": [
                        {"name": "creator", "type": "address"},
                        {"name": "marketToken", "type": "address"},
                        {"name": "resolver", "type": "address"},
                        {"name": "minDeposit", "type": "uint256"},
                        {"name": "deadline", "type": "uint256"},
                        {"name": "title", "type": "string"}
                    ],
                    "name": "createMarket",
                    "outputs": [{"name": "marketId", "type": "uint256"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]

                market_contract = w3.eth.contract(address=market_address, abi=create_market_abi)

                # Build and send transaction
                resolver = request.resolver_address or account.address
                min_deposit = int(request.min_deposit * 10**18)

                await ws_manager.broadcast({
                    "type": "market_creation",
                    "status": "signing",
                    "message": "Signing transaction..."
                })

                tx = market_contract.functions.createMarket(
                    account.address,
                    mock_usdc_address,
                    resolver,
                    min_deposit,
                    deadline,
                    request.title
                ).build_transaction({
                    'from': account.address,
                    'gas': 500000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': w3.eth.get_transaction_count(account.address),
                })

                signed_tx = account.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

                await ws_manager.broadcast({
                    "type": "market_creation",
                    "status": "pending",
                    "message": f"Transaction sent: {tx_hash.hex()}",
                    "tx_hash": tx_hash.hex()
                })

                # Wait for receipt
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt['status'] != 1:
                    raise Exception("Market creation transaction failed")

                # Extract market ID from logs
                if receipt['logs']:
                    # First topic is the event signature, second is the indexed marketId
                    market_id = int(receipt['logs'][0]['topics'][1].hex(), 16)
                else:
                    raise Exception("No market ID in transaction logs")

                # Store market info
                state.active_markets[market_id] = {
                    "title": request.title,
                    "deadline": deadline,
                    "created_at": datetime.now().isoformat(),
                    "is_graduated": False,
                    "tx_hash": tx_hash.hex()
                }

                # Save to file for orchestrator compatibility
                market_file = Path(__file__).parent.parent.parent / "backend" / "src" / "core" / "latest_market.txt"
                market_file.parent.mkdir(exist_ok=True)
                with open(market_file, "w") as f:
                    f.write(str(market_id))

                await ws_manager.broadcast({
                    "type": "market_creation",
                    "status": "completed",
                    "market_id": market_id,
                    "message": f"Market #{market_id} created successfully!",
                    "tx_hash": tx_hash.hex()
                })

                logger.info(f"Market {market_id} created successfully")

            except Exception as e:
                logger.error(f"Market creation error: {e}")
                await ws_manager.broadcast({
                    "type": "market_creation",
                    "status": "error",
                    "message": str(e)
                })

        background_tasks.add_task(create_market_task)

        return CreateMarketResponse(
            market_id=0,  # Will be updated via WebSocket
            transaction_hash="pending",
            deadline=0,
            title=request.title,
            status="creating"
        )

    except Exception as e:
        logger.error(f"Market creation request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets/{market_id}", response_model=MarketInfo)
async def get_market(market_id: int):
    """Get information about a specific market"""
    if market_id not in state.active_markets:
        raise HTTPException(status_code=404, detail="Market not found")

    market = state.active_markets[market_id]

    # Check if market is graduated
    try:
        launcher = AgentTokenLauncher()
        winning_proposal = launcher.get_winning_proposal(market_id)
        is_graduated = winning_proposal is not None
        winning_id = winning_proposal['id'] if winning_proposal else None
    except:
        is_graduated = False
        winning_id = None

    return MarketInfo(
        market_id=market_id,
        title=market["title"],
        deadline=market["deadline"],
        is_graduated=is_graduated,
        winning_proposal=winning_id,
        total_volume=market.get("total_volume")
    )

@app.get("/api/markets/stats/{market_id}", response_model=MarketStats)
async def get_market_stats(market_id: int):
    """Get comprehensive stats for a specific market including traders and proposals"""
    # Get trader and proposal counts from state
    traders_count = len([t for t_id, t in state.active_traders.items() if t.get("market_id") == market_id])
    proposals_count = len([p_id for p_id, p in state.active_proposals.items() if p["market_id"] == market_id])
    
    # Check if swarm is running
    is_running = market_id in state.swarm_processes
    status = "ACTIVE" if is_running else "IDLE"
    
    # Check if market exists in active_markets
    if market_id in state.active_markets:
        market = state.active_markets[market_id]
        title = market.get("title", "AI Agent Launch Market")
        deadline = market.get("deadline", int((datetime.now() + timedelta(minutes=10)).timestamp()))
    else:
        title = "AI Agent Launch Market"
        deadline = int((datetime.now() + timedelta(minutes=10)).timestamp())
    
    # Check if market is graduated
    try:
        launcher = AgentTokenLauncher()
        winning_proposal = launcher.get_winning_proposal(market_id)
        is_graduated = winning_proposal is not None
        winning_id = winning_proposal['id'] if winning_proposal else None
    except:
        is_graduated = False
        winning_id = None
    
    return MarketStats(
        market_id=market_id,
        title=title,
        deadline=deadline,
        is_graduated=is_graduated,
        winning_proposal=winning_id,
        total_volume=0,  # Would need to calculate from trades
        traders_count=traders_count,
        proposals_count=proposals_count,
        status=status
    )

@app.get("/api/markets", response_model=List[MarketInfo])
async def list_markets():
    """List all active markets - only return the real one from latest_market.txt"""
    markets = []
    
    # Read the latest market ID from file (the REAL one)
    market_file = Path(__file__).parent.parent.parent / "backend" / "src" / "core" / "latest_market.txt"
    if market_file.exists():
        with open(market_file, "r") as f:
            try:
                market_id = int(f.read().strip())
                
                # Get trader and proposal counts from state
                traders_count = len([t for t_id, t in state.active_traders.items() if t.get("market_id") == market_id])
                proposals_count = len([p_id for p_id, p in state.active_proposals.items() if p["market_id"] == market_id])
                
                # For now, just return this one real market
                # In production, you'd query the blockchain for all markets
                market_info = {
                    "market_id": market_id,
                    "title": "AI Agent Launch Market",
                    "deadline": int((datetime.now() + timedelta(minutes=10)).timestamp()),
                    "is_graduated": False,
                    "winning_proposal": None,
                    "total_volume": None,
                    "traders_count": traders_count,
                    "proposals_count": proposals_count
                }
                
                # Also include these in a MarketInfo compatible format
                markets.append(MarketInfo(
                    market_id=market_id,
                    title="AI Agent Launch Market",
                    deadline=int((datetime.now() + timedelta(minutes=10)).timestamp()),
                    is_graduated=False,
                    winning_proposal=None,
                    total_volume=None
                ))
            except Exception as e:
                logger.warning(f"Could not read market file: {e}")
    
    return markets

@app.post("/api/swarm/launch")
async def launch_swarm(request: LaunchSwarmRequest, background_tasks: BackgroundTasks):
    """Launch a swarm of trading agents for a market"""
    try:
        # Get market ID
        if request.market_id is None:
            market_file = Path(__file__).parent.parent.parent / "backend" / "src" / "core" / "latest_market.txt"
            if market_file.exists():
                with open(market_file, 'r') as f:
                    market_id = int(f.read().strip())
            else:
                raise HTTPException(status_code=400, detail="No market ID provided and no latest market found")
        else:
            market_id = request.market_id

        if market_id in state.swarm_processes:
            raise HTTPException(status_code=400, detail="Swarm already running for this market")

        async def run_swarm_with_updates():
            try:
                # Broadcast start
                await ws_manager.broadcast({
                    "type": "swarm_launch",
                    "status": "started",
                    "market_id": market_id,
                    "message": f"Launching swarm with {request.num_traders} traders and {request.num_proposal_agents} proposals"
                })

                # Set environment variables for the subprocess
                env = os.environ.copy()
                env["NUM_TRADERS"] = str(request.num_traders)
                env["NUM_PROPOSAL_AGENTS"] = str(request.num_proposal_agents)

                # Path to start_swarm.py
                swarm_script = Path(__file__).parent.parent.parent / "backend" / "src" / "core" / "start_swarm.py"

                # Run as subprocess to capture output - UNBUFFERED FOR REAL-TIME STREAMING
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-u", str(swarm_script),  # -u flag forces unbuffered stdout
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=env
                )

                state.swarm_processes[market_id] = process

                # Stream output to WebSocket
                async for line in process.stdout:
                    message = line.decode().strip()
                    if message:
                        await ws_manager.broadcast({
                            "type": "swarm_log",
                            "market_id": market_id,
                            "message": message,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Parse special messages and update state
                        if "Created trader" in message:
                            # Extract trader address from log: "Created trader 0x1234... → Name (Type)"
                            if "..." in message:
                                addr_start = message.find("0x")
                                if addr_start != -1:
                                    addr_end = message.find("...", addr_start)
                                    if addr_end != -1:
                                        trader_addr = message[addr_start:addr_end]
                                        # Extract personality info
                                        arrow_idx = message.find("→")
                                        if arrow_idx != -1:
                                            personality_info = message[arrow_idx+1:].strip()
                                        else:
                                            personality_info = "Unknown"
                                        
                                        # Add to active traders
                                        trader_id = f"{market_id}_{trader_addr}"
                                        state.active_traders[trader_id] = {
                                            "market_id": market_id,
                                            "address": trader_addr,
                                            "personality": personality_info,
                                            "balance": 0,
                                            "trades": 0,
                                            "created_at": datetime.now().isoformat()
                                        }
                                        logger.info(f"Added trader {trader_addr} to market {market_id}")
                        
                        elif "created proposal ID" in message:
                            # Extract proposal ID from log: "ProposalAgent X created proposal ID Y"
                            try:
                                parts = message.split("proposal ID")
                                if len(parts) > 1:
                                    proposal_id = int(parts[1].strip())
                                    # Add to active proposals
                                    state.active_proposals[proposal_id] = {
                                        "market_id": market_id,
                                        "id": proposal_id,
                                        "created_at": datetime.now().isoformat()
                                    }
                                    logger.info(f"Added proposal {proposal_id} to market {market_id}")
                                    
                                    await ws_manager.broadcast({
                                        "type": "proposal_created",
                                        "market_id": market_id,
                                        "proposal_id": proposal_id,
                                        "message": message
                                    })
                            except (ValueError, IndexError) as e:
                                logger.warning(f"Could not parse proposal ID from: {message}")
                        
                        elif "Trade executed" in message or "trade completed" in message.lower():
                            # Update trade count for traders
                            for trader_id, trader_data in state.active_traders.items():
                                if trader_data.get("market_id") == market_id:
                                    trader_data["trades"] = trader_data.get("trades", 0) + 1
                                    break  # Just increment for one trader for now
                            
                            await ws_manager.broadcast({
                                "type": "trade_executed",
                                "market_id": market_id,
                                "message": message
                            })
                        
                        elif "MarketMax" in message or "TWAP" in message:
                            # Parse MarketMax/TWAP updates: "MarketMax updated: Proposal X with price Y"
                            if "Proposal" in message and "price" in message:
                                try:
                                    # Extract proposal ID
                                    prop_start = message.find("Proposal") + 9
                                    prop_end = message.find(" ", prop_start)
                                    if prop_end == -1:
                                        prop_end = message.find("with", prop_start)
                                    proposal_id = int(message[prop_start:prop_end].strip())
                                    
                                    # Extract price
                                    price_start = message.find("price") + 6
                                    price_str = message[price_start:].strip()
                                    # Remove any trailing text
                                    price_parts = price_str.split()[0]
                                    price = float(price_parts)
                                    
                                    # Update market state
                                    if market_id in state.active_markets:
                                        state.active_markets[market_id]["leading_proposal"] = proposal_id
                                        state.active_markets[market_id]["leading_price"] = price
                                    else:
                                        state.active_markets[market_id] = {
                                            "leading_proposal": proposal_id,
                                            "leading_price": price
                                        }
                                    
                                    logger.info(f"MarketMax updated: Proposal {proposal_id} at price {price}")
                                    
                                    await ws_manager.broadcast({
                                        "type": "marketmax_update",
                                        "market_id": market_id,
                                        "proposal_id": proposal_id,
                                        "price": price,
                                        "message": message
                                    })
                                except (ValueError, IndexError) as e:
                                    logger.warning(f"Could not parse MarketMax from: {message}")

                # Wait for process to complete
                await process.wait()

                if process.returncode == 0:
                    await ws_manager.broadcast({
                        "type": "swarm_launch",
                        "status": "completed",
                        "market_id": market_id,
                        "message": "Swarm execution completed successfully!"
                    })
                else:
                    await ws_manager.broadcast({
                        "type": "swarm_launch",
                        "status": "error",
                        "market_id": market_id,
                        "message": f"Swarm process exited with code {process.returncode}"
                    })

            except Exception as e:
                logger.error(f"Swarm execution error: {e}")
                await ws_manager.broadcast({
                    "type": "swarm_launch",
                    "status": "error",
                    "market_id": market_id,
                    "message": str(e)
                })
            finally:
                if market_id in state.swarm_processes:
                    del state.swarm_processes[market_id]

        background_tasks.add_task(run_swarm_with_updates)

        return {
            "status": "launched",
            "market_id": market_id,
            "num_traders": request.num_traders,
            "num_proposal_agents": request.num_proposal_agents
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Swarm launch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/swarm/status/{market_id}", response_model=SwarmStatus)
async def get_swarm_status(market_id: int):
    """Get status of trading swarm for a market"""
    is_running = market_id in state.swarm_processes
    process_id = str(state.swarm_processes[market_id].pid) if is_running else None

    # Get trader count
    traders = [t for t_id, t in state.active_traders.items() if t.get("market_id") == market_id]

    # Get proposals
    proposals = [p_id for p_id, p in state.active_proposals.items() if p["market_id"] == market_id]

    # Try to get leading proposal from state
    leading_proposal = None
    leading_price = None
    if market_id in state.active_markets:
        market = state.active_markets[market_id]
        leading_proposal = market.get("leading_proposal")
        leading_price = market.get("leading_price")

    return SwarmStatus(
        market_id=market_id,
        active_traders=len(traders),
        active_proposals=proposals,
        total_trades=sum(t.get("trades", 0) for t in traders),
        is_running=is_running,
        process_id=process_id,
        leading_proposal=leading_proposal,
        leading_price=leading_price
    )

@app.post("/api/swarm/stop/{market_id}")
async def stop_swarm(market_id: int):
    """Stop the trading swarm for a market"""
    if market_id not in state.swarm_processes:
        raise HTTPException(status_code=404, detail="No swarm running for this market")

    try:
        process = state.swarm_processes[market_id]
        process.terminate()
        await asyncio.sleep(1)
        if process.returncode is None:
            process.kill()
        
        del state.swarm_processes[market_id]
        
        await ws_manager.broadcast({
            "type": "swarm_stopped",
            "market_id": market_id,
            "message": "Swarm stopped"
        })
        
        return {"status": "stopped", "market_id": market_id}
    except Exception as e:
        logger.error(f"Error stopping swarm: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/traders/{market_id}", response_model=List[TraderInfo])
async def get_traders(market_id: int):
    """Get list of active traders for a market"""
    traders = []
    for trader_id, trader_data in state.active_traders.items():
        if trader_data.get("market_id") == market_id:
            traders.append(TraderInfo(
                address=trader_data["address"],
                balance=trader_data.get("balance", 0),
                personality=trader_data.get("personality"),
                trades_executed=trader_data.get("trades", 0)
            ))
    return traders

@app.get("/api/personalities")
async def get_personalities():
    """Get available trader personalities with additional metadata for frontend"""
    # Transform personalities to include more useful fields for frontend
    personalities_with_metadata = []
    for p in INVISIBLE_CITIES:
        # Extract key info for frontend display
        personality = {
            "name": p["name"],
            "theme": p["theme"],
            "description": p["description"],
            "action_bias": p["action_bias"],
            "risk_profile": p["risk_profile"],
            "risk_tolerance": int((1 - p["bullish_threshold"]) * 100),  # Convert to 0-100 scale
            "trading_philosophy": p["trading_philosophy"],
            "typical_behavior": p["typical_behavior"]
        }
        personalities_with_metadata.append(personality)

    return personalities_with_metadata

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time market updates"""
    await ws_manager.connect(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to Zobeide WebSocket",
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle subscription requests
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    market_id = message.get("market_id")
                    # Send initial market data
                    if market_id in state.active_markets:
                        await websocket.send_text(json.dumps({
                            "type": "market_data",
                            "data": state.active_markets[market_id],
                            "timestamp": datetime.now().isoformat()
                        }))
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# Background task to broadcast updates
async def broadcast_updates():
    """Broadcast market and swarm updates to all WebSocket clients"""
    while True:
        try:
            # Read the latest market from file
            market_file = Path(__file__).parent.parent.parent / "backend" / "src" / "core" / "latest_market.txt"
            if market_file.exists() and ws_manager.active_connections:
                with open(market_file, "r") as f:
                    market_id = int(f.read().strip())
                    
                    # Broadcast market status
                    market_update = {
                        "type": "market_update",
                        "market_id": market_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Check if swarm is running
                    if market_id in state.swarm_processes:
                        market_update["swarm_status"] = {
                            "is_running": True,
                            "process_id": str(state.swarm_processes[market_id].pid) if state.swarm_processes[market_id] else None
                        }
                    else:
                        market_update["swarm_status"] = {
                            "is_running": False
                        }
                    
                    await ws_manager.broadcast(market_update)
                    
        except Exception as e:
            logger.error(f"Error in broadcast_updates: {e}")
        
        # Broadcast every 2 seconds
        await asyncio.sleep(2)

# Global background task
broadcast_task = None

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application state on startup"""
    global broadcast_task
    logger.info("Zobeide API starting up...")
    
    # Start the broadcast task
    broadcast_task = asyncio.create_task(broadcast_updates())
    
    # Load any existing market data
    market_file = Path(__file__).parent.parent.parent / "backend" / "src" / "core" / "latest_market.txt"
    if market_file.exists():
        with open(market_file, "r") as f:
            try:
                market_id = int(f.read().strip())
                # Could load market details from blockchain here
                state.active_markets[market_id] = {
                    "title": "Recovered Market",
                    "deadline": 0,
                    "is_graduated": False,
                    "recovered": True
                }
                logger.info(f"Recovered market ID: {market_id}")
            except Exception as e:
                logger.warning(f"Could not recover market: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global broadcast_task
    logger.info("Zobeide API shutting down...")
    
    # Cancel broadcast task
    if broadcast_task:
        broadcast_task.cancel()
    
    # Terminate all running swarm processes
    for market_id, process in state.swarm_processes.items():
        try:
            process.terminate()
            await asyncio.sleep(0.5)
            if process.returncode is None:
                process.kill()
        except:
            pass
    
    # Close WebSocket connections
    for connection in ws_manager.active_connections:
        try:
            await connection.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable for deployment
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,  # Disabled to avoid multiprocessing import issues with cosmpy/protobuf
        log_level="info"
    )