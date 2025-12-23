# Multilingual Architecture Audit & Implementation Plan
## Sous Chef Linguine - December 2025

---

## 📋 EXECUTIVE SUMMARY

This document provides a comprehensive technical audit of the current multilingual implementation and a prioritized action plan to achieve professional-grade multilingual architecture based on 2025 standards.

---

## 🔍 CURRENT STATE AUDIT

### 1. TECHNICAL STRUCTURE

| Component | Current State | Status |
|-----------|--------------|--------|
| URL-based language routing | ✅ Implemented (`/it/`, `/fr/`, `/en/`, `/de/`, `/es/`) | **GOOD** |
| Language context sync | ✅ Fixed - URL is single source of truth | **GOOD** |
| i18n state management | ✅ Synchronized with route via `LanguageContext.jsx` | **GOOD** |
| Navigation links | ✅ Fixed - All use `getLocalizedPath()` | **GOOD** |
| Recipe content translation | ⚠️ Partial - On-the-fly AI translation, not pre-translated | **NEEDS WORK** |
| Fallback UI indicators | ❌ Missing - No user notification when showing fallback content | **CRITICAL** |
| Search language filtering | ❌ Missing - Search always uses `lang='en'` hardcoded | **CRITICAL** |

### 2. MULTILINGUAL SEO

| Component | Current State | Status |
|-----------|--------------|--------|
| `<html lang="xx">` | ✅ Implemented via React Helmet | **GOOD** |
| `<link rel="alternate" hreflang>` | ✅ Implemented in `SEOHelmet.jsx` for all pages | **GOOD** |
| Localized meta titles | ✅ `HomeSEO` has translations for all 5 languages | **GOOD** |
| Localized meta descriptions | ✅ `HomeSEO` has translations for all 5 languages | **GOOD** |
| Canonical URLs | ✅ Language-prefixed canonicals implemented | **GOOD** |
| JSON-LD structured data | ✅ Recipe schema with `inLanguage` field | **GOOD** |
| Multilingual sitemap | ❌ Static, missing language URLs and recipe pages | **CRITICAL** |
| `index.html` hreflang | ⚠️ Static, not dynamically updated per route | **MINOR** |

### 3. INTERNAL SEARCH

| Component | Current State | Status |
|-----------|--------------|--------|
| Language-aware search | ❌ Hardcoded to `lang='en'` in `SearchBar.jsx` line 26 | **CRITICAL** |
| Filtered results | ❌ Returns mixed-language results | **CRITICAL** |
| Search backend | ⚠️ Supports `lang` param but not utilized correctly | **NEEDS WORK** |

---

## 🚨 IDENTIFIED ISSUES (Detailed Analysis)

### Issue 1: Recipe Pages Default to English Content
**Location:** `RecipePage.jsx` + Backend `/api/recipes/{slug}`

**Root Cause:** The backend performs on-the-fly AI translation when `lang` differs from `content_language`. However:
1. AI translation is slow and inconsistent
2. No caching mechanism for translations
3. If translation fails, English content is shown without notification

**Current Flow:**
```
User visits /fr/recipe/carbonara
  → Frontend calls: GET /api/recipes/carbonara?lang=fr
  → Backend checks: content_language='en', target='fr'
  → Backend calls AI translation (slow, may fail)
  → User sees: Either translated content OR English fallback
```

**Impact:** French users see English content with no indication it's a fallback.

---

### Issue 2: Search Ignores Active Language
**Location:** `/app/frontend/src/components/common/SearchBar.jsx` line 26

**Code:**
```javascript
const res = await recipeAPI.search(query, true, 'en'); // HARDCODED 'en'
```

**Impact:** 
- User on `/fr` searches "soupe" → Gets English results
- Creates confusion and poor UX
- SEO impact: Users leave site due to irrelevant results

---

### Issue 3: Static Sitemap Missing Multilingual URLs
**Location:** `/app/frontend/public/sitemap.xml`

**Current State:**
- Only 7 static URLs
- No language prefixes
- No recipe pages included
- No `xhtml:link` hreflang annotations

**Required:**
- Dynamic sitemap generation
- All 5 language versions of every URL
- All published recipe pages
- Proper hreflang annotations per Google guidelines

---

### Issue 4: No Fallback Content Indicators
**Location:** UI components

**Missing:**
- Visual indicator when showing fallback language
- Text like "This content is shown in English"
- Option to request translation

---

## 📊 PRIORITIZED ACTION PLAN

### 🔴 P0: CRITICAL (Immediate - Week 1)

#### P0.1: Fix Search Language Filtering
**Files:** `SearchBar.jsx`, `api.js`

**Changes:**
```javascript
// SearchBar.jsx - Use language from context
const { language, getLocalizedPath } = useLanguage();
const res = await recipeAPI.search(query, true, language);
```

**Backend Enhancement:**
- Add language filtering to search query
- Prioritize recipes with translations in requested language

**Acceptance:** Search on `/fr` returns French-prioritized results

---

#### P0.2: Add Fallback Content Indicators
**Files:** `RecipePage.jsx`, `TranslatedRecipeCard.jsx`, new `FallbackBanner.jsx`

**New Component:**
```jsx
const FallbackBanner = ({ originalLang, requestedLang }) => (
  <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mb-4">
    <p className="text-amber-800">
      {t('fallback.message', { lang: originalLang })}
    </p>
  </div>
);
```

**Integration:**
- Check `recipe._translated` or `recipe._display_lang` 
- Show banner if content language differs from URL language

**Acceptance:** Users see clear notification when viewing fallback content

---

#### P0.3: Recipe Content Language Alignment
**Files:** Backend translation routes, Recipe API

