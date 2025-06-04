from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

def configure_routers(app: FastAPI):
    """Configure and include all routers in the FastAPI app"""
    
    # Import routers
    from interfaces.auth.router import router as auth_router
    from interfaces.chat.router import router as chat_router
    from interfaces.admin.router import router as admin_router
    from interfaces.user.router import router as user_router
    from interfaces.memory.router import router as memory_router
    from interfaces.audio.router import router as audio_router
    from interfaces.image.router import router as image_router
    from interfaces.llm.router import router as llm_router
    from interfaces.plugins.router import router as plugin_router
    from interfaces.analytics.router import router as analytics_router
    from interfaces.code.router import router as code_router
    from interfaces.web.router import router as web_router
    from interfaces.export.router import router as export_router
    from interfaces.performance.router import router as performance_router
    from interfaces.scheduler.router import router as scheduler_router
    from interfaces.rules.router import router as rules_router
    from interfaces.env.router import router as env_router
    from interfaces.search.router import router as search_router
    from interfaces.file.router import router as file_router
    from modules.frontend_ui.router import router as frontend_router
    from interfaces.system.router import router as system_router

    # Include routers with appropriate prefixes and tags
    router_configs = [
        (web_router, "", ["Web Interface & Search"]),
        (auth_router, "/api/auth", ["Authentication"]),
        (chat_router, "/api/chat", ["Chat & Messaging"]),
        (memory_router, "/api/memory", ["Memory & Knowledge"]),
        (llm_router, "/api/llm", ["LLM & AI"]),
        (audio_router, "/api/audio", ["Audio Processing"]),
        (image_router, "/api/image", ["Image Processing"]),
        (analytics_router, "/api/analytics", ["Analytics & Reporting"]),
        (admin_router, "/api/admin", ["Administration"]),
        (user_router, "/api/user", ["User Management"]),
        (export_router, "/api/export", ["Export & Integration"]),
        (code_router, "/api/code", ["Code Analysis"]),
        (performance_router, "/api/performance", ["Performance Monitoring"]),
        (plugin_router, "/api/plugins", ["Plugin System"]),
        (scheduler_router, "/api/scheduler", ["Task Scheduling"]),
        (rules_router, "/api/rules", ["Rules & Governance"]),
        (env_router, "/api/env", ["Environment Management"]),
        (search_router, "/api/search", ["Search"]),
        (file_router, "/api/file", ["File Management"]),
        (frontend_router, "/api/frontend", ["Frontend UI"]),
        (system_router, "", ["System Management"])
    ]
    
    for router, prefix, tags in router_configs:
        if prefix:
            app.include_router(router, prefix=prefix, tags=tags)
        else:
            app.include_router(router, tags=tags)
    
    logger.info(f"Configured {len(router_configs)} routers") 