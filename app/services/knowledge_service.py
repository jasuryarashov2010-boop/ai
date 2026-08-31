from sqlalchemy import select
from app.db.models import KnowledgeItem
from app.db.session import SessionLocal

async def search(query, limit=8):
    async with SessionLocal() as s:
        rows = list((await s.scalars(
            select(KnowledgeItem).where(KnowledgeItem.active.is_(True)).order_by(KnowledgeItem.id.desc()).limit(100)
        )).all())
    terms = [x.lower() for x in query.split() if len(x) > 2]
    scored = []
    for item in rows:
        hay = f"{item.title} {item.content} {' '.join(item.tags)}".lower()
        scored.append((sum(t in hay for t in terms), item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:limit]]
