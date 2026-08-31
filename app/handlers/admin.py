import asyncio
import logging
from html import escape
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func
from app.config import get_settings
from app.db.models import User, Ticket, UsageEvent, Feedback, LearningLesson
from app.db.session import SessionLocal, check_db
from app.services.redis_service import check_redis
from app.services.admin_service import dashboard, operators, add_operator, remove_operator, list_channels, add_channel, remove_channel, add_knowledge, recent_logs, log
from app.services.user_service import assign_plan
from app.services.ticket_service import open_tickets, close as close_ticket
from app.services.ai_service import coach
from app.utils.ui import admin_kb, learning_kb

router = Router()
settings = get_settings()
logger = logging.getLogger(__name__)

def is_admin(event):
    u = getattr(event, "from_user", None)
    return bool(u and u.id in settings.admin_ids)

async def deny(event):
    if hasattr(event, "answer"): await event.answer("⛔ Faqat adminlar uchun.", show_alert=True)

class AStates(StatesGroup):
    user_search = State()
    user_action = State()
    operator = State()
    channel = State()
    knowledge = State()
    broadcast = State()
    learning = State()

@router.callback_query(F.data == "adm:dashboard")
async def dashboard_view(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    d = await dashboard()
    await callback.message.answer(
        "📊 <b>ADMIN DASHBOARD</b>\n\n"
        f"👥 Users: <b>{d['users']}</b>\n🎫 Open Tickets: <b>{d['tickets']}</b>\n"
        f"👨‍💻 Operators: <b>{d['operators']}</b>\n🧠 Knowledge: <b>{d['knowledge']}</b>\n"
        f"⭐ Feedback: <b>{d['feedback']}</b>", parse_mode="HTML"
    ); await callback.answer()

@router.callback_query(F.data == "adm:users")
async def users_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback): return await deny(callback)
    await state.set_state(AStates.user_search)
    await callback.message.answer("👥 Telegram ID yuboring."); await callback.answer()

@router.message(AStates.user_search, F.text)
async def user_search(message: Message, state: FSMContext):
    if not is_admin(message): return
    if not message.text.isdigit(): await message.answer("ID raqam bo‘lishi kerak."); return
    tg = int(message.text)
    async with SessionLocal() as s: user = await s.scalar(select(User).where(User.telegram_id == tg))
    if not user: await message.answer("❌ User topilmadi."); return
    await state.set_state(AStates.user_action); await state.update_data(target=tg)
    await message.answer(
        f"👤 <b>User</b>\n\n🆔 <code>{tg}</code>\n👤 @{user.username or '—'}\n"
        f"💎 {user.plan_slug}\n🚫 Blocked: {user.is_blocked}\n\n"
        "<code>pro 30</code>\n<code>free</code>\n<code>block</code>\n<code>unblock</code>",
        parse_mode="HTML"
    )

@router.message(AStates.user_action, F.text)
async def user_action(message: Message, state: FSMContext):
    if not is_admin(message): return
    p = message.text.split()
    d = await state.get_data(); tg = int(d["target"])
    if not p: return
    if p[0] in {"block","unblock"}:
        async with SessionLocal() as s:
            u = await s.scalar(select(User).where(User.telegram_id == tg))
            u.is_blocked = p[0] == "block"; await s.commit()
        await log(message.from_user.id, p[0], str(tg))
        await message.answer("✅ Bajarildi.")
    elif p[0] in {"free","comfort","pro","premium"}:
        days = int(p[1]) if len(p)>1 and p[1].isdigit() else None
        await assign_plan(tg, p[0], days)
        await log(message.from_user.id, "plan_change", str(tg), {"plan":p[0],"days":days})
        await message.answer(f"✅ {p[0].upper()} faollashtirildi.")
    await state.clear()

