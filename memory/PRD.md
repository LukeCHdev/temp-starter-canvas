# Sous Chef Linguini - Product Requirements Document

## Original Problem Statement
Build a production-ready, community-driven recipe ecosystem with internationalization, authentication, ingredient scaling, and automatic image assignment.

## Architecture
- **Frontend**: React + React Router + Axios + Shadcn UI
- **Backend**: FastAPI + MongoDB (motor) + Pydantic
- **Auth**: HTTP-only cookie sessions (local + Emergent Google OAuth)
- **i18n**: Custom `t()` function + central `translations.js`
- **Images**: Unsplash API (lazy auto-assignment with multi-step fallback)

## What's Been Implemented

### Core Features (DONE)
- Systemic i18n architecture (EN/IT/FR/ES/DE) with translation key parity
- Recipe ingredient scaling (frontend + backend)
- Full authentication system (email/password + Google Social Login)
- Protected review/comment sections (auth-gated CRUD)
- CORS configuration for credentials
- Automatic image assignment via Unsplash with multi-step fallback

### Unsplash Image Rendering Fix (DONE - Mar 2026)
- **Root Cause 1**: `RecipeCard.jsx` only checked `photos[0].image_url`, not top-level `image_url` from Unsplash
- **Root Cause 2**: `RecipePage.jsx` had zero image rendering — no hero image section existed
- **Root Cause 3**: Translation API (`routes/translation.py`) omitted `image_url`/`image_alt`/`image_source`/`image_metadata` from metadata response
- **Root Cause 4**: `TranslatedRecipeCard.jsx` had the same photos-only bug as RecipeCard
- All 4 fixes applied. Tested: 14/14 backend + all frontend UI tests pass
- **Step 1**: Exact query `"{title} {country} food"`
- **Step 2**: Simplified title (geographic descriptors stripped) `"{main_dish} {country} food"`
- **Step 3**: Cuisine fallback `"{country} food"`
- Deduplicates queries, never crashes, never exposes API key
- Concurrency lock prevents duplicate fetches
- Tested: 21/21 tests pass (unit + integration)

## Prioritized Backlog

### P1 - Upcoming
- Full Next.js migration for SEO and performance

### P2 - Future
- User profiles, favorites, and collections
- Community verification badges
- Apple/Facebook social logins
- Real email service integration (SendGrid/Resend)
- AdSense integration
- PDF/ODF recipe import

## Key DB Schema
- **users**: `{ id, username, email, password_hash, provider, provider_id, avatar_url, role, is_verified, created_at, last_login }`
- **ratings**: `{ id, user_id, recipe_slug, rating, comment, created_at, updated_at }`
- **recipes**: `{ ..., photos, image_url, image_alt, image_source, image_metadata }`

## Key Endpoints
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`
- `GET /api/auth/social/google`, `GET /api/auth/google/callback`, `GET /api/auth/me`
- `POST/PUT/DELETE /api/recipes/{slug}/review` (Protected)
- `POST /api/recipes/scale`
- `GET /api/recipes/{slug}` (auto-assigns image via Unsplash fallback)

## Mocked Flows
- Email verification and password reset (logged to console)
