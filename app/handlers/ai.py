import logging
from html import escape
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy import select
from app.db.models import Conversation
from app.db.session import SessionLocal
from app.services.user_service import get_user, get_plan, create_conversation, recent_messages, save_chat_pair, record_usage, list_conversations
from app.services.redis_service import consume_limit
from app.services.knowledge_service import search
from app.services.ai_service import chat, transcribe, vision, image
from app.services.document_service import extract_text, trim
from app.utils.i18n import tr

logger = logging.getLogger(__name__)
router = Router()

class AIStates(StatesGroup):
    chat = State()
    file = State()
    image = State()
    vision = State()

async def allowed(user, kind):
    p = await get_plan(user.plan_slug)
    if not p: return True
    ok, _ = await consume_limit(user.telegram_id, kind, getattr(p, f"daily_{kind}"))
    return ok

@router.callback_query(F.data == "ai:chat")
async def start_chat(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AIStates.chat)
    await state.update_data(conversation_id=None)
    await callback.message.answer("💬 <b>AI Chat</b>\n\nSavolingizni yozing. /stop bilan chiqish.", parse_mode="HTML")
    await callback.answer()

@router.message(AIStates.chat, F.text)
async def chat_message(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or not await allowed(user,"ai"):
        if user: await message.answer(tr(user.language,"limit"))
        return
    data = await state.get_data()
    cid = data.get("conversation_id")
    conv = None
    if cid:
        conv = await __import__("app.services.user_service",fromlist=["get_conversation"]).get_conversation(user.id,int(cid))
    if conv is None:
        conv = await create_conversation(user.id, message.text)
        await state.update_data(conversation_id=conv.id)
    rows = await recent_messages(conv.id)
    history = [{"role": x.role, "content": x.content} for x in rows]
    history.append({"role":"user","content":message.text})
    kb = await search(message.text)
    try:
        answer = await chat(history, [f"{x.title}: {x.content}" for x in kb])
    except Exception:
        logger.exception("AI chat error")
        await message.answer("⚠️ AI ishlamadi. OPENAI_API_KEY va modelni tekshiring."); return
    await save_chat_pair(conv.id, message.text, answer)
    await record_usage(user.id,"ai")
    await message.answer(escape(answer), parse_mode="HTML")

@router.callback_query(F.data == "ai:history")
async def history(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    rows = await list_conversations(user.id)
    text = "🗂 <b>CHATLARIM</b>\n\n" + ("\n".join(f"• #{x.id} — {x.title[:70]}" for x in rows) if rows else "Hali chat yo‘q.")
    await callback.message.answer(text, parse_mode="HTML"); await callback.answer()

@router.callback_query(F.data == "ai:voice")
async def voice_info(callback: CallbackQuery):
    await callback.message.answer("🎙 <b>Voice</b>\n\nOvozli xabar yuboring.", parse_mode="HTML")
    await callback.answer()

@router.message(F.voice)
async def voice_message(message: Message):
    user = await get_user(message.from_user.id)
    if not user: return
    if not await allowed(user,"voice"):
        await message.answer(tr(user.language,"limit")); return
    try:
        f = await message.bot.get_file(message.voice.file_id)
        stream = await message.bot.download_file(f.file_path)
        text = await transcribe(stream.read())
        answer = await chat([{"role":"user","content":text}])
        await message.answer(f"🎙 <b>Text:</b>\n{escape(text)}\n\n🤖 <b>AI:</b>\n{escape(answer)}", parse_mode="HTML")
        await record_usage(user.id,"voice"); await record_usage(user.id,"ai")
    except Exception:
        logger.exception("voice error"); await message.answer("⚠️ Voice ishlamadi.")

@router.callback_query(F.data == "ai:file")
async def file_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AIStates.file)
    await callback.message.answer("📄 <b>Fayl</b>\n\nPDF, DOCX, XLSX, CSV yoki TXT yuboring.", parse_mode="HTML")
    await callback.answer()

@router.message(AIStates.file, F.document)
async def file_message(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or not await allowed(user,"file"): 
        if user: await message.answer(tr(user.language,"limit"))
        return
    p = await get_plan(user.plan_slug)
    size = (message.document.file_size or 0)/1048576
    if p and size > p.max_file_mb:
        await message.answer(f"📦 Fayl {size:.1f} MB. Limitingiz: {p.max_file_mb} MB."); return
    try:
        f = await message.bot.get_file(message.document.file_id)
        stream = await message.bot.download_file(f.file_path)
        text = trim(extract_text(message.document.file_name or "file.txt", stream.read()))
        answer = await chat([{"role":"user","content":f"Faylni tahlil qil va foydali javob ber:\n\n{text}"}])
        await message.answer(f"📄 <b>{escape(message.document.file_name or "file")}</b>\n\n{escape(answer)}", parse_mode="HTML")
        await record_usage(user.id,"file"); await state.clear()
    except Exception:
        logger.exception("file error"); await message.answer("⚠️ Fayl tahlilida xatolik.")

@router.callback_query(F.data == "ai:image")
async def image_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AIStates.image)
    await callback.message.answer("🖼 <b>Image Generator</b>\n\nRasmni tasvirlab yozing.", parse_mode="HTML")
    await callback.answer()

@router.message(AIStates.image, F.text)
async def image_message(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or not await allowed(user,"image"):
        if user: await message.answer(tr(user.language,"limit"))
        return
    try:
        data = await image(message.text)
        await message.answer_photo(BufferedInputFile(data, filename="ai-image.png"), caption="✨ <b>AI Image</b>", parse_mode="HTML")
        await record_usage(user.id,"image"); await state.clear()
    except Exception:
        logger.exception("image error"); await message.answer("⚠️ Rasm yaratishda xatolik.")

@router.callback_query(F.data == "ai:vision")
async def vision_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AIStates.vision)
    await callback.message.answer("🧠 <b>Vision</b>\n\nRasm yuboring.", parse_mode="HTML")
    await callback.answer()

@router.message(AIStates.vision, F.photo)
async def vision_message(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user or not await allowed(user,"file"):
        if user: await message.answer(tr(user.language,"limit"))
        return
    try:
        f = await message.bot.get_file(message.photo[-1].file_id)
        stream = await message.bot.download_file(f.file_path)
        answer = await vision(stream.read(), message.caption or "Rasmni tahlil qil.")
        await message.answer(escape(answer), parse_mode="HTML")
        await record_usage(user.id,"file"); await state.clear()
    except Exception:
        logger.exception("vision error"); await message.answer("⚠️ Vision ishlamadi.")

@router.message(F.text == "/stop")
async def stop(message: Message, state: FSMContext):
    await state.clear(); await message.answer("✅ Rejim yopildi.")
