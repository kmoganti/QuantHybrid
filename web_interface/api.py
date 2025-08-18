"""
FastAPI-based web interface for QuantHybrid trading system.
"""
from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, List, Optional
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio

from config.settings import WEB_INTERFACE_SETTINGS
from utils.trading_state import TradingState
from database.database_manager import DatabaseManager

app = FastAPI(title="QuantHybrid Trading System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
trading_state = TradingState()
db_manager = DatabaseManager()

# Models
class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class SystemStatus(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_strategies: int
    total_positions: int
    daily_pnl: float
    risk_level: str

class StrategyConfig(BaseModel):
    name: str
    type: str
    parameters: Dict
    is_active: bool

# Authentication functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=WEB_INTERFACE_SETTINGS['access_token_expire_minutes'])
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, WEB_INTERFACE_SETTINGS['secret_key'], algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, WEB_INTERFACE_SETTINGS['secret_key'], algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = User(username=username)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Routes
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate credentials (implement proper validation)
    if form_data.username != WEB_INTERFACE_SETTINGS['admin_username'] or \
       form_data.password != WEB_INTERFACE_SETTINGS['admin_password']:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/system/status", response_model=SystemStatus)
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Get current system status."""
    try:
        metrics = await db_manager.get_latest_system_metrics()
        return SystemStatus(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies")
async def get_strategies(current_user: User = Depends(get_current_user)):
    """Get all configured strategies."""
    try:
        strategies = await db_manager.get_all_strategies()
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies")
async def create_strategy(
    strategy: StrategyConfig,
    current_user: User = Depends(get_current_user)
):
    """Create a new strategy."""
    try:
        strategy_id = await db_manager.create_strategy(strategy.dict())
        return {"id": strategy_id, "message": "Strategy created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    strategy: StrategyConfig,
    current_user: User = Depends(get_current_user)
):
    """Update an existing strategy."""
    try:
        await db_manager.update_strategy(strategy_id, strategy.dict())
        return {"message": "Strategy updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions(current_user: User = Depends(get_current_user)):
    """Get all open positions."""
    try:
        positions = await db_manager.get_open_positions()
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get recent orders."""
    try:
        orders = await db_manager.get_orders(status=status, limit=limit)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance(
    strategy_id: Optional[int] = None,
    timeframe: str = "1d",
    current_user: User = Depends(get_current_user)
):
    """Get strategy performance metrics."""
    try:
        performance = await db_manager.get_performance_metrics(
            strategy_id=strategy_id,
            timeframe=timeframe
        )
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/enable")
async def enable_trading(current_user: User = Depends(get_current_user)):
    """Enable trading system-wide."""
    try:
        trading_state.enable_trading()
        return {"message": "Trading enabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/disable")
async def disable_trading(current_user: User = Depends(get_current_user)):
    """Disable trading system-wide."""
    try:
        trading_state.disable_trading()
        return {"message": "Trading disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data."""
    await websocket.accept()
    try:
        while True:
            market_data = await db_manager.get_latest_market_data()
            await websocket.send_json(market_data)
            await asyncio.sleep(1)
    except Exception as e:
        await websocket.close()

@app.websocket("/ws/system-metrics")
async def websocket_system_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time system metrics."""
    await websocket.accept()
    try:
        while True:
            metrics = await db_manager.get_latest_system_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(5)
    except Exception as e:
        await websocket.close()

# Mount static files for web interface
app.mount("/", StaticFiles(directory="web_interface/static", html=True), name="static")
