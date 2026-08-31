import logging
from datetime import datetime, timezone
from redis.asyncio import Redis
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
redis: Redis | None = None

async def init_redis():
    global redis
    if not settings.REDIS_URL:
        logger.warning("REDIS_URL not set; using MemoryStorage/fallback.")
        return
    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
        await client.ping()
        redis = client
        logger.info("redis connected")
    except Exception:
        redis = None
        logger.exception("redis unavailable; continuing with fallback")

async def close_redis():
    global redis
    if redis:
        await redis.aclose()
    redis = None

async def check_redis():
    try:
        return bool(redis and await redis.ping())
    except Exception:
        return False

async def consume_limit(tg_id: int, kind: str, limit: int):
    if redis is None:
        return True, -1
    key = f"v300:usage:{datetime.now(timezone.utc).date().isoformat()}:{tg_id}:{kind}"
    try:
        used = await redis.incr(key)
        await redis.expire(key, 90000)
        if used > limit:
            await redis.decr(key)
            return False, 0
        return True, limit - used
    except Exception:
        logger.exception("limit check failed")
        return True, -1
