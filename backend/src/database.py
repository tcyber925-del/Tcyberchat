"""
Database configuration and session management for SQLAlchemy and ChromaDB
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import asyncio
from typing import Optional

# Model imports moved to function to avoid circular imports
# They will be imported when initialize_database() is called

# Database URLs
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatbot.db")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

# Ensure data directories exist
os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ChromaDB setup
chroma_client = None
vector_store_initialized = False

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        # Import models here to avoid circular imports
        from .models.conversation import Conversation
        from .models.message import Message
        from .models.document import Document
        from .models.summary import Summary
        from .models.media_content import MediaContent

        Base.metadata.create_all(bind=engine)
        print("SQLAlchemy tables created successfully")
        return True
    except Exception as e:
        print(f"Failed to create tables: {e}")
        return False

def drop_tables():
    """Drop all database tables (for testing/reset)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ SQLAlchemy tables dropped successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to drop tables: {e}")
        return False

def initialize_chroma():
    """Initialize ChromaDB vector store"""
    global chroma_client, vector_store_initialized

    try:
        import chromadb
        from chromadb.config import Settings

        chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )

        # Test connection by creating/getting a collection
        test_collection = chroma_client.get_or_create_collection("test_init")
        chroma_client.delete_collection("test_init")

        vector_store_initialized = True
        print("ChromaDB initialized successfully")
        return True

    except ImportError:
        print("ChromaDB not available - install chromadb package")
        return False
    except Exception as e:
        print(f"Failed to initialize ChromaDB: {e}")
        return False

def initialize_database():
    """Initialize both SQLAlchemy and ChromaDB"""
    print("Initializing databases...")

    # Initialize SQLAlchemy
    sql_success = create_tables()

    # Initialize ChromaDB
    chroma_success = initialize_chroma()

    if sql_success and chroma_success:
        print("All databases initialized successfully!")
        return True
    else:
        print("Some databases failed to initialize")
        return False

def get_database_status():
    """Get status of all database systems"""
    # Check SQLAlchemy
    sql_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            sql_status = "connected"
    except Exception as e:
        sql_status = f"error: {str(e)}"

    # Check ChromaDB
    chroma_status = "not_initialized" if not vector_store_initialized else "ready"
    if chroma_client:
        try:
            collections = chroma_client.list_collections()
            chroma_status = f"ready ({len(collections)} collections)"
        except Exception as e:
            chroma_status = f"error: {str(e)}"

    return {
        "sqlalchemy": {
            "status": sql_status,
            "url": DATABASE_URL.replace(os.path.dirname(DATABASE_URL), "...")  # Hide path for security
        },
        "chromadb": {
            "status": chroma_status,
            "persist_dir": CHROMA_PERSIST_DIR
        },
        "overall_status": "healthy" if sql_status == "connected" and "ready" in chroma_status else "degraded"
    }

# Auto-initialize on import (in development)
if __name__ != "__main__":
    # Only auto-initialize if not running as script
    initialize_database()