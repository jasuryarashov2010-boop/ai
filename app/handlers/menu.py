from aiogram import Router, F
from html import escape
from aiogram.types import Message, CallbackQuery
from app.config import get_settings
from app.services.user_service import get_user, get_plan, usage_totals, referral_count
from app.utils.ui import ai_kb, support_kb, profile_kb, main_kb, plans_kb

router = Router()
settings = get_settings()

@router.message(F.text == "🤖 AI Chat")
async def ai_menu(message: Message):
    await message.answer(
        "🤖 <b>AI WORKSPACE</b>\n\n"
        "💬 Chat — suhbat va maslahat\n"
        "🎙 Voice — ovozli xabarni matnga aylantirish\n"
        "📄 Fayl — PDF/DOCX/XLSX/CSV/TXT tahlili\n"
        "🖼 Rasm — AI image generator\n"
        "🧠 Vision — rasmni tushunish\n"
        "🗂 Chatlarim — tarixni davom ettirish",
        reply_markup=ai_kb(), parse_mode="HTML"
    )

@router.message(F.text == "💬 Support")
async def support(message: Message):
    await message.answer(
        "💬 <b>SUPPORT CENTER</b>\n\nMuammo turini tanlang.",
        reply_markup=support_kb(), parse_mode="HTML"
    )

@router.message(F.text == "👤 Profil")
async def profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user: return
    plan = await get_plan(user.plan_slug)
    await message.answer(
        "👤 <b>PROFIL</b>\n\n"
        f"🆔 <code>{user.telegram_id}</code>\n"
        f"👤 @{escape(user.username or '—')}\n"
        f"🌐 {user.language.upper()}\n"
        f"💎 <b>{plan.name if plan else user.plan_slug.upper()}</b>\n"
        f"📅 {user.plan_expires_at or 'Doimiy'}",
        reply_markup=profile_kb(), parse_mode="HTML"
    )

@router.message(F.text == "🔄 Yangilash")
async def refresh(message: Message):
    user = await get_user(message.from_user.id)
    if not user: return
    await message.answer(
        "🔄 <b>Ma’lumotlar yangilandi.</b>\n\n"
        f"💎 Tarif: <b>{user.plan_slug.upper()}</b>\n🆔 <code>{user.telegram_id}</code>",
        reply_markup=main_kb(message.from_user.id in settings.admin_ids), parse_mode="HTML"
    )

@router.message(F.text == "🛠 Admin Panel")
async def admin_panel(message: Message):
    if message.from_user.id not in settings.admin_ids: return
    from app.utils.ui import admin_kb
    await message.answer("🛠 <b>ADMIN CONTROL CENTER</b>", reply_markup=admin_kb(), parse_mode="HTML")

@router.callback_query(F.data == "profile:stats")
async def stats(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    data = await usage_totals(user.id)
    await callback.message.answer(
        "📊 <b>STATISTIKA</b>\n\n"
        f"💬 AI: <b>{data.get('ai',0)}</b>\n🎙 Voice: <b>{data.get('voice',0)}</b>\n"
        f"📄 File: <b>{data.get('file',0)}</b>\n🖼 Image: <b>{data.get('image',0)}</b>",
        parse_mode="HTML"
    ); await callback.answer()

@router.callback_query(F.data == "profile:plan")
async def plan(callback: CallbackQuery):
    user = await get_user(callback.from_user.id); p = await get_plan(user.plan_slug)
    await callback.message.answer(
        f"💎 <b>{p.name if p else user.plan_slug.upper()}</b>\n\n"
        f"🤖 AI: {p.daily_ai if p else '—'}/day\n🎙 Voice: {p.daily_voice if p else '—'}/day\n"
        f"📄 File: {p.daily_file if p else '—'}/day\n🖼 Image: {p.daily_image if p else '—'}/day\n"
        f"📦 Max file: {p.max_file_mb if p else '—'} MB",
        reply_markup=plans_kb(), parse_mode="HTML"
    ); await callback.answer()

@router.callback_query(F.data == "profile:referral")
async def referral(callback: CallbackQuery):
    n = await referral_count(callback.from_user.id)
    me = await callback.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{callback.from_user.id}"
    await callback.message.answer(f"🔗 <b>REFERRAL</b>\n\n👥 {n}\n\n<code>{link}</code>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("plan:"))
async def plan_request(callback: CallbackQuery):
    slug = callback.data.split(":",1)[1]
    if slug == "free": await callback.answer("FREE — asosiy tarif.", show_alert=True); return
    sup = settings.SUPPORT_USERNAME.lstrip("@") if settings.SUPPORT_USERNAME else "admin"
    await callback.message.answer(
        f"💎 <b>{slug.upper()}</b>\n\nUshbu tarifni ulash uchun @{sup} bilan bog‘laning.",
        parse_mode="HTML"
    ); await callback.answer()
