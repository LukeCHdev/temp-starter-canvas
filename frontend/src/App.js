import React from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
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

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppLayout>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/explore" element={<ExplorePage />} />
              <Route path="/explore/:continent" element={<ExplorePage />} />
              <Route path="/explore/:continent/:country" element={<ExplorePage />} />
              <Route path="/regions" element={<RegionsPage />} />
              <Route path="/country/:slug" element={<CountryPage />} />
              <Route path="/recipe/:slug" element={<RecipePage />} />
              <Route path="/menu-builder" element={<MenuBuilderPage />} />
              <Route path="/techniques" element={<TechniquesPage />} />
              <Route path="/favorites" element={<FavoritesPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/for-ai" element={<ForAIPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/cookies" element={<CookiesPage />} />
              
              {/* Admin Routes */}
              <Route path="/admin" element={<AdminLoginPage />} />
              <Route path="/admin/login" element={<AdminLoginPage />} />
              <Route path="/admin/recipes" element={<AdminRecipesPage />} />
              <Route path="/admin/recipes/new" element={<AdminNewRecipePage />} />
              <Route path="/admin/recipes/:slug/edit" element={<AdminEditRecipePage />} />
              <Route path="/admin/import-csv" element={<AdminImportCSVPage />} />
              <Route path="/admin/import-json" element={<AdminImportJSONPage />} />
              <Route path="/admin/import-scrape" element={<AdminScrapePage />} />
              <Route path="/admin/import-document" element={<AdminDocumentImportPage />} />
            </Routes>
          </AppLayout>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
