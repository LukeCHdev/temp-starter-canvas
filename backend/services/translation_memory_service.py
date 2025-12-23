"""
Translation Memory Service
Stores and retrieves sentence-level translations with fuzzy matching.
Prevents re-translation of already processed content.
"""

import re
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

# Minimum similarity for fuzzy matching (0.0 to 1.0)
FUZZY_THRESHOLD = 0.85

# Maximum entries to check for fuzzy matching (performance limit)
MAX_FUZZY_CANDIDATES = 100


class TranslationMemoryService:
    """
    Translation Memory (TM) service for storing and retrieving translations.
    
    Features:
    - Sentence-level storage
    - Fuzzy matching for similar content
    - Confidence/verified status tracking
    - Usage count for analytics
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.translation_memory
    
    async def ensure_indexes(self):
        """Create necessary indexes for efficient lookups."""
        try:
            # Compound index for exact lookups
            await self.collection.create_index([
                ("source_hash", 1),
                ("source_lang", 1),
                ("target_lang", 1)
            ], unique=True, name="tm_lookup_idx")
            
            # Index for fuzzy search candidates
            await self.collection.create_index([
                ("source_lang", 1),
                ("target_lang", 1),
                ("source_length", 1)
            ], name="tm_fuzzy_idx")
            
            # Index for analytics
            await self.collection.create_index([
                ("usage_count", -1)
            ], name="tm_usage_idx")
            
            logger.info("Translation memory indexes created")
        except Exception as e:
            logger.warning(f"Index creation skipped: {e}")
    
    def _compute_hash(self, text: str) -> str:
        """Compute hash for text lookup."""
        normalized = self._normalize_for_hash(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def _normalize_for_hash(self, text: str) -> str:
        """Normalize text for consistent hashing."""
        # Lowercase, collapse whitespace, strip
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity ratio between two texts."""
        return SequenceMatcher(None, 
                              self._normalize_for_hash(text1), 
                              self._normalize_for_hash(text2)).ratio()
    
    async def store(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        confidence: float = 1.0,
        verified: bool = False,
        context: Optional[str] = None,
        source_type: str = "ai"
    ) -> Dict:
        """
        Store a translation in memory.
        
        Args:
            source_text: Original text
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            confidence: Confidence score (0.0 to 1.0)
            verified: Whether human-verified
            context: Optional context (e.g., "recipe_name", "ingredient")
            source_type: "ai", "human", or "imported"
        
        Returns:
            Dict with storage result
        """
        source_hash = self._compute_hash(source_text)
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            # Upsert - update if exists, insert if new
            result = await self.collection.update_one(
                {
                    "source_hash": source_hash,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                },
                {
                    "$set": {
                        "translated_text": translated_text,
                        "confidence": confidence,
                        "verified": verified,
                        "updated_at": now
                    },
                    "$setOnInsert": {
                        "source_text": source_text,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "source_hash": source_hash,
                        "source_length": len(source_text),
                        "context": context,
                        "source_type": source_type,
                        "created_at": now,
                        "usage_count": 0
                    },
                    "$inc": {"usage_count": 1}
                },
                upsert=True
            )
            
            return {
                "success": True,
                "action": "updated" if result.matched_count > 0 else "inserted",
                "source_hash": source_hash
            }
        except Exception as e:
            logger.error(f"TM store error: {e}")
            return {"success": False, "error": str(e)}
    
    async def lookup(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        fuzzy: bool = True
    ) -> Optional[Dict]:
        """
        Look up a translation in memory.
        
        Args:
            source_text: Text to find translation for
            source_lang: Source language code
            target_lang: Target language code
            fuzzy: Whether to try fuzzy matching if exact not found
        
        Returns:
            Dict with translation or None
        """
        source_hash = self._compute_hash(source_text)
        
        # Step 1: Try exact match
        exact = await self.collection.find_one({
            "source_hash": source_hash,
            "source_lang": source_lang,
            "target_lang": target_lang
        })
        
        if exact:
            # Increment usage count
            await self.collection.update_one(
                {"_id": exact["_id"]},
                {"$inc": {"usage_count": 1}}
            )
            return {
                "translated_text": exact["translated_text"],
                "match_type": "exact",
                "confidence": exact.get("confidence", 1.0),
                "verified": exact.get("verified", False),
                "usage_count": exact.get("usage_count", 0) + 1
            }
        
        # Step 2: Try fuzzy match if enabled
        if fuzzy:
            fuzzy_result = await self._fuzzy_lookup(source_text, source_lang, target_lang)
            if fuzzy_result:
                return fuzzy_result
        
        return None
    
    async def _fuzzy_lookup(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[Dict]:
        """Find similar translation using fuzzy matching."""
        source_length = len(source_text)
        
        # Get candidates with similar length (±30%)
        min_length = int(source_length * 0.7)
        max_length = int(source_length * 1.3)
        
        candidates = await self.collection.find({
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source_length": {"$gte": min_length, "$lte": max_length}
        }).limit(MAX_FUZZY_CANDIDATES).to_list(MAX_FUZZY_CANDIDATES)
        
        best_match = None
        best_similarity = 0
        
        for candidate in candidates:
            similarity = self._compute_similarity(source_text, candidate["source_text"])
            if similarity >= FUZZY_THRESHOLD and similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate
        
        if best_match:
            # Increment usage count
            await self.collection.update_one(
                {"_id": best_match["_id"]},
                {"$inc": {"usage_count": 1}}
            )
            return {
                "translated_text": best_match["translated_text"],
                "match_type": "fuzzy",
                "similarity": best_similarity,
                "confidence": best_match.get("confidence", 1.0) * best_similarity,
                "verified": False,  # Fuzzy matches are not verified
                "original_source": best_match["source_text"],
                "usage_count": best_match.get("usage_count", 0) + 1
            }
        
        return None
    
    async def batch_lookup(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        fuzzy: bool = True
    ) -> Dict[str, Optional[Dict]]:
        """
        Look up multiple translations at once.
        
        Returns:
            Dict mapping source text to translation result (or None)
        """
        results = {}
        for text in texts:
            results[text] = await self.lookup(text, source_lang, target_lang, fuzzy)
        return results
    
    async def batch_store(
        self,
        translations: List[Dict],
        source_lang: str,
        target_lang: str,
        source_type: str = "ai"
    ) -> Dict:
        """
        Store multiple translations at once.
        
        Args:
            translations: List of {"source": str, "target": str, "context": str}
            source_lang: Source language code
            target_lang: Target language code
            source_type: Source type for all entries
        
        Returns:
            Dict with batch results
        """
        inserted = 0
        updated = 0
        errors = 0
        
        for trans in translations:
            result = await self.store(
                source_text=trans.get("source", ""),
                translated_text=trans.get("target", ""),
                source_lang=source_lang,
                target_lang=target_lang,
                context=trans.get("context"),
                source_type=source_type
            )
            
            if result.get("success"):
                if result.get("action") == "inserted":
                    inserted += 1
                else:
                    updated += 1
            else:
                errors += 1
        
        return {
            "total": len(translations),
            "inserted": inserted,
            "updated": updated,
            "errors": errors
        }
    
    async def get_stats(self) -> Dict:
        """Get translation memory statistics."""
        total = await self.collection.count_documents({})
        
        # By language pair
        pipeline = [
            {"$group": {
                "_id": {"source": "$source_lang", "target": "$target_lang"},
                "count": {"$sum": 1},
                "verified_count": {"$sum": {"$cond": ["$verified", 1, 0]}},
                "total_usage": {"$sum": "$usage_count"}
            }}
        ]
        
        lang_stats = await self.collection.aggregate(pipeline).to_list(100)
        
        # By source type
        type_pipeline = [
            {"$group": {
                "_id": "$source_type",
                "count": {"$sum": 1}
            }}
        ]
        
        type_stats = await self.collection.aggregate(type_pipeline).to_list(10)
        
        return {
            "total_entries": total,
            "by_language_pair": {
                f"{s['_id']['source']}->{s['_id']['target']}": {
                    "count": s["count"],
                    "verified": s["verified_count"],
                    "total_usage": s["total_usage"]
                } for s in lang_stats
            },
            "by_source_type": {s["_id"]: s["count"] for s in type_stats if s["_id"]}
        }
    
    async def export_for_language_pair(
        self,
        source_lang: str,
        target_lang: str,
        verified_only: bool = False
    ) -> List[Dict]:
        """Export translations for a language pair."""
        query = {
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        
        if verified_only:
            query["verified"] = True
        
        entries = await self.collection.find(
            query,
            {"_id": 0, "source_text": 1, "translated_text": 1, "context": 1, "verified": 1}
        ).to_list(10000)
        
        return entries


# Singleton instance
_tm_service = None

def get_translation_memory(db):
    """Get or create translation memory service instance."""
    global _tm_service
    if _tm_service is None:
        _tm_service = TranslationMemoryService(db)
    return _tm_service
