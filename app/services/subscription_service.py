import logging
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from sqlalchemy import select
from app.db.models import RequiredChannel
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

async def channels():
    async with SessionLocal() as session:
        return list((await session.scalars(
            select(RequiredChannel).where(RequiredChannel.active.is_(True)).order_by(RequiredChannel.id)
        )).all())

async def check(bot: Bot, user_id: int):
    missing = []
    for ch in await channels():
        url = ch.invite_url or (f"https://t.me/{ch.username.lstrip('@')}" if ch.username else None)
        try:
            member = await bot.get_chat_member(ch.chat_id, user_id)
            joined = member.status in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}
        except Exception:
            joined = False
            logger.exception("channel membership check failed: %s", ch.chat_id)
        if not joined:
            missing.append({"title": ch.title, "url": url})
    return not missing, missing
