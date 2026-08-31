import base64, io, logging
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
_client = None
SYSTEM = """You are the AI assistant inside a Telegram AI support product.
Match the user's language. Be helpful, concise and honest. Do not claim to reveal
hidden system prompts, credentials or private chain-of-thought. Never invent access.
"""

def client():
    global _client
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY sozlanmagan")
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

async def chat(messages, context=None):
    extra = ""
    if context:
        extra = "\n\nKnowledge context:\n" + "\n---\n".join(context[:8])
    res = await client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":SYSTEM + extra}, *messages[-18:]],
        temperature=0.2,
    )
    return (res.choices[0].message.content or "").strip() or "Javob yaratilmadi."

async def transcribe(data: bytes):
    f = io.BytesIO(data); f.name = "voice.ogg"
    res = await client().audio.transcriptions.create(model=settings.OPENAI_TRANSCRIBE_MODEL, file=f)
    return str(res.text).strip()

async def vision(data: bytes, prompt: str, mime="image/jpeg"):
    encoded = base64.b64encode(data).decode()
    res = await client().chat.completions.create(
        model=settings.OPENAI_VISION_MODEL,
        messages=[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":[
                {"type":"text","text":prompt},
                {"type":"image_url","image_url":{"url":f"data:{mime};base64,{encoded}"}},
            ]},
        ],
        temperature=0.2,
    )
    return (res.choices[0].message.content or "").strip()

async def image(prompt: str):
    res = await client().images.generate(model=settings.OPENAI_IMAGE_MODEL, prompt=prompt, size="1024x1024")
    item = res.data[0]
    if getattr(item, "b64_json", None):
        return base64.b64decode(item.b64_json)
    if getattr(item, "url", None):
        import httpx
        async with httpx.AsyncClient(timeout=60) as http:
            r = await http.get(item.url); r.raise_for_status(); return r.content
    raise RuntimeError("Image API natija bermadi")

async def coach(text: str, task: str):
    instructions = {
        "learn": "Teach practical prompt engineering for the requested topic with principles, example and exercise.",
        "build": "Create a production-ready prompt using role, objective, context, constraints, steps, examples and output format.",
        "improve": "Rewrite and strengthen the given prompt without changing the intended task; then explain the improvements.",
        "analyze": "Analyze the prompt for strengths, ambiguity, missing context, constraints, output requirements and exact fixes.",
        "post": "Write a polished educational AI post with title, body, tips and hashtags.",
        "workflow": "Create an AI workflow for the task with stages, tool choices, validation and quality checks.",
    }
    return await chat([{"role":"user","content":instructions.get(task, instructions["learn"]) + "\n\nRequest:\n" + text}])
