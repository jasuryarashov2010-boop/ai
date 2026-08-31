# AI Supporter Bot V300

Clean rebuild focused on reliability:
- Python 3.12.10 pinned to avoid pydantic-core source builds on Python 3.14.
- FastAPI webhook + aiogram 3.
- Explicit router registration so Telegram updates are handled.
- PostgreSQL via SQLAlchemy async.
- Redis only for FSM, cache and daily counters.
- ORM seed for plans/learning lessons, avoiding JSON raw-SQL and timestamp-default errors.
- Premium HTML/inline-keyboard UI.
- AI chat, voice, documents, vision, image generation.
- Support tickets, feedback, plans, referrals, required channels.
- Admin dashboard, users, plans, operators, channels, knowledge base, broadcast, analytics, logs and AI Learning Center.

## Render
Build:
python -m pip install --upgrade pip && python -m pip install -r requirements.txt

Start:
uvicorn app.main:app --host 0.0.0.0 --port $PORT

Required:
BOT_TOKEN, ADMIN_IDS, DATABASE_URL, REDIS_URL.
OPENAI_API_KEY is needed for AI features.

V300 is intended for a clean database. `create_all()` never deletes records, but it is not a full schema migration engine.
