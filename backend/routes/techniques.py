"""Techniques routes — public + admin endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import Optional
import re
import logging

from models.technique import TechniqueCreate

logger = logging.getLogger(__name__)

techniques_router = APIRouter(prefix="/api", tags=["techniques"])

_db = None


def set_techniques_db(database):
    global _db
    _db = database


def _slugify(text: str) -> str:
    """Generate a URL-safe slug from text."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


# ─── Public endpoints ────────────────────────────────────────

@techniques_router.get("/techniques")
async def get_all_techniques():
    """Return all published techniques, newest first."""
    docs = await _db.techniques.find(
        {"status": "published"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return docs


@techniques_router.get("/techniques/{slug}")
async def get_technique(slug: str):
    """Return a single published technique by slug."""
    doc = await _db.techniques.find_one(
        {"slug": slug, "status": "published"},
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Technique not found")
    return doc


# ─── Admin endpoint ──────────────────────────────────────────

@techniques_router.post("/admin/techniques")
async def create_technique(body: TechniqueCreate, request: Request):
    """Create a new technique (admin only)."""
    from routes.auth import get_session_user

    user = await get_session_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    now = datetime.now(timezone.utc).isoformat()

    slug = body.slug or _slugify(body.title)

    # Ensure slug uniqueness
    existing = await _db.techniques.find_one({"slug": slug})
    if existing:
        raise HTTPException(status_code=409, detail="A technique with this slug already exists")

    doc = {
        "title": body.title,
        "slug": slug,
        "category": body.category,
        "difficulty": body.difficulty.value,
        "readTime": body.readTime,
        "introduction": body.introduction,
        "sections": [s.model_dump() for s in body.sections],
        "status": body.status or "draft",
        "created_at": now,
        "updated_at": now,
    }

    await _db.techniques.insert_one(doc)
    doc.pop("_id", None)

    logger.info(f"Technique created: {slug} (status={doc['status']})")
    return doc
