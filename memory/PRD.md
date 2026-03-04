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

## Key DB Schema
- **users**: `{ id, username, email, password_hash, provider, provider_id, avatar_url, role, is_verified, created_at, last_login }`
- **recipe_reviews**: `{ id, user_id, recipe_slug, rating, comment, created_at, updated_at }` - Unique index on (user_id, recipe_slug)
- **recipes**: `{ ..., image_url, image_alt, image_source, custom_image_prompt }` - Indexes: status+slug, status+recipe_name, status+origin_country, status+avg_rating+ratings_count
- **favorites**: `{ user_id, recipe_slug, created_at }` - Unique index on (user_id, recipe_slug)

## Key Endpoints
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`
- `GET /api/auth/social/google`, `GET /api/auth/google/callback`, `GET /api/auth/me`
- `GET /api/recipes/search?q=&lang=&limit=` (DB-only, indexed, rate-limited)
- `POST/PUT/DELETE /api/recipes/{slug}/review` (Protected)
- `POST/DELETE /api/recipes/{slug}/favorite` (Protected)
- `GET /api/users/me/favorites` (Protected)
- `POST /api/admin/images/generate-batch`, `GET /api/admin/images/status`

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
