import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Recipe API
export const recipeAPI = {
    getAll: (params) => api.get('/recipes', { params }),
    getBySlug: (slug, lang = 'en') => api.get(`/recipes/${slug}`, { params: { lang } }),
    getByCountry: (country) => api.get(`/recipes/country/${country}`),
    getByRegion: (region) => api.get(`/recipes/region/${region}`),
    generate: (data) => api.post('/recipes/generate', data),
    search: (query, autoGenerate = true, lang = 'en') => api.get('/recipes/search', { 
        params: { q: query, auto_generate: autoGenerate, lang } 
    }),
    // Homepage & Explore
    getBest: () => api.get('/recipes/best'),
    getFeatured: (limit = 4) => api.get('/recipes/featured', { params: { limit } }),
    getTopWorldwide: (limit = 10) => api.get('/recipes/top-worldwide', { params: { limit } }),
    getByContinent: (continent, limit = 10) => api.get(`/recipes/by-continent/${continent}`, { params: { limit } }),
    getByCountryName: (country, limit = 50) => api.get(`/recipes/by-country/${country}`, { params: { limit } }),
    // Reviews & Ratings
    getReviews: (slug, limit = 50, offset = 0) => api.get(`/recipes/${slug}/reviews`, { params: { limit, offset } }),
    createReview: (slug, data) => api.post(`/recipes/${slug}/review`, data),
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
    build: (region) => api.post('/menu-builder', null, { params: { region } }),
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
