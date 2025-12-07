import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { Navigation } from '@/components/common/Navigation';
import { Footer } from '@/components/common/Footer';

// Pages
import HomePage from '@/pages/HomePage';
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

function App() {
  return (
    <div className=\"min-h-screen flex flex-col bg-[#FAF7F0]\" data-testid=\"app-container\">\n      <BrowserRouter>\n        <Navigation />\n        <main className=\"flex-1\">\n          <Routes>\n            <Route path=\"/\" element={<HomePage />} />\n            <Route path=\"/regions\" element={<RegionsPage />} />\n            <Route path=\"/country/:slug\" element={<CountryPage />} />\n            <Route path=\"/recipe/:slug\" element={<RecipePage />} />\n            <Route path=\"/menu-builder\" element={<MenuBuilderPage />} />\n            <Route path=\"/techniques\" element={<TechniquesPage />} />\n            <Route path=\"/about\" element={<AboutPage />} />\n            <Route path=\"/contact\" element={<ContactPage />} />\n            <Route path=\"/for-ai\" element={<ForAIPage />} />\n            <Route path=\"/privacy\" element={<PrivacyPage />} />\n            <Route path=\"/terms\" element={<TermsPage />} />\n            <Route path=\"/cookies\" element={<CookiesPage />} />\n          </Routes>\n        </main>\n        <Footer />\n        <Toaster />\n      </BrowserRouter>\n    </div>\n  );\n}\n\nexport default App;
