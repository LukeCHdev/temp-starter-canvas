# Sous Chef Linguini - Product Requirements Document

## Original Problem Statement
Build a production-ready, community-driven recipe ecosystem with internationalization, authentication, ingredient scaling, and automatic image assignment.

## Architecture
- **Frontend**: React + React Router + Axios + Shadcn UI
- **Backend**: FastAPI + MongoDB (motor) + Pydantic
- **Auth**: HTTP-only cookie sessions (local + Emergent Google OAuth)
- **i18n**: Custom `t()` function + central `translations.js`
- **Images**: OpenAI `gpt-image-1` (lazy auto-assignment, stored as WebP)
- **Search**: Pure DB-only indexed regex search (no AI generation)

## Completed Phases

### Phase 1 Auth Finalization (DONE - Mar 2026)
- Login rate limiting, forgot/reset password (mocked), i18n audit, token leak fix
- 18/18 backend tests passed

### Phase 2 Favorites (DONE - Mar 2026)
- Full CRUD, unique index, FavoriteButton component, FavoritesPage
- 13/13 backend tests passed

### Phase 3 Comments/Reviews (DONE - Mar 2026)
- One review per user, rate limit 5/hr, XSS prevention, auth-gated
- 22/22 backend tests passed

### AI Image System (DONE - Mar 2026)
- 161 WebP images via gpt-image-1, lazy generation on first view
- Admin batch generation + single regeneration endpoints
- 21/21 backend tests passed

### Search Refactor to DB-Only (DONE - Mar 2026)
- Removed auto_generate/AI generation from search entirely
- Removed _find_similar_recipe() full memory load
- Removed thefuzz dependency from search flow
- New indexed regex search on recipe_name, origin_country, slug
- Input validation: min 2 chars, max 80 chars
- Rate limiting: 30 searches per 10 minutes per IP
- Regex injection fixed in all 3 search pathways
- Error messages sanitized (no internal leakage)
- Added 4 MongoDB indexes on recipes collection
- Frontend SearchBar updated for new array response format
- 22/22 backend tests + all frontend flows passed

### Techniques System (DONE - Mar 2026)
- New `techniques` MongoDB collection with schema: title, slug (unique), category, difficulty (enum), readTime, introduction, sections[], status, timestamps
- Indexes: slug_1 (unique), status_1, category_1
- Public endpoints: GET /api/techniques (published, newest first), GET /api/techniques/{slug}
- Admin endpoint: POST /api/admin/techniques (role=admin required, Pydantic validation)
- Validation: title 3-120 chars, difficulty enum, readTime > 0, sections min 1, slug URL-safe
- Slug auto-generation from title, duplicate prevention (409)
- 27/27 backend tests + all frontend flows passed

## Key DB Schema
- **users**: `{ id, username, email, password_hash, provider, provider_id, avatar_url, role, is_verified, created_at, last_login }`
- **recipe_reviews**: `{ id, user_id, recipe_slug, rating, comment, created_at, updated_at }` - Unique index on (user_id, recipe_slug)
- **recipes**: `{ ..., image_url, image_alt, image_source, custom_image_prompt }` - Indexes: status+slug, status+recipe_name, status+origin_country, status+avg_rating+ratings_count
- **techniques**: `{ title, slug (unique), category, difficulty, readTime, introduction, sections[{title, content}], status, created_at, updated_at }` - Indexes: slug_1 (unique), status_1, category_1
- **favorites**: `{ user_id, recipe_slug, created_at }` - Unique index on (user_id, recipe_slug)

### Techniques SEO & Production Readiness (DONE - Mar 2026)
- Techniques page fetches from static `/techniques.json` (20 techniques)
- JSON-LD HowTo @graph schema injected (20 items with steps)
- SEO meta tags: title, description, canonical all override correctly
- Sitemap includes `/techniques` for all 5 languages with hreflang
- robots.txt allows `/techniques`, no noindex meta
- Page is fully indexable
- All 6 SEO checks pass (title, description, canonical, JSON-LD, robots, content)

