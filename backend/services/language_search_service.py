"""
Language-Aware Search Service
Provides multilingual search with language-specific text processing.
Uses MongoDB text indexes with custom language analyzers via Python.
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Language-specific stop words
STOP_WORDS = {
    'en': {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'whom', 'how', 'when', 'where', 'why'},
    'it': {'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'e', 'ed', 'o', 'ma', 'se', 'perché', 'come', 'quando', 'dove', 'chi', 'che', 'cosa', 'quale', 'quanto', 'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'sono', 'è', 'siamo', 'sei', 'essere', 'avere', 'ho', 'hai', 'ha', 'abbiamo', 'questo', 'questa', 'questi', 'queste', 'quello', 'quella'},
    'fr': {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'si', 'car', 'que', 'qui', 'quoi', 'dont', 'où', 'comment', 'quand', 'pourquoi', 'de', 'du', 'à', 'au', 'aux', 'en', 'dans', 'sur', 'sous', 'avec', 'pour', 'par', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'ce', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'est', 'sont', 'être', 'avoir'},
    'es': {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'si', 'porque', 'como', 'cuando', 'donde', 'quien', 'que', 'cual', 'cuanto', 'de', 'del', 'a', 'al', 'en', 'con', 'por', 'para', 'sin', 'sobre', 'entre', 'yo', 'tú', 'él', 'ella', 'nosotros', 'ustedes', 'ellos', 'ellas', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'mi', 'tu', 'su', 'nuestro', 'es', 'son', 'ser', 'estar', 'haber'},
    'de': {'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'einer', 'und', 'oder', 'aber', 'wenn', 'weil', 'wie', 'wann', 'wo', 'wer', 'was', 'welche', 'welcher', 'von', 'zu', 'bei', 'mit', 'nach', 'aus', 'für', 'über', 'unter', 'zwischen', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'sie', 'dieser', 'diese', 'dieses', 'jener', 'mein', 'dein', 'sein', 'ist', 'sind', 'sein', 'haben', 'werden'}
}

# Common cooking terms that should be preserved across languages
COOKING_TERMS = {
    'en': {'sauté', 'braise', 'julienne', 'blanch', 'deglaze', 'fold', 'whisk', 'simmer', 'poach', 'roast', 'grill', 'bake', 'fry', 'steam'},
    'it': {'soffriggere', 'brasare', 'sbollentare', 'sfumare', 'montare', 'sobbollire', 'affogare', 'arrostire', 'grigliare', 'cuocere', 'friggere', 'stufare'},
    'fr': {'sauter', 'braiser', 'blanchir', 'déglacer', 'incorporer', 'fouetter', 'mijoter', 'pocher', 'rôtir', 'griller', 'cuire', 'frire', 'étuver'},
    'es': {'saltear', 'brasear', 'blanquear', 'desglasar', 'incorporar', 'batir', 'hervir', 'escalfar', 'asar', 'hornear', 'freír', 'guisar'},
    'de': {'anbraten', 'schmoren', 'blanchieren', 'ablöschen', 'unterheben', 'schlagen', 'köcheln', 'pochieren', 'braten', 'grillen', 'backen', 'frittieren', 'dünsten'}
}


class LanguageSearchService:
    """Service for language-aware recipe search."""
    
    def __init__(self, db):
        self.db = db
        self._ensure_text_indexes()
    
    async def _ensure_text_indexes(self):
        """Ensure text indexes exist for search."""
        try:
            # Create text index on searchable fields
            await self.db.recipes.create_index([
                ("recipe_name", "text"),
                ("history_summary", "text"),
                ("characteristic_profile", "text"),
                ("origin_country", "text"),
                ("ingredients.item", "text")
            ], name="recipe_text_search", default_language="english")
            logger.info("Text index created/verified for recipes")
        except Exception as e:
            logger.warning(f"Text index creation skipped: {e}")
    
    def _normalize_text(self, text: str, lang: str = 'en') -> str:
        """Normalize text for search: lowercase, remove accents, remove stop words."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove stop words for the language
        stop_words = STOP_WORDS.get(lang, STOP_WORDS['en'])
        words = text.split()
        words = [w for w in words if w not in stop_words and len(w) > 1]
        
        return ' '.join(words)
    
    def _get_search_variants(self, query: str, lang: str) -> List[str]:
        """Generate search variants for fuzzy matching."""
        variants = [query]
        normalized = self._normalize_text(query, lang)
        if normalized != query:
            variants.append(normalized)
        
        # Add individual words for partial matching
        words = normalized.split()
        if len(words) > 1:
            variants.extend(words)
        
        return list(set(variants))
    
    async def search(
        self,
        query: str,
        lang: str = 'en',
        limit: int = 20,
        include_translations: bool = True
    ) -> Dict:
        """
        Search recipes with language awareness.
        
        Args:
            query: Search query
            lang: Target language for results
            limit: Maximum results
            include_translations: Whether to include translated content
        
        Returns:
            Dict with recipes and search metadata
        """
        results = []
        search_metadata = {
            "query": query,
            "lang": lang,
            "normalized_query": self._normalize_text(query, lang),
            "method": "language_aware"
        }
        
        try:
            # Step 1: Try MongoDB text search first
            text_results = await self._text_search(query, limit * 2)
            
            # Step 2: If target language is not English, also search translations
            if lang != 'en' and include_translations:
                translation_results = await self._search_translations(query, lang, limit)
                # Merge results, prioritizing translations
                text_results = self._merge_results(translation_results, text_results)
            
            # Step 3: Apply language-specific scoring
            scored_results = self._score_results(text_results, query, lang)
            
            # Step 4: Sort by score and limit
            scored_results.sort(key=lambda x: x['_search_score'], reverse=True)
            results = scored_results[:limit]
            
            # Step 5: If not enough results, try fuzzy search
            if len(results) < limit // 2:
                fuzzy_results = await self._fuzzy_search(query, lang, limit - len(results))
                results.extend(fuzzy_results)
                search_metadata["method"] = "fuzzy_fallback"
            
            search_metadata["total_found"] = len(results)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            search_metadata["error"] = str(e)
        
        return {
            "recipes": results,
            "metadata": search_metadata
        }
    
    async def _text_search(self, query: str, limit: int) -> List[Dict]:
        """Perform MongoDB text search."""
        try:
            cursor = self.db.recipes.find(
                {"$text": {"$search": query}, "status": "published"},
                {"score": {"$meta": "textScore"}, "_id": 0}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(limit)
        except Exception as e:
            logger.warning(f"Text search failed: {e}")
            return []
    
    async def _search_translations(self, query: str, lang: str, limit: int) -> List[Dict]:
        """Search in translated content."""
        try:
            # Search in translations collection
            translations = await self.db.translations.find({
                "lang": lang,
                "status": "ready",
                "$or": [
                    {"content.recipe_name": {"$regex": query, "$options": "i"}},
                    {"content.history_summary": {"$regex": query, "$options": "i"}},
                    {"content.characteristic_profile": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).limit(limit).to_list(limit)
            
            # Convert to recipe format
            results = []
            for trans in translations:
                recipe = await self.db.recipes.find_one(
                    {"slug": trans.get("slug")},
                    {"_id": 0}
                )
                if recipe:
                    # Merge translated content
                    recipe['_translated'] = True
                    recipe['_display_lang'] = lang
                    if trans.get('content'):
                        recipe.update(trans['content'])
                    results.append(recipe)
            
            return results
        except Exception as e:
            logger.warning(f"Translation search failed: {e}")
            return []
    
    async def _fuzzy_search(self, query: str, lang: str, limit: int) -> List[Dict]:
        """Fuzzy search using regex patterns."""
        try:
            normalized = self._normalize_text(query, lang)
            words = normalized.split()[:3]  # Limit to first 3 words
            
            if not words:
                return []
            
            # Build regex pattern for fuzzy matching
            patterns = []
            for word in words:
                if len(word) >= 3:
                    patterns.append({"recipe_name": {"$regex": word, "$options": "i"}})
                    patterns.append({"origin_country": {"$regex": word, "$options": "i"}})
            
            if not patterns:
                return []
            
            cursor = self.db.recipes.find(
                {"$or": patterns, "status": "published"},
                {"_id": 0}
            ).limit(limit)
            
            return await cursor.to_list(limit)
        except Exception as e:
            logger.warning(f"Fuzzy search failed: {e}")
            return []
    
    def _merge_results(self, primary: List[Dict], secondary: List[Dict]) -> List[Dict]:
        """Merge two result lists, avoiding duplicates."""
        seen_slugs = set()
        merged = []
        
        for recipe in primary:
            slug = recipe.get('slug')
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                merged.append(recipe)
        
        for recipe in secondary:
            slug = recipe.get('slug')
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                merged.append(recipe)
        
        return merged
    
    def _score_results(self, results: List[Dict], query: str, lang: str) -> List[Dict]:
        """Apply language-specific scoring to results."""
        query_normalized = self._normalize_text(query, lang)
        query_words = set(query_normalized.split())
        
        for recipe in results:
            score = recipe.get('score', 0)  # MongoDB text score
            
            # Boost for exact name match
            name = recipe.get('recipe_name', '').lower()
            if query.lower() in name:
                score += 10
            
            # Boost for translated content matching target language
            if recipe.get('_translated') and recipe.get('_display_lang') == lang:
                score += 5
            
            # Boost for matching cooking terms
            cooking_terms = COOKING_TERMS.get(lang, set())
            if any(term in query_normalized for term in cooking_terms):
                score += 3
            
            # Boost for country match
            country = recipe.get('origin_country', '').lower()
            if any(word in country for word in query_words):
                score += 2
            
            recipe['_search_score'] = score
        
        return results


# Singleton instance
_search_service = None

def get_search_service(db):
    """Get or create search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = LanguageSearchService(db)
    return _search_service
