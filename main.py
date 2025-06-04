# main.py

import uvicorn
import logging
from core.config import settings
from core.app_config import create_app
from core.app_routes import include_routers, add_exception_handlers, add_health_endpoints

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = create_app()

# Add all routers and endpoints
include_routers(app)
add_exception_handlers(app)
add_health_endpoints(app)

if __name__ == "__main__":
    logger.info("🚀 Starting Axis AI application...")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
