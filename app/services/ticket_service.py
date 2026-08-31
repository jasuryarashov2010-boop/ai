from sqlalchemy import select
from app.db.models import User, Ticket, TicketMessage
from app.db.session import SessionLocal

async def create_ticket(tg_id, category):
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.telegram_id == tg_id))
        if not user: raise ValueError("User topilmadi")
        t = Ticket(user_id=user.id, category=category, subject=f"{category} support")
        s.add(t); await s.flush()
        s.add(TicketMessage(ticket_id=t.id, sender_type="user", sender_telegram_id=tg_id, content=f"Ticket: {category}"))
        await s.commit(); await s.refresh(t)
        return t

async def add_message(ticket_id, sender_type, sender_id, content):
    async with SessionLocal() as s:
        t = await s.scalar(select(Ticket).where(Ticket.id == ticket_id))
        if not t: return
        t.status = "in_progress"
        s.add(TicketMessage(ticket_id=ticket_id, sender_type=sender_type, sender_telegram_id=sender_id, content=content))
        await s.commit()

async def close(ticket_id):
    async with SessionLocal() as s:
        t = await s.scalar(select(Ticket).where(Ticket.id == ticket_id))
        if t: t.status = "closed"; await s.commit()

async def open_tickets():
    async with SessionLocal() as s:
        return list((await s.scalars(
            select(Ticket).where(Ticket.status.in_(["pending","in_progress"])).order_by(Ticket.updated_at.asc()).limit(40)
        )).all())
