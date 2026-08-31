import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.config import get_settings
from app.db.session import init_db, check_db
from app.services import redis_service
from app.services.redis_service import init_redis, close_redis, check_redis
from app.handlers.start import router as start_router
from app.handlers.menu import router as menu_router
from app.handlers.ai import router as ai_router
from app.handlers.support import router as support_router
from app.handlers.admin import router as admin_router

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai-supporter-v300")
bot = Bot(token=settings.BOT_TOKEN)
dp: Dispatcher | None = None

def build_dispatcher():
    storage = RedisStorage(redis=redis_service.redis) if redis_service.redis else MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    # Explicit registration prevents "Update ... is not handled".
    dispatcher.include_router(start_router)
    dispatcher.include_router(menu_router)
    dispatcher.include_router(ai_router)
    dispatcher.include_router(support_router)
    dispatcher.include_router(admin_router)
    logger.info("routers registered: start menu ai support admin")
    return dispatcher

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dp
    await init_redis()
    dp = build_dispatcher()
    await init_db()

    if settings.webhook_url:
        await bot.set_webhook(
            settings.webhook_url,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=False,
        )
        logger.info("webhook configured: %s", settings.webhook_url)
        logger.info("allowed updates: %s", dp.resolve_used_update_types())
    else:
        logger.error("WEBHOOK URL missing: set PUBLIC_BASE_URL or use Render RENDER_EXTERNAL_URL")

    yield

    if settings.webhook_url:
        try:
            await bot.delete_webhook(drop_pending_updates=False)
        except Exception:
            logger.exception("webhook delete failed")
    await close_redis()
    await bot.session.close()

app = FastAPI(title="AI Supporter V300", version="3.0.0", lifespan=lifespan)

@app.get("/")
async def root():
    return {"service":"AI Supporter V300","status":"online","webhook_configured":bool(settings.webhook_url)}

@app.get("/health")
async def health():
    db = await check_db()
    rd = await check_redis()
    return {
        "status":"ok" if db else "degraded",
        "database":db,
        "redis":rd,
        "webhook_configured":bool(settings.webhook_url),
        "webhook_url":settings.webhook_url,
        "routers_registered":dp is not None,
    }

@app.post(settings.WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    if dp is None:
        return {"ok":False,"error":"dispatcher_not_ready"}
    from aiogram.types import Update
    update = Update.model_validate(await request.json())
    try:
        await dp.feed_update(bot, update)
    except Exception:
        logger.exception("update handling failed")
    return {"ok":True}
