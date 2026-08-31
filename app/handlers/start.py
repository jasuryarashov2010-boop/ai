from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from app.config import get_settings
from app.db.models import User
from app.db.session import SessionLocal
from app.services.user_service import get_or_create_user, get_user
from app.services.subscription_service import check
from app.utils.ui import lang_kb, sub_kb, main_kb
from app.utils.i18n import tr

router = Router()
settings = get_settings()

def ref_id(args):
    if not args: return None
    x = args.removeprefix("ref_")
    return int(x) if x.isdigit() else None

async def home(message, user):
    await message.answer(
        tr(user.language, "home") + "\n\n"
        "🤖 <b>AI Workspace</b>\n💬 <b>Support CRM</b>\n💎 <b>Plan & Daily Limits</b>",
        reply_markup=main_kb(message.from_user.id in settings.admin_ids),
        parse_mode="HTML",
    )

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, bot: Bot, command: CommandObject):
    await state.clear()
    user = await get_or_create_user(message.from_user, ref_id(command.args))
    if user.is_blocked:
        await message.answer(tr(user.language, "blocked"), parse_mode="HTML"); return
    ok, missing = await check(bot, message.from_user.id)
    if not ok:
        await message.answer(tr(user.language, "subscribe"), reply_markup=sub_kb(missing), parse_mode="HTML"); return
    if user.language not in {"uz","ru","en"}:
        await message.answer(tr("uz","choose"), reply_markup=lang_kb(), parse_mode="HTML"); return
    await home(message, user)

@router.callback_query(F.data.startswith("lang:"))
async def lang(callback: CallbackQuery):
    value = callback.data.split(":",1)[1]
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        if user: user.language = value; await s.commit()
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(tr(value, "home"), parse_mode="HTML")
    await callback.message.answer("🏠 <b>Asosiy menu</b>", reply_markup=main_kb(callback.from_user.id in settings.admin_ids), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "sub:check")
async def sub_check(callback: CallbackQuery, bot: Bot):
    user = await get_user(callback.from_user.id)
    if not user: await callback.answer("Avval /start.", show_alert=True); return
    ok, missing = await check(bot, callback.from_user.id)
    if not ok:
        await callback.answer(tr(user.language,"subscribe"), show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=sub_kb(missing)); return
    await callback.message.edit_text(tr(user.language,"home"), parse_mode="HTML")
    await callback.message.answer("🏠 <b>Asosiy menu</b>", reply_markup=main_kb(callback.from_user.id in settings.admin_ids), parse_mode="HTML")
    await callback.answer("✅")
