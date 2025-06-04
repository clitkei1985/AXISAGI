import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def create_default_admin_user():
    """Create default admin user if it doesn't exist"""
    try:
        from core.database import SessionLocal, User
        from core.security.auth import get_password_hash
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # Check if admin user already exists
            existing_admin = db.query(User).filter(User.username == "admin").first()
            if not existing_admin:
                # Create admin user with credentials: admin/1609
                hashed_password = get_password_hash("1609")
                
                admin_user = User(
                    username="admin",
                    email="admin@axis.local",
                    hashed_password=hashed_password,
                    is_admin=True,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                db.add(admin_user)
                db.commit()
                logger.info("✅ Default admin user created (admin/1609)")
            else:
                logger.info("✅ Admin user already exists")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management. (Features: 165, 166, 167, 168, 169, 170, 171)"""
    # Startup
    logger.info("🚀 Starting Axis AI...")
    
    # Initialize database
    try:
        from core.database import create_tables
        create_tables()
        logger.info("✅ Database initialized")
        
        # Create default admin user
        create_default_admin_user()
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        
    # Initialize memory system
    try:
        from modules.memory.memory_manager import initialize_memory_system
        await initialize_memory_system()
        logger.info("✅ Memory system initialized")
    except Exception as e:
        logger.error(f"❌ Memory system initialization failed: {e}")
        
    # Initialize plugin system
    try:
        from modules.plugin_system.manager import initialize_plugin_system
        await initialize_plugin_system()
        logger.info("✅ Plugin system initialized")
    except Exception as e:
        logger.error(f"❌ Plugin system initialization failed: {e}")
        
    # Start background services
    try:
        from modules.performance.monitor import start_monitoring
        await start_monitoring()
        logger.info("✅ Performance monitoring started")
    except Exception as e:
        logger.error(f"❌ Performance monitoring failed: {e}")
        
    logger.info("🎉 Axis AI started successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Axis AI...")
    
    # Cleanup memory system
    try:
        from modules.memory.memory_manager import cleanup_memory_system
        await cleanup_memory_system()
        logger.info("✅ Memory system cleaned up")
    except Exception as e:
        logger.error(f"❌ Memory cleanup failed: {e}")
        
    # Stop monitoring
    try:
        from modules.performance.monitor import stop_monitoring
        await stop_monitoring()
        logger.info("✅ Performance monitoring stopped")
    except Exception as e:
        logger.error(f"❌ Performance monitoring stop failed: {e}")
        
    logger.info("👋 Axis AI shutdown complete") 