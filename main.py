"""
Main application entry point for QuantHybrid trading system.
"""
import asyncio
from fastapi import FastAPI
from config.logging_config import get_logger
from utils.trading_state import TradingState
from database.database_manager import init_db

# Initialize FastAPI app
app = FastAPI(title="QuantHybrid Trading System")

# Get logger
logger = get_logger('system')

# Initialize global trading state
trading_state = TradingState()

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    try:
        logger.info("Initializing QuantHybrid Trading System...")
        
        # Initialize database
        await init_db()
        
        # Initialize other components
        # TODO: Add initialization of other components
        
        logger.info("System initialization completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "active", "trading_enabled": trading_state.is_trading_enabled()}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# TODO: Add more endpoints for trading control, monitoring, etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
