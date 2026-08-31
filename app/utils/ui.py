from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 UZ", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 EN", callback_data="lang:en"),
    ]])

def sub_kb(channels):
    rows = []
    for x in channels:
        if x["url"]:
            rows.append([InlineKeyboardButton(text=f"📢 {x['title']}", url=x["url"])])
    rows.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="sub:check")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def main_kb(admin=False):
    rows = [
        [KeyboardButton(text="🤖 AI Chat"), KeyboardButton(text="💬 Support")],
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="🔄 Yangilash")],
    ]
    if admin:
        rows.append([KeyboardButton(text="🛠 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)

def ai_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Chat", callback_data="ai:chat"),
         InlineKeyboardButton(text="🎙 Voice", callback_data="ai:voice")],
        [InlineKeyboardButton(text="📄 Fayl", callback_data="ai:file"),
         InlineKeyboardButton(text="🖼 Rasm", callback_data="ai:image")],
        [InlineKeyboardButton(text="🧠 Vision", callback_data="ai:vision"),
         InlineKeyboardButton(text="🗂 Chatlarim", callback_data="ai:history")],
    ])

def support_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To‘lov", callback_data="ticket:payment"),
         InlineKeyboardButton(text="🤖 AI", callback_data="ticket:ai")],
        [InlineKeyboardButton(text="🐞 Texnik", callback_data="ticket:technical"),
         InlineKeyboardButton(text="💎 Tarif", callback_data="ticket:plan")],
        [InlineKeyboardButton(text="❓ Boshqa", callback_data="ticket:other")],
        [InlineKeyboardButton(text="⭐ Baholash", callback_data="support:rating"),
         InlineKeyboardButton(text="📝 Feedback", callback_data="support:feedback")],
    ])

def profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="profile:stats"),
         InlineKeyboardButton(text="💎 Tarifim", callback_data="profile:plan")],
        [InlineKeyboardButton(text="🔗 Referral", callback_data="profile:referral"),
         InlineKeyboardButton(text="🎫 Ticketlarim", callback_data="profile:tickets")],
    ])

def plans_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 FREE", callback_data="plan:free"),
         InlineKeyboardButton(text="💙 COMFORT", callback_data="plan:comfort")],
        [InlineKeyboardButton(text="💎 PRO", callback_data="plan:pro"),
         InlineKeyboardButton(text="👑 PREMIUM", callback_data="plan:premium")],
    ])

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Dashboard", callback_data="adm:dashboard"),
         InlineKeyboardButton(text="👥 Users", callback_data="adm:users")],
        [InlineKeyboardButton(text="🎫 Tickets", callback_data="adm:tickets"),
         InlineKeyboardButton(text="👨‍💻 Operators", callback_data="adm:operators")],
        [InlineKeyboardButton(text="💎 Plans", callback_data="adm:plans"),
         InlineKeyboardButton(text="📢 Channels", callback_data="adm:channels")],
        [InlineKeyboardButton(text="🧠 Knowledge", callback_data="adm:knowledge"),
         InlineKeyboardButton(text="🧑‍🏫 AI Learning", callback_data="adm:learning")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="adm:broadcast"),
         InlineKeyboardButton(text="📈 Analytics", callback_data="adm:analytics")],
        [InlineKeyboardButton(text="📜 Logs", callback_data="adm:logs"),
         InlineKeyboardButton(text="🟢 Health", callback_data="adm:health")],
    ])

def learning_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 AI Coach", callback_data="learn:learn"),
         InlineKeyboardButton(text="✨ Prompt Builder", callback_data="learn:build")],
        [InlineKeyboardButton(text="🔧 Improve", callback_data="learn:improve"),
         InlineKeyboardButton(text="🔍 Analyze", callback_data="learn:analyze")],
        [InlineKeyboardButton(text="📝 Post", callback_data="learn:post"),
         InlineKeyboardButton(text="🧠 Workflow", callback_data="learn:workflow")],
        [InlineKeyboardButton(text="📚 Lessons", callback_data="learn:lessons")],
    ])