**Strategy:**
1. Use the existing async translation queue (`/api/translations/recipes`)
2. Pre-translate high-traffic recipes
3. Show translation status in UI:
   - `status: 'ready'` → Show translated content
   - `status: 'pending'` → Show fallback + "Translation in progress"
   - `status: 'failed'` → Show fallback + "Translation unavailable"

**Frontend Change:**
- Switch `RecipePage` to use `/api/translations/recipe/{slug}?lang=xx`
- Handle all three status states

**Acceptance:** Recipe pages correctly show translated content or clear fallback indicators

---

### 🟡 P1: HIGH PRIORITY (Week 2-3)

#### P1.1: Dynamic Multilingual Sitemap Generation
**Files:** New backend endpoint, build script

**Sitemap Structure:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://www.souscheflinguine.com/en/</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://...com/en/"/>
    <xhtml:link rel="alternate" hreflang="it" href="https://...com/it/"/>
    <xhtml:link rel="alternate" hreflang="fr" href="https://...com/fr/"/>
    <xhtml:link rel="alternate" hreflang="es" href="https://...com/es/"/>
    <xhtml:link rel="alternate" hreflang="de" href="https://...com/de/"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://...com/en/"/>
    <priority>1.0</priority>
  </url>
  <!-- Repeat for all pages and recipes -->
</urlset>
```

**Backend Endpoint:**
```python
@api_router.get("/sitemap.xml")
async def generate_sitemap():
    # Fetch all published recipes
    # Generate URLs for all 5 languages
    # Include hreflang annotations
```

**Acceptance:** `/api/sitemap.xml` returns complete multilingual sitemap

---

#### P1.2: Localized Meta Tags for All Pages
**Files:** `ExplorePage.jsx`, `AboutPage.jsx`, etc.

**Current Gap:** Only `HomeSEO` has full translations. Other pages use generic English.

**Implementation:**
- Add `PageSEO` or `ExploreSEO` to all pages
- Pass translated title/description based on current language
- Use i18n translation keys for consistency

---

#### P1.3: Pre-translate Popular Recipes
**Files:** Backend script, translation worker

**Strategy:**
1. Identify top 100 recipes by views/ratings
2. Queue all translations for all 5 languages
3. Run translation worker to process queue
4. Store translations in `recipe.translations` object

**Acceptance:** Top 100 recipes have translations ready in all languages

---

### 🟢 P2: SCALABILITY (Week 4+)

#### P2.1: Elasticsearch Integration for Multilingual Search
**Goal:** Language-specific analyzers and tokenizers

**Implementation:**
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "french_analyzer": { "type": "french" },
        "italian_analyzer": { "type": "italian" },
        "german_analyzer": { "type": "german" },
        "spanish_analyzer": { "type": "spanish" }
      }
    }
  }
}
```

**Benefits:**
- Stemming (cuire → cuit → cuisine)
- Stop words per language
- Accent folding
- Better relevance scoring

---

#### P2.2: Translation Memory System
**Goal:** Reuse translations for similar content

**Implementation:**
- Store translated phrases/sentences
- Match new content against memory
- Only translate new portions
- Reduce AI costs and improve consistency

---

#### P2.3: Regional Language Variants
**Goal:** Support `es-MX`, `fr-CA`, `pt-BR`, etc.

**Implementation:**
- Extended language codes in routing
- Regional vocabulary preferences
- Measurement unit localization (metric vs imperial)

---

## 📁 FILES TO MODIFY

### P0 Changes
| File | Change |
|------|--------|
| `/app/frontend/src/components/common/SearchBar.jsx` | Use `language` from context in search API call |
| `/app/frontend/src/pages/RecipePage.jsx` | Use translation API, add fallback banner |
| `/app/frontend/src/components/recipe/FallbackBanner.jsx` | **NEW** - Fallback notification component |
| `/app/frontend/src/i18n/translations.js` | Add `fallback.*` translation keys |

### P1 Changes
| File | Change |
|------|--------|
| `/app/backend/routes/sitemap.py` | **NEW** - Dynamic sitemap generation |
| `/app/backend/server.py` | Register sitemap route |
| `/app/frontend/src/pages/*.jsx` | Add appropriate SEO components |
| `/app/backend/scripts/pretranslate.py` | **NEW** - Batch translation script |

### P2 Changes
| File | Change |
|------|--------|
| `/app/backend/services/search_service.py` | **NEW** - Elasticsearch integration |
| `/app/backend/services/translation_memory.py` | **NEW** - Translation caching |

---

## ✅ ACCEPTANCE CRITERIA

### P0 Complete When:
- [ ] `/fr` search returns French-prioritized results
- [ ] Recipe pages show fallback banner when translation unavailable
- [ ] No mixed-language UI/content screens

### P1 Complete When:
- [ ] `/api/sitemap.xml` returns all URLs in all 5 languages
- [ ] All pages have localized meta titles/descriptions
- [ ] Top 100 recipes pre-translated

### P2 Complete When:
- [ ] Search uses language-specific analyzers
- [ ] Translation memory reduces AI calls by 50%+
- [ ] Regional variants supported

---

## 🔄 IMPLEMENTATION ORDER

```
Week 1: P0.1 → P0.2 → P0.3
Week 2: P1.1 → P1.2
Week 3: P1.3 → Testing
Week 4+: P2.1 → P2.2 → P2.3
```

---

## 📝 NOTES

1. **Existing Strengths:**
   - SEO components already well-implemented
   - Translation infrastructure exists (queue, worker)
   - Language context is robust

2. **Quick Wins:**
   - P0.1 (Search fix) is a 5-line change
   - P0.2 (Fallback banner) is a new small component

3. **Risk Areas:**
   - AI translation costs for P1.3
   - Sitemap size for large recipe catalogs

---

*Document created: December 2025*
*Author: E1 Development Agent*
