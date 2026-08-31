import asyncio
import logging
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import get_settings
from .base import Base
from .models import Plan, LearningLesson

settings = get_settings()
logger = logging.getLogger(__name__)

def normalize_db_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url

engine = create_async_engine(
    normalize_db_url(settings.DATABASE_URL),
    pool_pre_ping=True, pool_recycle=1800, pool_size=3, max_overflow=2
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

PLANS = [
    dict(slug="free", name="FREE", daily_ai=settings.FREE_DAILY_AI, daily_voice=settings.FREE_DAILY_VOICE,
         daily_file=settings.FREE_DAILY_FILE, daily_image=settings.FREE_DAILY_IMAGE, max_file_mb=10, priority_support=False),
    dict(slug="comfort", name="COMFORT", daily_ai=100, daily_voice=20, daily_file=20, daily_image=5, max_file_mb=25, priority_support=False),
    dict(slug="pro", name="PRO", daily_ai=300, daily_voice=75, daily_file=50, daily_image=15, max_file_mb=50, priority_support=True),
    dict(slug="premium", name="PREMIUM", daily_ai=1000, daily_voice=250, daily_file=150, daily_image=50, max_file_mb=100, priority_support=True),
]
LESSONS = [
    dict(slug="foundations", title="Prompt asoslari", level="beginner",
         body="Role, goal, context, constraints va output formatni aniq berish.",
         tags=["prompt", "basics"]),
    dict(slug="few-shot", title="Few-shot prompting", level="intermediate",
         body="Kichik miqdorda yaxshi input/output misollari bilan kutilgan formatni ko‘rsatish.",
         tags=["examples", "prompt"]),
    dict(slug="structured", title="Structured output", level="intermediate",
         body="Natijani JSON, jadval yoki aniq schema shaklida talab qilish.",
         tags=["format", "json"]),
    dict(slug="evaluation", title="AI natijasini baholash", level="advanced",
         body="Accuracy, relevance, completeness, safety va style mezonlari bilan tekshirish.",
         tags=["evaluation", "quality"]),
]

async def init_db():
    last = None
    for attempt in range(1, 6):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Safe additive repair for the old timestamp failure.
                await conn.execute(text(
                    "ALTER TABLE learning_lessons ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP"
                ))
            async with SessionLocal() as session:
                for row in PLANS:
                    obj = await session.scalar(select(Plan).where(Plan.slug == row["slug"]))
                    if obj is None:
                        session.add(Plan(**row))
                    else:
                        for k, v in row.items():
                            if k != "slug":
                                setattr(obj, k, v)
                for row in LESSONS:
                    obj = await session.scalar(select(LearningLesson).where(LearningLesson.slug == row["slug"]))
                    if obj is None:
                        session.add(LearningLesson(**row))
                    else:
                        obj.title, obj.level, obj.body, obj.tags, obj.active = (
                            row["title"], row["level"], row["body"], row["tags"], True
                        )
                await session.commit()
            logger.info("database initialized")
            return
        except Exception as exc:
            last = exc
            logger.exception("database init attempt %s failed", attempt)
            await asyncio.sleep(min(attempt * 2, 10))
    raise RuntimeError(f"Database initialization failed: {last}") from last

async def check_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("database health check failed")
        return False
