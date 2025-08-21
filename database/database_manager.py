"""
Database manager for QuantHybrid system.
"""
import asyncio
from typing import Any, List, Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from config.settings import DATABASE_URL
from config.logging_config import get_logger
from database.models import Base

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
        self._initialized = False
    
    async def init_db(self):
        """Initialize database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    # Compatibility methods expected by tests
    async def initialize(self, test_mode: bool = False):
        """Alias used by tests to (re)initialize the database."""
        await self.init_db()

    def initialize_database(self):
        """Synchronous shim used by some tests to initialize schema."""
        asyncio.get_event_loop().run_until_complete(self.init_db())
    
    async def add_item(self, item: Any) -> bool:
        """Add a single item to the database."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    session.add(item)
                await session.commit()
            logger.debug(f"Added item to {item.__tablename__}")
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
                await session.commit()
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
                await session.commit()
            logger.debug(f"Updated item in {item.__tablename__}")
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
                await session.commit()
            logger.debug(f"Deleted item from {item.__tablename__}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete item: {str(e)}")
            return False

# Initialization function to be called at startup
async def init_db():
    """Initialize the database using a temporary manager."""
    temp_manager = DatabaseManager()
    await temp_manager.init_db()
