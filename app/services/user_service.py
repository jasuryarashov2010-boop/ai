from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from app.db.models import User, Plan, Conversation, ChatMessage, UsageEvent, Referral
from app.db.session import SessionLocal

async def get_or_create_user(tg_user, referrer_id=None):
    now = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_user.id))
        if user is None:
            ref = referrer_id if referrer_id and referrer_id != tg_user.id else None
            user = User(
                telegram_id=tg_user.id, username=tg_user.username, first_name=tg_user.first_name,
                referrer_id=ref, created_at=now, last_active_at=now
            )
            session.add(user)
            await session.flush()
            if ref:
                session.add(Referral(referrer_telegram_id=ref, referred_telegram_id=tg_user.id))
        else:
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_active_at = now
        await session.commit()
        return user

async def get_user(tg_id):
    async with SessionLocal() as session:
        return await session.scalar(select(User).where(User.telegram_id == tg_id))

async def get_plan(slug):
    async with SessionLocal() as session:
        return await session.scalar(select(Plan).where(Plan.slug == slug, Plan.active.is_(True)))

async def assign_plan(tg_id, slug, days=None):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        plan = await session.scalar(select(Plan).where(Plan.slug == slug))
        if not user or not plan:
            raise ValueError("User yoki plan topilmadi")
        user.plan_slug = slug
        user.plan_expires_at = None if slug == "free" or not days else datetime.now(timezone.utc) + timedelta(days=days)
        await session.commit()

async def create_conversation(user_id, title):
    async with SessionLocal() as session:
        obj = Conversation(user_id=user_id, title=title[:255], mode="chat")
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

async def get_conversation(user_id, conversation_id):
    async with SessionLocal() as session:
        return await session.scalar(select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        ))

async def recent_messages(conversation_id, limit=12):
    async with SessionLocal() as session:
        rows = list((await session.scalars(
            select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc()).limit(limit)
        )).all())
        rows.reverse()
        return rows

async def save_chat_pair(conversation_id, user_text, assistant_text):
    async with SessionLocal() as session:
        session.add(ChatMessage(conversation_id=conversation_id, role="user", content=user_text))
        session.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=assistant_text))
        await session.commit()

async def list_conversations(user_id, limit=15):
    async with SessionLocal() as session:
        return list((await session.scalars(
            select(Conversation).where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc()).limit(limit)
        )).all())

async def record_usage(user_id, kind):
    async with SessionLocal() as session:
        session.add(UsageEvent(user_id=user_id, kind=kind, units=1))
        await session.commit()

async def usage_totals(user_id):
    async with SessionLocal() as session:
        rows = await session.execute(
            select(UsageEvent.kind, func.sum(UsageEvent.units))
            .where(UsageEvent.user_id == user_id).group_by(UsageEvent.kind)
        )
        return {k: int(v or 0) for k, v in rows.all()}

async def referral_count(tg_id):
    async with SessionLocal() as session:
        return int(await session.scalar(
            select(func.count(Referral.id)).where(Referral.referrer_telegram_id == tg_id)
        ) or 0)
