import React from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { Navigation } from '@/components/common/Navigation';
import { Footer } from '@/components/common/Footer';
import { AuthProvider } from '@/context/AuthContext';
import { LanguageProvider } from '@/context/LanguageContext';

// Pages
import HomePage from '@/pages/HomePage';
import ExplorePage from '@/pages/ExplorePage';
import RegionsPage from '@/pages/RegionsPage';
import CountryPage from '@/pages/CountryPage';
import RecipePage from '@/pages/RecipePage';
import MenuBuilderPage from '@/pages/MenuBuilderPage';
import TechniquesPage from '@/pages/TechniquesPage';
import AboutPage from '@/pages/AboutPage';
import ContactPage from '@/pages/ContactPage';
import ForAIPage from '@/pages/ForAIPage';
import PrivacyPage from '@/pages/PrivacyPage';
import TermsPage from '@/pages/TermsPage';
import CookiesPage from '@/pages/CookiesPage';
import FavoritesPage from '@/pages/FavoritesPage';
import EditorialPolicyPage from '@/pages/EditorialPolicyPage';

// Admin Pages
import {
  AdminLoginPage,
  AdminRecipesPage,
  AdminNewRecipePage,
  AdminEditRecipePage,
  AdminImportCSVPage,
  AdminImportJSONPage,
  AdminScrapePage,
  AdminDocumentImportPage
} from '@/pages/admin';

// Layout wrapper that conditionally shows Navigation and Footer
const AppLayout = ({ children }) => {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');
  
  return (
    <div className={`min-h-screen flex flex-col ${isAdminRoute ? 'bg-gray-50' : 'bg-[#FAF7F0]'}`} data-testid="app-container">
      {!isAdminRoute && <Navigation />}
      <main className="flex-1">
        {children}
      </main>
      {!isAdminRoute && <Footer />}
      <Toaster />
    </div>
  );
};

// Public routes component - reused for each language prefix
const PublicRoutes = () => (
  <>
    <Route index element={<HomePage />} />
    <Route path="explore" element={<ExplorePage />} />
    <Route path="explore/:continent" element={<ExplorePage />} />
    <Route path="explore/:continent/:country" element={<ExplorePage />} />
    <Route path="regions" element={<RegionsPage />} />
    <Route path="country/:slug" element={<CountryPage />} />
    <Route path="recipe/:slug" element={<RecipePage />} />
    <Route path="menu-builder" element={<MenuBuilderPage />} />
    <Route path="techniques" element={<TechniquesPage />} />
    <Route path="favorites" element={<FavoritesPage />} />
    <Route path="about" element={<AboutPage />} />
    <Route path="contact" element={<ContactPage />} />
    <Route path="for-ai" element={<ForAIPage />} />
    <Route path="privacy" element={<PrivacyPage />} />
    <Route path="terms" element={<TermsPage />} />
    <Route path="cookies" element={<CookiesPage />} />
    <Route path="editorial-policy" element={<EditorialPolicyPage />} />
  </>
);

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <AppLayout>
            <Routes>
              {/* 
                Multilingual URL Structure:
                - / → Spanish (default)
                - /es/* → Spanish (explicit)
                - /en/* → English
                - /it/* → Italian
                - /fr/* → French
                - /de/* → German
              */}
              
              {/* Root routes (Spanish default) */}
              <Route path="/">
                {PublicRoutes()}
              </Route>
              
              {/* Spanish explicit prefix */}
              <Route path="/es">
                {PublicRoutes()}
              </Route>
              
              {/* English routes */}
              <Route path="/en">
                {PublicRoutes()}
              </Route>
              
              {/* Italian routes */}
              <Route path="/it">
                {PublicRoutes()}
              </Route>
              
              {/* French routes */}
              <Route path="/fr">
                {PublicRoutes()}
              </Route>
              
              {/* German routes */}
              <Route path="/de">
                {PublicRoutes()}
              </Route>
              
              {/* Admin Routes (no language prefix) */}
              <Route path="/admin" element={<AdminLoginPage />} />
              <Route path="/admin/login" element={<AdminLoginPage />} />
              <Route path="/admin/recipes" element={<AdminRecipesPage />} />
              <Route path="/admin/recipes/new" element={<AdminNewRecipePage />} />
              <Route path="/admin/recipes/:slug/edit" element={<AdminEditRecipePage />} />
              <Route path="/admin/import-csv" element={<AdminImportCSVPage />} />
              <Route path="/admin/import-json" element={<AdminImportJSONPage />} />
              <Route path="/admin/import-scrape" element={<AdminScrapePage />} />
              <Route path="/admin/import-document" element={<AdminDocumentImportPage />} />
              
              {/* Catch-all redirect to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AppLayout>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}

export default App;
