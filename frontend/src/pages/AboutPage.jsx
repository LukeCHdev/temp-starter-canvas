import React from 'react';
import { Link } from 'react-router-dom';
import { ChefHat, Home, ChevronRight, Shield, Archive, BookOpen, Globe, CheckCircle } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const AboutPage = () => {
    const { language } = useLanguage();

    return (
        <div className="min-h-screen bg-[#FAF7F0]" data-testid="about-page">
            {/* Header */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-6">
                        <Link to="/" className="hover:text-[#6A1F2E] flex items-center gap-1">
                            <Home className="h-4 w-4" /> {t('common.home', language)}
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-[#6A1F2E] font-medium">{t('nav.about', language)}</span>
                    </nav>
                    
                    <div className="text-center">
                        <ChefHat className="h-16 w-16 mx-auto text-[#6A1F2E] mb-6" />
                        <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('about.title', language)}
                        </h1>
                        <p className="text-lg text-[#1E1E1E]/70">
                            {t('about.subtitle', language)}
                        </p>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto mt-6"></div>
                    </div>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Our Mission */}
                <div className="bg-white rounded-xl p-8 shadow-sm mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <Archive className="h-6 w-6 text-[#6A1F2E]" />
                        <h2 className="text-2xl font-semibold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('about.mission.title', language)}
                        </h2>
                    </div>
                    <p className="text-[#1E1E1E]/80 leading-relaxed">
                        {t('about.mission.text', language)}
                    </p>
                </div>

                {/* What We Are */}
                <div className="bg-white rounded-xl p-8 shadow-sm mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <BookOpen className="h-6 w-6 text-[#6A1F2E]" />
                        <h2 className="text-2xl font-semibold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('about.whatWeAre.title', language)}
                        </h2>
                    </div>
                    <p className="text-[#1E1E1E]/80 leading-relaxed">
                        {t('about.whatWeAre.text', language)}
                    </p>
                </div>

                {/* The Authenticity Framework */}
                <div className="bg-white rounded-xl p-8 shadow-sm mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <Shield className="h-6 w-6 text-[#6A1F2E]" />
                        <h2 className="text-2xl font-semibold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('about.authenticity.title', language)}
                        </h2>
                    </div>
                    <p className="text-[#1E1E1E]/80 leading-relaxed mb-6">
                        {t('about.authenticity.intro', language)}
                    </p>

                    <div className="space-y-6">
                        {/* Level 1: Official */}
                        <div className="bg-[#F5F2E8] rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="w-8 h-8 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-bold text-sm">1</span>
                                <h3 className="text-lg font-semibold text-[#6A1F2E]">
                                    {t('about.authenticity.level1.title', language)}
                                </h3>
                            </div>
                            <p className="text-[#1E1E1E]/70 ml-10">
                                {t('about.authenticity.level1.text', language)}
                            </p>
                        </div>

                        {/* Level 2: Traditional */}
                        <div className="bg-[#F5F2E8] rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="w-8 h-8 rounded-full bg-[#3F4A3C] text-white flex items-center justify-center font-bold text-sm">2</span>
                                <h3 className="text-lg font-semibold text-[#3F4A3C]">
                                    {t('about.authenticity.level2.title', language)}
                                </h3>
                            </div>
                            <p className="text-[#1E1E1E]/70 ml-10">
                                {t('about.authenticity.level2.text', language)}
                            </p>
                        </div>

                        {/* Level 3: Regional Variation */}
                        <div className="bg-[#F5F2E8] rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="w-8 h-8 rounded-full bg-[#CBA55B] text-white flex items-center justify-center font-bold text-sm">3</span>
                                <h3 className="text-lg font-semibold text-[#CBA55B]">
                                    {t('about.authenticity.level3.title', language)}
                                </h3>
                            </div>
                            <p className="text-[#1E1E1E]/70 ml-10">
                                {t('about.authenticity.level3.text', language)}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Who is Sous Chef Linguine */}
                <div className="bg-white rounded-xl p-8 shadow-sm">
                    <div className="flex items-center gap-3 mb-4">
                        <ChefHat className="h-6 w-6 text-[#6A1F2E]" />
                        <h2 className="text-2xl font-semibold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('about.whoIs.title', language)}
                        </h2>
                    </div>
                    <p className="text-[#1E1E1E]/80 leading-relaxed">
                        {t('about.whoIs.text', language)}
                    </p>
                </div>

                {/* Link to Editorial Policy */}
                <div className="mt-12 text-center">
                    <Link 
                        to="/editorial-policy" 
                        className="inline-flex items-center gap-2 text-[#6A1F2E] hover:underline font-medium"
                    >
                        <CheckCircle className="h-5 w-5" />
                        {t('footer.editorial', language)}
                        <ChevronRight className="h-4 w-4" />
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default AboutPage;