@router.callback_query(F.data == "adm:operators")
async def operators_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback): return await deny(callback)
    rows = await operators()
    text = "👨‍💻 <b>OPERATORS</b>\n\n" + ("\n".join(f"• {x.telegram_id} — {x.role}" for x in rows) or "Yo‘q.")
    await callback.message.answer(text + "\n\n<code>add 123 operator</code>\n<code>remove 123</code>", parse_mode="HTML")
    await state.set_state(AStates.operator); await callback.answer()

@router.message(AStates.operator, F.text)
async def operator_manage(message: Message, state: FSMContext):
    if not is_admin(message): return
    p = message.text.split()
    if len(p)>=2 and p[0]=="add" and p[1].isdigit(): await add_operator(int(p[1]), p[2] if len(p)>2 else "operator"); await message.answer("✅")
    elif len(p)==2 and p[0]=="remove" and p[1].isdigit(): await remove_operator(int(p[1])); await message.answer("✅")
    else: await message.answer("Format: add 123 operator")
    await state.clear()

@router.callback_query(F.data == "adm:channels")
async def channels_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback): return await deny(callback)
    rows = await list_channels()
    text = "📢 <b>CHANNELS</b>\n\n" + ("\n".join(f"• {x.title} — {x.chat_id}" for x in rows) or "Yo‘q.")
    await callback.message.answer(text + "\n\n<code>add -100123 Title @username https://t.me/x</code>\n<code>remove -100123</code>", parse_mode="HTML")
    await state.set_state(AStates.channel); await callback.answer()

@router.message(AStates.channel, F.text)
async def channel_manage(message: Message, state: FSMContext):
    if not is_admin(message): return
    p = message.text.split()
    if len(p)>=3 and p[0]=="add":
        await add_channel(p[1], p[2].replace("_"," "), p[3] if len(p)>3 else None, p[4] if len(p)>4 else None)
        await message.answer("✅ Kanal qo‘shildi.")
    elif len(p)==2 and p[0]=="remove":
        await remove_channel(p[1]); await message.answer("✅")
    else: await message.answer("Format noto‘g‘ri.")
    await state.clear()

@router.callback_query(F.data == "adm:knowledge")
async def knowledge_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback): return await deny(callback)
    await state.set_state(AStates.knowledge)
    await callback.message.answer("🧠 <b>Knowledge</b>\n1-qator title, keyingi qism content.", parse_mode="HTML")
    await callback.answer()

@router.message(AStates.knowledge, F.text)
async def knowledge_save(message: Message, state: FSMContext):
    if not is_admin(message): return
    parts = message.text.split("\n",1)
    if len(parts)!=2: await message.answer("Title va content kerak."); return
    await add_knowledge(parts[0], parts[1], parts[0].split()[:5])
    await log(message.from_user.id,"knowledge_add",parts[0][:200])
    await state.clear(); await message.answer("✅ Knowledge saqlandi.")

