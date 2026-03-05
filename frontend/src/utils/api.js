import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 60000,  // 60 second timeout for AI operations
    withCredentials: true,  // Important: Send cookies with requests
});

// Recipe API
export const recipeAPI = {
    getAll: (params) => api.get('/recipes', { params }),
    getBySlug: (slug, lang = 'en') => api.get(`/recipes/${slug}`, { params: { lang } }),
    getByCountry: (country) => api.get(`/recipes/country/${country}`),
    getByRegion: (region) => api.get(`/recipes/region/${region}`),
    generate: (data) => api.post('/recipes/generate', data),
    search: (query, lang = 'en', limit = 10) => api.get('/recipes/search', { 
        params: { q: query, lang, limit },
        timeout: 15000  // 15 second timeout for DB-only search
    }),
    // Homepage & Explore - with language support
    getBest: (lang = 'en') => api.get('/recipes/best', { params: { lang } }),
    getFeatured: (limit = 4, lang = 'en', skip = 1) => api.get('/recipes/featured', { params: { limit, lang, skip } }),
    getTopWorldwide: (limit = 10, lang = 'en') => api.get('/recipes/top-worldwide', { params: { limit, lang } }),
    getByContinent: (continent, limit = 10, lang = 'en') => api.get(`/recipes/by-continent/${continent}`, { params: { limit, lang } }),
    getByCountryName: (country, limit = 100, lang = 'en') => api.get(`/recipes/by-country/${country}`, { params: { limit, lang } }),
    // Reviews & Ratings
    getReviews: (slug, limit = 50, offset = 0) => api.get(`/recipes/${slug}/reviews`, { params: { limit, offset } }),
    createReview: (slug, data) => api.post(`/recipes/${slug}/review`, data),
    updateReview: (slug, data) => api.put(`/recipes/${slug}/review`, data),
    deleteReview: (slug) => api.delete(`/recipes/${slug}/review`),
};

// Auth API
export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    logout: () => api.post('/auth/logout'),
    me: () => api.get('/auth/me'),
    googleAuth: (sessionId) => api.post('/auth/social/google', { session_id: sessionId }),
    verifyEmail: (token) => api.post('/auth/verify-email', { token }),
    requestPasswordReset: (email) => api.post('/auth/reset-password', { email }),
    confirmPasswordReset: (data) => api.post('/auth/reset-password/confirm', data),
};

// Favorites API
export const favoritesAPI = {
    add: (slug) => api.post(`/recipes/${slug}/favorite`),
    remove: (slug) => api.delete(`/recipes/${slug}/favorite`),
    status: (slug) => api.get(`/recipes/${slug}/favorite-status`),
    myFavorites: () => api.get('/users/me/favorites'),
};

// Translation API - Language-aware recipe content
export const translationAPI = {
    // Get single recipe with translated content
    getRecipe: (slug, lang = 'en') => api.get(`/translations/recipe/${slug}`, { params: { lang } }),
    
    // Get recipes list with translated content
    getRecipes: (params) => api.get('/translations/recipes', { params }),
    
    // Queue translations for multiple recipes
    queueTranslations: (slugs, lang) => api.post('/translations/queue', slugs, { params: { lang } }),
    
    // Get queue status
    getQueueStatus: () => api.get('/translations/queue/status'),
};

// Continent API
export const continentAPI = {
    getAll: () => api.get('/continents'),
    getCountries: (continent) => api.get(`/continents/${continent}/countries`),
};

// Region API
export const regionAPI = {
    getAll: () => api.get('/regions'),
    getBySlug: (slug) => api.get(`/regions/${slug}`),
};

// Country API
export const countryAPI = {
    getAll: () => api.get('/countries'),
    getBySlug: (slug) => api.get(`/countries/${slug}`),
};

// Menu Builder API
export const menuAPI = {
    build: (country) => api.post('/menu-builder', null, { params: { country } }),
};

// AI Utilities API
export const aiAPI = {
    substitute: (data) => api.post('/ai/substitute', data),
    scale: (recipeSlug, targetServings) => api.post('/ai/scale', null, { params: { recipe_slug: recipeSlug, target_servings: targetServings } }),
};

// Locale API
export const localeAPI = {
    detect: (data) => api.post('/locale/detect', data),
};
