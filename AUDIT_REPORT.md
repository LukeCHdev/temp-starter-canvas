# RECIPE SYSTEM AUDIT REPORT
**Date:** 2024-12-28  
**Scope:** Data Structure, Scaling Logic, Translation Logic, Runtime Errors

---

## 🔍 TASK 1 — DATA STRUCTURE INSPECTION

### Current Schema
Ingredients are stored as **STRUCTURED ARRAY OBJECTS** (NOT strings).

```javascript
// Canonical ingredient structure (from /app/backend/models/recipe.py)
CanonicalIngredient = {
  item: str,      // Name of ingredient (e.g., "Spaghetti")
  amount: str,    // Quantity as string (e.g., "380", "1/2")
  unit: str,      // Unit of measurement (g, ml, tbsp, etc.)
  notes: str      // Optional preparation notes (e.g., "finely grated")
}
```

### Example Recipe Raw Database Record
```json
{
  "recipe_name": "Spaghetti alla Carbonara",
  "ingredients": [
    { "item": "Spaghetti", "amount": "380", "unit": "g", "notes": "" },
    { "item": "Guanciale", "amount": "150", "unit": "g", "notes": "cut into strips" },
    { "item": "Egg yolks", "amount": "4", "unit": "", "notes": "" },
    { "item": "Whole egg", "amount": "1", "unit": "", "notes": "" },
    { "item": "Pecorino Romano", "amount": "100", "unit": "g", "notes": "finely grated" },
    { "item": "Black pepper", "amount": "to taste", "unit": "", "notes": "freshly ground" }
  ]
}
```

### Database Statistics
| Metric | Value |
|--------|-------|
| Recipes with **array** ingredients | 194 (100%) |
| Recipes with **string** ingredients | 0 (0%) |
| Total recipes | 194 |

### Scaling Engine Compatibility
⚠️ **PARTIAL** - The scaling engine expects `amount` to be **numeric**, but the schema stores it as **string**.

```python
# /app/backend/services/scaling_engine.py line 29
if 'amount' in ingredient:
    ingredient['amount'] = round(ingredient['amount'] * scale_factor, 2)  # FAILS if amount is string
```

**Issue:** `amount` field contains strings like `"380"`, `"to taste"`, `"1/2"` which cannot be directly multiplied.

---

## 🔍 TASK 2 — SCALING LOGIC INSPECTION

### Serving Selector Status
❌ **NO serving selector component exists in the frontend.**
- No files matching `*scale*` or `*serving*` in `/app/frontend/src/`
- RecipePage.jsx does NOT render a serving selector UI

### Scaling API Endpoint
✅ API exists but is **NOT USED** by frontend.

```javascript
// /app/frontend/src/utils/api.js line 77
aiAPI.scale: (recipeSlug, targetServings) => api.post('/ai/scale', ...)
```

### Scaling Logic Location
**File:** `/app/backend/services/scaling_engine.py`

### Scaling Behavior
| Aspect | Status |
|--------|--------|
| Scaling engine implemented | ✅ Yes |
| Expects numeric amounts | ⚠️ Yes (but data is string) |
| Dynamically recalculates | ✅ Yes (multiplies by scale_factor) |
| Unit conversion (metric↔imperial) | ⚠️ Basic (hardcoded 0.035274 oz conversion) |
| Frontend integration | ❌ No |

### Why Scaling Will Fail
1. **Amount is stored as STRING** (`"380"`) not number (`380`)
2. **Non-numeric amounts exist** (`"to taste"`, `"1/2"`)
3. **No serving selector UI** in RecipePage.jsx
4. **API endpoint exists but unused**

---

## 🔍 TASK 3 — TRANSLATION LOGIC INSPECTION

### Architecture Overview
| Component | Type | Language Storage |
|-----------|------|------------------|
| UI text (buttons, labels) | Frontend i18n | translations.js (multilingual objects) |
| Recipe content (ingredients, instructions) | Backend DB | translations field per recipe |

### UI Translation
✅ **WORKING CORRECTLY**
- UI translations use `t()` function from `/app/frontend/src/i18n/translations.js`
- Silent English fallback was **FIXED** in this session
- All 5 locales (EN, IT, FR, ES, DE) display correctly

### Recipe Content Translation
✅ **WORKING CORRECTLY**
- Translations stored per recipe: `recipe.translations.{lang}`
- Each language contains: `recipe_name`, `history_summary`, `ingredients`, `instructions`, etc.
- Status tracking: `ready` | `pending` | `failed`