@router.callback_query(F.data == "adm:tickets")
async def tickets_view(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    rows = await open_tickets()
    text = "🎫 <b>OPEN TICKETS</b>\n\n" + ("\n".join(f"• #{x.id} — {x.category} — {x.status}" for x in rows) or "Ochiq ticket yo‘q.")
    await callback.message.answer(text + "\n\n<code>/close_ticket ID</code>", parse_mode="HTML"); await callback.answer()

@router.message(F.text.startswith("/close_ticket"))
async def close_cmd(message: Message):
    if not is_admin(message): return
    p = message.text.split()
    if len(p)==2 and p[1].isdigit(): await close_ticket(int(p[1])); await message.answer("✅ Ticket yopildi.")
    else: await message.answer("Format: /close_ticket 123")

@router.callback_query(F.data == "adm:plans")
async def plans_view(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    await callback.message.answer("💎 <b>PLANS</b>\n\nFREE 20/3/3/1\nCOMFORT 100/20/20/5\nPRO 300/75/50/15\nPREMIUM 1000/250/150/50", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "adm:learning")
async def learning_view(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    await callback.message.answer("🧑‍🏫 <b>AI LEARNING CENTER</b>", reply_markup=learning_kb(), parse_mode="HTML"); await callback.answer()

@router.callback_query(F.data.startswith("learn:"))
async def learning_action(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback): return await deny(callback)
    task = callback.data.split(":",1)[1]
    if task == "lessons":
        async with SessionLocal() as s:
            rows = list((await s.scalars(select(LearningLesson).where(LearningLesson.active.is_(True)).order_by(LearningLesson.id))).all())
        text = "📚 <b>LESSONS</b>\n\n" + "\n\n".join(f"<b>{x.title}</b> — {x.level}\n{x.body}" for x in rows)
        await callback.message.answer(text, parse_mode="HTML"); await callback.answer(); return
    await state.set_state(AStates.learning); await state.update_data(task=task)
    prompts = {"learn":"Mavzuni yozing.","build":"Vazifani yozing.","improve":"Promptni yuboring.","analyze":"Promptni yuboring.","post":"Mavzuni yozing.","workflow":"Vazifani yozing."}
    await callback.message.answer("🧑‍🏫 " + prompts.get(task,"Requestni yozing.")); await callback.answer()

@router.message(AStates.learning, F.text)
async def learning(message: Message, state: FSMContext):
    if not is_admin(message): return
    task = (await state.get_data()).get("task","learn")
    try:
        result = await coach(message.text, task)
        await message.answer(escape(result), parse_mode="HTML")
    except Exception:
        logger.exception("learning failed")
        await message.answer("⚠️ AI Learning ishlamadi. OPENAI_API_KEYni tekshiring.")
    await state.clear()

@router.callback_query(F.data == "adm:broadcast")
async def broadcast_view(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback): return await deny(callback)
    await state.set_state(AStates.broadcast)
    await callback.message.answer("📢 Xabarni yuboring. Barcha block qilinmagan userlarga ketadi.")
    await callback.answer()

@router.message(AStates.broadcast, F.text)
async def broadcast(message: Message, state: FSMContext):
    if not is_admin(message): return
    async with SessionLocal() as s:
        ids = list((await s.scalars(select(User.telegram_id).where(User.is_blocked.is_(False)))).all())
    sent = failed = 0
    for tg in ids:
        try:
            await message.bot.send_message(int(tg), message.text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await log(message.from_user.id,"broadcast",details={"sent":sent,"failed":failed})
    await state.clear(); await message.answer(f"📢 Tugadi.\n✅ {sent}\n❌ {failed}")

@router.callback_query(F.data == "adm:analytics")
async def analytics(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    async with SessionLocal() as s:
        rows = await s.execute(select(UsageEvent.kind, func.sum(UsageEvent.units)).group_by(UsageEvent.kind))
        avg = await s.scalar(select(func.avg(Feedback.rating)).where(Feedback.rating.is_not(None)))
    usage = "\n".join(f"• {k}: <b>{int(v or 0)}</b>" for k,v in rows.all()) or "Usage yo‘q."
    await callback.message.answer(f"📈 <b>ANALYTICS</b>\n\n{usage}\n\n⭐ Rating: <b>{float(avg or 0):.2f}</b>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "adm:logs")
async def logs(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    rows = await recent_logs()
    text = "📜 <b>LOGS</b>\n\n" + ("\n".join(f"• {x.created_at:%Y-%m-%d %H:%M} — {x.action} — {x.target or '—'}" for x in rows) or "Yo‘q.")
    await callback.message.answer(text, parse_mode="HTML"); await callback.answer()

@router.callback_query(F.data == "adm:health")
async def health(callback: CallbackQuery):
    if not is_admin(callback): return await deny(callback)
    db = await check_db(); rd = await check_redis()
    await callback.message.answer(
        f"🟢 <b>HEALTH</b>\n\nTelegram: ✅\nPostgreSQL: {'✅' if db else '❌'}\n"
        f"Redis: {'✅' if rd else '⚪'}\nWebhook: {'✅' if settings.webhook_url else '❌'}",
        parse_mode="HTML"
    ); await callback.answer()
