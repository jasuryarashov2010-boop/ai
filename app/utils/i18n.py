T = {
    "uz": {
        "home": "🏠 <b>AI Yordamchi</b>\n\nPremium AI + Support markaziga xush kelibsiz.",
        "choose": "🌐 <b>Tilni tanlang</b>",
        "subscribe": "📢 <b>Botdan foydalanish uchun majburiy kanallarga obuna bo‘ling.</b>",
        "blocked": "🚫 Akkountingiz vaqtincha bloklangan.",
        "limit": "⚠️ Ushbu funksiya uchun bugungi limit tugadi.",
    },
    "ru": {
        "home": "🏠 <b>AI Помощник</b>\n\nДобро пожаловать в центр AI + Support.",
        "choose": "🌐 <b>Выберите язык</b>",
        "subscribe": "📢 <b>Подпишитесь на обязательные каналы.</b>",
        "blocked": "🚫 Аккаунт временно заблокирован.",
        "limit": "⚠️ Дневной лимит этой функции исчерпан.",
    },
    "en": {
        "home": "🏠 <b>AI Assistant</b>\n\nWelcome to the AI + Support center.",
        "choose": "🌐 <b>Choose your language</b>",
        "subscribe": "📢 <b>Subscribe to the required channels.</b>",
        "blocked": "🚫 Your account is temporarily blocked.",
        "limit": "⚠️ Your daily limit for this feature is exhausted.",
    },
}
def tr(lang: str, key: str) -> str:
    return T.get(lang, T["uz"]).get(key, key)