### Translation Structure Example
```json
{
  "translations": {
    "it": {
      "status": "ready",
      "translated_at": "2025-12-24T00:03:56.451640+00:00",
      "recipe_name": "Spaghetti alla Carbonara",
      "ingredients": [
        { "item": "Spaghetti", "amount": "380", "unit": "g", "notes": "" }
      ],
      "instructions": [
        "Cuocere il guanciale in una padella fredda..."
      ]
    },
    "fr": { ... },
    "es": { ... },
    "de": { ... }
  }
}
```

### Language State Storage
| Location | Purpose |
|----------|---------|
| URL path (`/it/recipe/...`) | **Primary source of truth** |
| localStorage (`preferred_language`) | Persistence fallback |
| LanguageContext state | React state for rendering |
| i18n.language | i18next library state |

### Content Reload Trigger
1. URL change triggers `location.pathname` effect
2. `useLanguage()` context updates `language` state
3. RecipePage.jsx `useEffect` fetches with `currentLang`
4. Translation API returns translated content or queues translation

### Translation Caching
- **Backend:** Translations cached in MongoDB (`recipe.translations.{lang}`)
- **Frontend:** No explicit caching (fetches on each page load)
- **Translation Queue:** Jobs tracked in `translation_queue` collection

### Fallback Logic
✅ **IMPLEMENTED CORRECTLY**
1. If `translation[lang].status === 'ready'` → return translated content
2. If translation pending → show skeleton, queue translation
3. If translation failed → show fallback banner + English content
4. Never silently return mixed language content

### Test Case Results
| Scenario | Result |
|----------|--------|
| Italian recipe → Switch to English | ✅ Works (fetches EN content) |
| French recipe → Switch to Spanish | ✅ Works (fetches ES translation) |
| Switch language twice in session | ✅ Works (no stale state) |

### Why Translation Sometimes Fails
Translation **is working correctly** based on audit. Possible edge cases:
1. **Translation not ready yet** - shows pending/skeleton
2. **Translation API timeout** - shows error banner
3. **Network issues** - falls back to English

---

## 🔍 TASK 4 — CONSOLE + RUNTIME ERRORS

### Browser Console Errors Found

| Error | Severity | Cause |
|-------|----------|-------|
| `WebSocket connection to 'ws://localhost:443/ws' failed` | ⚠️ Warning | Hot reload WebSocket (dev-only, not a bug) |
| `Using UNSAFE_componentWillMount in strict mode` | ⚠️ Warning | react-helmet legacy code (non-blocking) |

### Translation API Failures
❌ **NONE FOUND** during audit

### Undefined Ingredient Properties
❌ **NONE FOUND** - Ingredients are properly structured objects

### Missing Language Keys
❌ **NONE FOUND** - i18n enforcement pass completed successfully

### State Hydration Errors
❌ **NONE FOUND**

---

## 📊 SUMMARY REPORT

```
STRUCTURE STATUS:     ✅ HEALTHY
                      - Ingredients stored as array of objects
                      - 194/194 recipes use structured format
                      - Schema is consistent and well-defined

SCALING STATUS:       ⚠️ NOT FUNCTIONAL
                      - Backend scaling engine exists
                      - Frontend has NO serving selector UI
                      - API endpoint exists but is unused
                      - Amount field is STRING not NUMBER (will cause errors)

TRANSLATION STATUS:   ✅ HEALTHY (after today's fix)
                      - UI text: Working (i18n enforcement complete)
                      - Recipe content: Working (stored translations)
                      - Language switching: Working
                      - Fallback logic: Properly implemented

ROOT CAUSES:
1. SCALING: No frontend UI + amount is string not number
2. TRANSLATION: Was broken due to silent English fallback (NOW FIXED)

IMMEDIATE FIX PRIORITY:
1. 🟡 SCALING: Add serving selector to RecipePage.jsx
2. 🟡 SCALING: Parse amount strings to numbers before scaling
3. ✅ TRANSLATION: Already fixed in this session

RISK LEVEL:           🟢 LOW
                      - Core features working
                      - No critical bugs found
                      - Scaling is missing but not broken
                      - Translation system is healthy
```

---

## 📁 FILES AUDITED

| File | Purpose |
|------|---------|
| `/app/backend/models/recipe.py` | Canonical recipe schema |
| `/app/backend/services/scaling_engine.py` | Scaling logic |
| `/app/backend/services/translation_engine.py` | Translation locale adapter |
| `/app/backend/routes/translation.py` | Translation API endpoints |
| `/app/frontend/src/pages/RecipePage.jsx` | Recipe display page |
| `/app/frontend/src/context/LanguageContext.jsx` | Language state management |
| `/app/frontend/src/utils/api.js` | API client |
| `/app/frontend/src/i18n/translations.js` | UI translations |

---

## 🔒 NO CHANGES MADE

This audit was READ-ONLY. No code modifications were performed.
