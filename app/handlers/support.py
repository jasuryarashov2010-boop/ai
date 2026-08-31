from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from app.db.models import User, Ticket, Feedback
from app.db.session import SessionLocal
from app.services.ticket_service import create_ticket, add_message
from app.utils.ui import support_kb

router = Router()

class SupportStates(StatesGroup):
    ticket = State()
    feedback = State()

@router.callback_query(F.data.startswith("ticket:"))
async def create(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":",1)[1]
    t = await create_ticket(callback.from_user.id, category)
    await state.set_state(SupportStates.ticket); await state.update_data(ticket_id=t.id)
    await callback.message.answer(
        f"🎫 <b>Ticket #{t.id}</b>\n\n📌 {category}\n🟡 Kutilmoqda\n\nMuammoingizni yozing.",
        parse_mode="HTML"
    ); await callback.answer("✅ Ticket yaratildi")

@router.message(SupportStates.ticket, F.text)
async def ticket_message(message: Message, state: FSMContext):
    d = await state.get_data()
    if not d.get("ticket_id"): return
    await add_message(int(d["ticket_id"]), "user", message.from_user.id, message.text)
    await message.answer("✅ Xabaringiz ticketga qo‘shildi.")

@router.callback_query(F.data == "support:rating")
async def rating(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.feedback)
    await callback.message.answer("⭐ 1–5 raqam yuboring."); await callback.answer()

@router.callback_query(F.data == "support:feedback")
async def feedback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.feedback)
    await callback.message.answer("📝 Fikringizni yozing."); await callback.answer()

@router.message(SupportStates.feedback, F.text)
async def save_feedback(message: Message, state: FSMContext):
    user = await __import__("app.services.user_service",fromlist=["get_user"]).get_user(message.from_user.id)
    if not user: return
    rating = int(message.text) if message.text.isdigit() and 1 <= int(message.text) <= 5 else None
    async with SessionLocal() as s:
        s.add(Feedback(user_id=user.id, kind="rating" if rating else "feedback", text=message.text, rating=rating))
        await s.commit()
    await state.clear(); await message.answer("✅ Rahmat! Fikringiz saqlandi.")

@router.callback_query(F.data == "profile:tickets")
async def my_tickets(callback: CallbackQuery):
    user = await __import__("app.services.user_service",fromlist=["get_user"]).get_user(callback.from_user.id)
    async with SessionLocal() as s:
        rows = list((await s.scalars(select(Ticket).where(Ticket.user_id == user.id).order_by(Ticket.updated_at.desc()).limit(15))).all())
    text = "🎫 <b>TICKETLARIM</b>\n\n" + ("\n".join(f"• #{x.id} — {x.category} — {x.status}" for x in rows) if rows else "Ticket yo‘q.")
    await callback.message.answer(text, reply_markup=support_kb(), parse_mode="HTML"); await callback.answer()
