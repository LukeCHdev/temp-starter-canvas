import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
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

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-[#FAF7F0]" data-testid="app-container">
          <BrowserRouter>
            <Navigation />
            <main className="flex-1">
            <Routes>
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
            </Routes>
          </main>
          <Footer />
          <Toaster />
        </BrowserRouter>
      </div>
    </AuthProvider>
  </LanguageProvider>
  );
}

export default App;