## Key Endpoints
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`
- `GET /api/auth/social/google`, `GET /api/auth/google/callback`, `GET /api/auth/me`
- `GET /api/recipes/search?q=&lang=&limit=` (DB-only, indexed, rate-limited)
- `POST/PUT/DELETE /api/recipes/{slug}/review` (Protected)
- `POST/DELETE /api/recipes/{slug}/favorite` (Protected)
- `GET /api/users/me/favorites` (Protected)
- `GET /api/techniques` (public, published only)
- `GET /api/techniques/{slug}` (public, published only)
- `POST /api/admin/techniques` (admin only, Pydantic validated)
- `POST /api/admin/images/generate-batch`, `GET /api/admin/images/status`

### Google Analytics (DONE - Mar 2026)
- Added Google Analytics gtag.js (G-8PR5RJL21H) to `public/index.html`
- Added AdSense meta tag `google-adsense-account` to `public/index.html`

### Mobile Layout Fix + elegant-sona Patterns + Scaling + React Query (DONE - Mar 2026)

**Files created:**
- `/app/frontend/src/hooks/useRecipe.js` — React Query hook for cached recipe fetching
- `/app/frontend/src/utils/ingredientScaler.js` — Safe ingredient amount parser (handles "380", "1/2", "1 1/2", "2-3", "to taste", "½")
- `/app/frontend/src/lib/queryClient.js` — React Query config (staleTime=10min)

**Files modified:**
- `frontend/src/index.js` — Added QueryClientProvider wrapper
- `frontend/src/pages/RecipePage.jsx` — Major mobile-first rewrite:
  - React Query integration (useRecipe hook, cached per [slug, lang])
  - Serving selector (+/- stepper, connected to POST /api/ai/scale)
  - Scaling error state with visual feedback
  - Mobile-first responsive: flex-col sm:flex-row for ingredients, touch-friendly buttons (h-9 w-9)
  - All text sizes responsive (text-sm sm:text-base, text-base sm:text-lg)
  - Hero title: text-2xl sm:text-4xl lg:text-5xl (was text-4xl sm:text-5xl lg:text-6xl)
  - Image aspect ratio: aspect-[4/3] sm:aspect-video
  - Error state with AlertTriangle icon for failed loads
  - break-words + min-w-0 on all text containers
- `frontend/src/components/recipe/RecipeCard.jsx` — Responsive image (h-40 sm:h-56), padding (p-4 sm:p-6), text sizes
- `frontend/src/components/common/Navigation.jsx` — Logo truncation fix (min-w-0 shrink), responsive icon sizes
- `frontend/src/components/common/FavoriteButton.jsx` — deferStatusCheck prop (prevents N+1 API calls on list pages)
- `frontend/src/i18n/translations.js` — Added scalingError, loadError, search.failed, explore.loadMore, explore.remaining keys
- 16/16 frontend tests passed (iteration_12)

### Search & Filter Deep Bug Fix (DONE - Mar 2026)
- **Root cause A**: FavoriteButton fired 161 concurrent API calls on explore page mount → Fixed: added `deferStatusCheck` prop, defers API call until user clicks
- **Root cause B**: `searchParams` mutation passed same object reference to `setSearchParams` → Fixed: cloned with `new URLSearchParams()`
- **Root cause C**: Sync effect only set dishTypes when URL param existed, didn't clear when param removed (browser back) → Fixed: unconditional state sync
- **Root cause D**: 161 recipe cards rendered simultaneously, choking mobile → Fixed: pagination with 24 cards + "Load More" button
- **Root cause E**: Search didn't include `dish_type` field → Fixed: added `dish_type` to text search
- **Secondary**: Added missing `search.failed`, `explore.loadMore`, `explore.remaining` translation keys
- 19/19 frontend tests passed (iteration_11)

### Search & Filter Bug Fix - Initial (DONE - Mar 2026)
- Added `dish_type` field to all 194 recipes via classification migration script (`backend/scripts/classify_dish_types.py`)
- Categories: appetizer (21), aperitif (6), first-course (45), main-course (65), side-dish (18), dessert (24), street-food (12), festive (3)
- Added search text input to ExplorePage for real-time client-side recipe filtering
- Fixed dish type filter (previously returned 0 results due to missing field)
- Fixed continent filter to work as client-side filter instead of navigating away
- Combined filtering: search + dish type + continent all work together
- Loads all published recipes (skip=0, limit=300) for complete client-side filtering
- Mobile: all filters work correctly (search, dish type dropdown, continent dropdown)
- Backend: added `skip` query parameter to `/api/recipes/featured` endpoint
- 13/13 frontend tests passed

## Mocked Flows
- Email verification and password reset (logged to console)

## Prioritized Backlog

### P0 - Blocked
- Bongo recipe image regeneration (BLOCKED: OpenAI billing limit reached)

### P1 - Upcoming
- Full Next.js migration for SEO and performance

### P2 - Future
- User profiles and collections
- Community verification badges
- Apple/Facebook social logins
- Real email service integration (SendGrid/Resend)
- AdSense integration
- PDF/ODF recipe import
- Moderation panel for reviews
- Reporting system for reviews
- Remove dead search infrastructure (routes/search.py LanguageSearchService, unused /api/search/* endpoints)
- Move rate limiters to Redis for multi-process scalability
