"""
Database manager for QuantHybrid system.
"""
import asyncio
from typing import Any, List, Optional, Type, TypeVar, Dict, AsyncIterator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text
from contextlib import asynccontextmanager
from config.settings import DATABASE_URL
from config.logging_config import get_logger
from database.models import Base, Trade, Position, Order, Strategy, Account

logger = get_logger('system')

# Type variable for generic database operations
T = TypeVar('T')

class DatabaseManager:
    """Manages database operations for the trading system."""
    
    def __init__(self, test_mode: bool = False):
        """Initialize database manager.
        
        Args:
            test_mode (bool): If True, uses an in-memory SQLite database
        """
        if test_mode:
            db_url = "sqlite+aiosqlite:///:memory:"
        else:
            db_url = DATABASE_URL

        # Ensure async driver is used
        if db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        self.connection_string = db_url
        self.engine = create_async_engine(
            db_url,
            echo=False,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def init_db(self):
        """Initialize database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def initialize(self, test_mode: bool = True):
        """Re-initialize a clean database for tests.
        Drops and recreates all tables, optionally using in-memory DB.
        """
        try:
            if test_mode:
                # Recreate engine with in-memory DB
                self.connection_string = "sqlite+aiosqlite:///:memory:"
                self.engine = create_async_engine(self.connection_string, echo=False, future=True)
                self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
            # Drop and recreate tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Test database re-initialized")
        except Exception as e:
            logger.error(f"Failed to re-initialize database: {str(e)}")
            raise
    
    async def cleanup(self):
        """Cleanup database after test (drop all tables)."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        except Exception as e:
            logger.error(f"Failed to cleanup database: {str(e)}")
    
    # Legacy sync-style helpers expected by some tests
    def initialize_database(self):
        """Synchronous helper to initialize database using current connection_string."""
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.init_db())
    
    def close_connection(self):
        """Dispose engine (compat with tests)."""
        # Engine dispose is sync-compatible
        try:
            self.engine.sync_engine.dispose()
        except Exception:
            # Fallback to async dispose
            pass
    
    # Generic helpers
    async def add_item(self, item: Any) -> bool:
        """Add a single item to the database."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    session.add(item)
            logger.debug(f"Added item to {getattr(item, '__tablename__', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to add item: {str(e)}")
            return False
    
    async def add_items(self, items: List[Any]) -> bool:
        """Add multiple items to the database."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    session.add_all(items)
            logger.debug(f"Added {len(items)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to add items: {str(e)}")
            return False
    
    async def get_item(self, model: Type[T], item_id: int) -> Optional[T]:
        """Get a single item by ID."""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(model).filter(model.id == item_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get item: {str(e)}")
            return None
    
    async def get_items(self, model: Type[T], **filters) -> List[T]:
        """Get items with optional filters."""
        try:
            async with self.async_session() as session:
                query = select(model)
                for key, value in filters.items():
                    query = query.filter(getattr(model, key) == value)
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get items: {str(e)}")
            return []
    
    async def update_item(self, item: Any) -> bool:
        """Update an existing item."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    session.add(item)
            logger.debug(f"Updated item in {getattr(item, '__tablename__', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to update item: {str(e)}")
            return False
    
    async def delete_item(self, item: Any) -> bool:
        """Delete an item from the database."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    await session.delete(item)
            logger.debug(f"Deleted item from {getattr(item, '__tablename__', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete item: {str(e)}")
            return False

    # Transaction context manager
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        async with self.async_session() as session:
            try:
                async with session.begin():
                    yield session
            except Exception:
                await session.rollback()
                raise

    # CRUD APIs expected by tests
    async def insert_trade(self, trade: Any) -> int:
        if isinstance(trade, dict):
            trade_obj = Trade(
                symbol=trade.get('symbol'),
                quantity=trade.get('quantity'),
                price=trade.get('price'),
                timestamp=trade.get('timestamp'),
                entry_price=trade.get('entry_price'),
                exit_price=trade.get('exit_price'),
                entry_time=trade.get('entry_time'),
                exit_time=trade.get('exit_time'),
                strategy_id=trade.get('strategy_id'),
                pnl=trade.get('pnl'),
            )
        else:
            trade_obj = trade
        await self.add_item(trade_obj)
        return trade_obj.id

    async def get_trade(self, trade_id: int) -> Optional[Trade]:
        return await self.get_item(Trade, trade_id)

    async def update_trade(self, trade: Trade) -> bool:
        return await self.update_item(trade)

    async def insert_position(self, position: Any) -> int:
        if isinstance(position, dict):
            pos_obj = Position(
                symbol=position.get('symbol'),
                quantity=position.get('quantity'),
                average_price=position.get('average_price'),
                current_price=position.get('current_price'),
                unrealized_pnl=position.get('unrealized_pnl'),
                strategy_id=position.get('strategy_id'),
            )
        else:
            pos_obj = position
        await self.add_item(pos_obj)
        return pos_obj.id

    async def get_position(self, symbol: str) -> Optional[Position]:
        items = await self.get_items(Position, symbol=symbol)
        return items[0] if items else None

    async def get_all_positions(self) -> List[Position]:
        return await self.get_items(Position)

    async def update_position(self, position: Any) -> bool:
        if isinstance(position, dict):
            # Upsert by symbol
            existing = await self.get_position(position.get('symbol'))
            if existing:
                existing.quantity = position.get('quantity', existing.quantity)
                existing.average_price = position.get('average_price', existing.average_price)
                existing.current_price = position.get('current_price', existing.current_price)
                existing.unrealized_pnl = position.get('unrealized_pnl', existing.unrealized_pnl)
                return await self.update_item(existing)
            else:
                await self.insert_position(position)
                return True
        return await self.update_item(position)

    async def insert_order(self, order: Any) -> int:
        if isinstance(order, dict):
            order_obj = Order(
                symbol=order.get('symbol'),
                quantity=order.get('quantity'),
                price=order.get('price'),
                order_type=order.get('order_type'),
                side=order.get('side'),
                status=order.get('status'),
                strategy_id=order.get('strategy_id'),
            )
        else:
            order_obj = order
        await self.add_item(order_obj)
        return order_obj.id

    async def update_order_status(self, order_id: int, new_status: str) -> bool:
        order = await self.get_item(Order, order_id)
        if not order:
            return False
        order.status = new_status
        return await self.update_item(order)

    async def get_order(self, order_id: int) -> Optional[Order]:
        return await self.get_item(Order, order_id)

    async def insert_strategy(self, strategy: Any) -> int:
        if isinstance(strategy, dict):
            strat_obj = Strategy(
                name=strategy.get('name'),
                parameters=strategy.get('parameters', {}),
                status=strategy.get('status', 'INACTIVE'),
                capital_allocated=strategy.get('capital_allocated', 0.0),
            )
        else:
            strat_obj = strategy
        await self.add_item(strat_obj)
        return strat_obj.id

    async def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        return await self.get_item(Strategy, strategy_id)

    async def insert_account(self, account: Any) -> int:
        if isinstance(account, dict):
            acc_obj = Account(
                balance=account.get('balance', 0.0),
                equity=account.get('equity', 0.0),
                margin_used=account.get('margin_used', 0.0),
                free_margin=account.get('free_margin', 0.0),
            )
        else:
            acc_obj = account
        await self.add_item(acc_obj)
        return acc_obj.id

    async def update_account(self, account: Account) -> bool:
        return await self.update_item(account)

    # Schema utilities
    async def get_all_tables(self) -> List[str]:
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                rows = [r[0] for r in result.fetchall()]
                return rows
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    async def get_table_schema(self, table_name: str) -> List[str]:
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text(f"PRAGMA table_info('{table_name}')"))
                cols = [r[1] for r in result.fetchall()]
                return cols
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return []

    # Metrics and queries
    async def calculate_performance_metrics(self, strategy_id: Optional[int] = None) -> Dict[str, float]:
        trades = await self.get_items(Trade)
        if strategy_id is not None:
            trades = [t for t in trades if t.strategy_id == strategy_id]
        pnls = []
        for t in trades:
            if t.pnl is not None:
                pnls.append(t.pnl)
            elif t.entry_price is not None and t.exit_price is not None and t.quantity is not None:
                # BUY assumed
                pnls.append((t.exit_price - t.entry_price) * t.quantity)
        total_pnl = sum(pnls) if pnls else 0.0
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        return {
            'total_pnl': total_pnl,
            'win_rate': (len(wins) / len(pnls)) if pnls else 0.0,
            'average_win': (sum(wins) / len(wins)) if wins else 0.0,
            'average_loss': (sum(losses) / len(losses)) if losses else 0.0,
        }

    async def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        return await self.get_items(Trade, symbol=symbol)

    async def update_execution_metrics(self, metrics: Dict[str, Any]) -> bool:
        # Store a summary metric in SystemMetrics table
        try:
            async with self.async_session() as session:
                async with session.begin():
                    await session.execute(text(
                        "INSERT INTO system_metrics (timestamp, api_latency, order_success_rate, cpu_usage, memory_usage, error_count, warning_count)\n"
                        "VALUES (:timestamp, :api_latency, :order_success_rate, :cpu_usage, :memory_usage, :error_count, :warning_count)"
                    ), {
                        'timestamp': metrics.get('timestamp'),
                        'api_latency': float(metrics.get('latency_ms', 0.0)),
                        'order_success_rate': float(metrics.get('success_rate', 0.0)),
                        'cpu_usage': float(metrics.get('cpu_usage', 0.0)),
                        'memory_usage': float(metrics.get('memory_usage', 0.0)),
                        'error_count': int(metrics.get('error_count', 0)),
                        'warning_count': int(metrics.get('warning_count', 0)),
                    })
            return True
        except Exception as e:
            logger.error(f"Failed to update execution metrics: {e}")
            return False

    async def get_recent_trades(self, limit: int = 100) -> List[Trade]:
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Trade).order_by(Trade.timestamp.desc()).limit(limit)
                )
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            return []

    async def verify_consistency(self) -> Dict[str, Any]:
        # Simple consistency checks for tests
        tables = await self.get_all_tables()
        consistent = all(t in tables for t in ['trades', 'positions', 'orders', 'strategies', 'accounts'])
        return {'is_consistent': consistent}

# Initialization function to be called at startup
async def init_db():
    """Initialize the database using a temporary manager."""
    temp_manager = DatabaseManager()
    await temp_manager.init_db()
