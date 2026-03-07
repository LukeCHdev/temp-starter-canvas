import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ChevronRight, Shield, FileCheck, Languages, Edit3, CheckCircle } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const EditorialPolicyPage = () => {
    const { language } = useLanguage();

    const principles = [
        {
            icon: Shield,
            titleKey: 'editorial.principles.principle1.title',
            textKey: 'editorial.principles.principle1.text',
            color: 'text-[#6A1F2E]',
            bgColor: 'bg-[#6A1F2E]/10'
        },
        {
            icon: FileCheck,
            titleKey: 'editorial.principles.principle2.title',
            textKey: 'editorial.principles.principle2.text',
            color: 'text-[#3F4A3C]',
            bgColor: 'bg-[#3F4A3C]/10'
        },
        {
            icon: CheckCircle,
            titleKey: 'editorial.principles.principle3.title',
            textKey: 'editorial.principles.principle3.text',
            color: 'text-[#CBA55B]',
            bgColor: 'bg-[#CBA55B]/10'
        },
        {
            icon: Edit3,
            titleKey: 'editorial.principles.principle4.title',
            textKey: 'editorial.principles.principle4.text',
            color: 'text-[#1E1E1E]',
            bgColor: 'bg-[#1E1E1E]/10'
        }
    ];

    return (
        <div className="min-h-screen bg-[#FAF7F0]" data-testid="editorial-policy-page">
            {/* Header */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-6">
                        <Link to="/" className="hover:text-[#6A1F2E] flex items-center gap-1">
                            <Home className="h-4 w-4" /> {t('common.home', language)}
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-[#6A1F2E] font-medium">{t('editorial.title', language)}</span>
                    </nav>
                    
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('editorial.title', language)}
                    </h1>
                    <p className="text-lg text-[#1E1E1E]/70">
                        {t('editorial.subtitle', language)}
                    </p>
                    <div className="w-24 h-1 bg-[#CBA55B] mt-6"></div>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Core Editorial Principles */}
                <div className="bg-white rounded-xl p-8 shadow-sm mb-8">
                    <h2 className="text-2xl font-bold text-[#6A1F2E] mb-6" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('editorial.principles.title', language)}
                    </h2>

                    <div className="space-y-6">
                        {principles.map((principle, index) => (
                            <div key={index} className={`${principle.bgColor} rounded-lg p-6`}>
                                <div className="flex items-center gap-3 mb-3">
                                    <principle.icon className={`h-6 w-6 ${principle.color}`} />
                                    <h3 className={`text-lg font-semibold ${principle.color}`}>
                                        {t(principle.titleKey, language)}
                                    </h3>
                                </div>
                                <p className="text-[#1E1E1E]/70 leading-relaxed">
                                    {t(principle.textKey, language)}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Translation Policy */}
                <div className="bg-white rounded-xl p-8 shadow-sm mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <Languages className="h-6 w-6 text-[#6A1F2E]" />
                        <h2 className="text-2xl font-bold text-[#6A1F2E]" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('editorial.translation.title', language)}
                        </h2>
                    </div>
                    <p className="text-[#1E1E1E]/80 leading-relaxed">
                        {t('editorial.translation.text', language)}
                    </p>
                </div>

                {/* Corrections and Updates */}
                <div className="bg-white rounded-xl p-8 shadow-sm">
                    <div className="flex items-center gap-3 mb-4">
                        <Edit3 className="h-6 w-6 text-[#6A1F2E]" />
                        <h2 className="text-2xl font-bold text-[#6A1F2E]" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('editorial.corrections.title', language)}
                        </h2>
                    </div>
                    <p className="text-[#1E1E1E]/80 leading-relaxed mb-4">
                        {t('editorial.corrections.text', language)}
                    </p>
                    <div className="bg-[#F5F2E8] rounded-lg p-4">
                        <p className="text-sm text-[#1E1E1E]/70">
                            <strong>{language === 'en' ? 'Contact:' : language === 'it' ? 'Contatto:' : language === 'fr' ? 'Contact:' : language === 'es' ? 'Contacto:' : 'Kontakt:'}</strong>{' '}
                            <a href="mailto:editorial@souscheflinguine.com" className="text-[#6A1F2E] hover:underline">
                                editorial@souscheflinguine.com
                            </a>
                        </p>
                    </div>
                </div>

                {/* Related Links */}
                <div className="mt-12 flex flex-wrap justify-center gap-4">
                    <Link 
                        to="/about" 
                        className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-[#1E1E1E]"
                    >
                        {t('nav.about', language)}
                        <ChevronRight className="h-4 w-4" />
                    </Link>
                    <Link 
                        to="/contact" 
                        className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-[#1E1E1E]"
                    >
                        {t('nav.contact', language)}
                        <ChevronRight className="h-4 w-4" />
                    </Link>
                    <Link 
                        to="/privacy" 
                        className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-[#1E1E1E]"
                    >
                        {t('footer.privacy', language)}
                        <ChevronRight className="h-4 w-4" />
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default EditorialPolicyPage;
