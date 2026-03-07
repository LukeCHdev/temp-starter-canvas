import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ChevronRight, Mail, BookOpen, Wrench, MessageSquare, Clock } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const ContactPage = () => {
    const { language } = useLanguage();

    const contactSections = [
        {
            icon: BookOpen,
            titleKey: 'contact.editorial.title',
            textKey: 'contact.editorial.text',
            email: 'editorial@souscheflinguine.com',
            color: 'bg-[#6A1F2E]'
        },
        {
            icon: Mail,
            titleKey: 'contact.contributions.title',
            textKey: 'contact.contributions.text',
            email: 'contributions@souscheflinguine.com',
            color: 'bg-[#3F4A3C]'
        },
        {
            icon: Wrench,
            titleKey: 'contact.technical.title',
            textKey: 'contact.technical.text',
            email: 'support@souscheflinguine.com',
            color: 'bg-[#CBA55B]'
        },
        {
            icon: MessageSquare,
            titleKey: 'contact.general.title',
            textKey: 'contact.general.text',
            email: 'contact@souscheflinguine.com',
            color: 'bg-[#1E1E1E]'
        }
    ];

    return (
        <div className="min-h-screen bg-[#FAF7F0]" data-testid="contact-page">
            {/* Header */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-6">
                        <Link to="/" className="hover:text-[#6A1F2E] flex items-center gap-1">
                            <Home className="h-4 w-4" /> {t('common.home', language)}
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-[#6A1F2E] font-medium">{t('nav.contact', language)}</span>
                    </nav>
                    
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('contact.title', language)}
                    </h1>
                    <p className="text-lg text-[#1E1E1E]/70">
                        {t('contact.subtitle', language)}
                    </p>
                    <div className="w-24 h-1 bg-[#CBA55B] mt-6"></div>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid md:grid-cols-2 gap-6">
                    {contactSections.map((section, index) => (
                        <div key={index} className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex items-start gap-4">
                                <div className={`${section.color} p-3 rounded-full`}>
                                    <section.icon className="h-6 w-6 text-white" />
                                </div>
                                <div className="flex-1">
                                    <h2 className="text-xl font-semibold text-[#1E1E1E] mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {t(section.titleKey, language)}
                                    </h2>
                                    <p className="text-[#1E1E1E]/70 text-sm mb-4">
                                        {t(section.textKey, language)}
                                    </p>
                                    <a 
                                        href={`mailto:${section.email}`}
                                        className="inline-flex items-center text-[#6A1F2E] hover:underline font-medium text-sm"
                                    >
                                        <Mail className="h-4 w-4 mr-2" />
                                        {section.email}
                                    </a>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Response Time Notice */}
                <div className="mt-10 bg-[#F5F2E8] rounded-xl p-6 text-center">
                    <Clock className="h-8 w-8 mx-auto text-[#6A1F2E] mb-3" />
                    <p className="text-[#1E1E1E]/80 font-medium">
                        {t('contact.responseTime', language)}
                    </p>
                </div>

                {/* Address / Additional Info */}
                <div className="mt-10 bg-white rounded-xl p-8 shadow-sm">
                    <h3 className="text-xl font-semibold text-[#1E1E1E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        Sous Chef Linguine
                    </h3>
                    <p className="text-[#1E1E1E]/70 mb-6">
                        {language === 'en' 
                            ? 'Sous Chef Linguine is an online editorial platform dedicated to the preservation and documentation of authentic traditional recipes from around the world.'
                            : language === 'it'
                            ? 'Sous Chef Linguine è una piattaforma editoriale online dedicata alla conservazione e documentazione di ricette tradizionali autentiche da tutto il mondo.'
                            : language === 'fr'
                            ? 'Sous Chef Linguine est une plateforme éditoriale en ligne dédiée à la préservation et à la documentation de recettes traditionnelles authentiques du monde entier.'
                            : language === 'es'
                            ? 'Sous Chef Linguine es una plataforma editorial en línea dedicada a la preservación y documentación de recetas tradicionales auténticas de todo el mundo.'
                            : 'Sous Chef Linguine ist eine redaktionelle Online-Plattform, die der Bewahrung und Dokumentation authentischer traditioneller Rezepte aus aller Welt gewidmet ist.'
                        }
                    </p>
                    
                    <div className="border-t border-[#E5DCC3] pt-6">
                        <p className="text-sm text-[#1E1E1E]/60">
                            <strong>Website:</strong> <a href="https://www.souscheflinguine.com" className="text-[#6A1F2E] hover:underline">www.souscheflinguine.com</a>
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default ContactPage;
