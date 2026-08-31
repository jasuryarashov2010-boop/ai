from sqlalchemy import select, func
from app.db.models import User, Ticket, Operator, RequiredChannel, KnowledgeItem, AuditLog, Feedback
from app.db.session import SessionLocal

async def dashboard():
    async with SessionLocal() as s:
        return {
            "users": int(await s.scalar(select(func.count(User.id))) or 0),
            "tickets": int(await s.scalar(select(func.count(Ticket.id)).where(Ticket.status.in_(["pending","in_progress"]))) or 0),
            "operators": int(await s.scalar(select(func.count(Operator.id)).where(Operator.active.is_(True))) or 0),
            "knowledge": int(await s.scalar(select(func.count(KnowledgeItem.id)).where(KnowledgeItem.active.is_(True))) or 0),
            "feedback": int(await s.scalar(select(func.count(Feedback.id))) or 0),
        }

async def log(admin_id, action, target=None, details=None):
    async with SessionLocal() as s:
        s.add(AuditLog(admin_telegram_id=admin_id, action=action, target=target, details=details or {}))
        await s.commit()

async def operators():
    async with SessionLocal() as s:
        return list((await s.scalars(select(Operator).where(Operator.active.is_(True)))).all())

async def add_operator(tg_id, role="operator"):
    async with SessionLocal() as s:
        x = await s.scalar(select(Operator).where(Operator.telegram_id == tg_id))
        if x: x.active, x.role = True, role
        else: s.add(Operator(telegram_id=tg_id, role=role, active=True))
        await s.commit()

async def remove_operator(tg_id):
    async with SessionLocal() as s:
        x = await s.scalar(select(Operator).where(Operator.telegram_id == tg_id))
        if x: x.active = False
        await s.commit()

async def list_channels():
    async with SessionLocal() as s:
        return list((await s.scalars(select(RequiredChannel).where(RequiredChannel.active.is_(True)))).all())

async def add_channel(chat_id, title, username, invite):
    async with SessionLocal() as s:
        x = await s.scalar(select(RequiredChannel).where(RequiredChannel.chat_id == chat_id))
        if x:
            x.title, x.username, x.invite_url, x.active = title, username, invite, True
        else:
            s.add(RequiredChannel(chat_id=chat_id, title=title, username=username, invite_url=invite, active=True))
        await s.commit()

async def remove_channel(chat_id):
    async with SessionLocal() as s:
        x = await s.scalar(select(RequiredChannel).where(RequiredChannel.chat_id == chat_id))
        if x: x.active = False
        await s.commit()

async def add_knowledge(title, content, tags):
    async with SessionLocal() as s:
        s.add(KnowledgeItem(title=title, content=content, tags=tags, active=True))
        await s.commit()

async def recent_logs():
    async with SessionLocal() as s:
        return list((await s.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(30))).all())
