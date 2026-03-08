import React from 'react';
import { Link } from 'react-router-dom';
import { ChefHat, Home, ChevronRight, Shield, Archive, BookOpen, Globe, CheckCircle } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const AboutPage = () => {
    const { language, getLocalizedPath } = useLanguage();

    return (
        <div className="min-h-screen bg-background" data-testid="about-page">
            {/* Header */}
            <section className="bg-gradient-to-b from-muted to-background py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
                        <Link to={getLocalizedPath('/')} className="hover:text-primary flex items-center gap-1">
                            <Home className="h-4 w-4" /> {t('common.home', language)}
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-primary font-medium">{t('nav.about', language)}</span>
                    </nav>
                    
                    <div className="text-center">
                        <ChefHat className="h-12 w-12 sm:h-16 sm:w-16 mx-auto text-primary mb-6" />
                        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-light text-foreground mb-4 tracking-tight" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('about.title', language)}
                        </h1>
                        <p className="text-base sm:text-lg text-muted-foreground font-light">
                            {t('about.subtitle', language)}
                        </p>
                        <div className="section-divider-gold mt-6"></div>
                    </div>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Our Mission */}
                <div className="bg-card rounded-xl p-6 sm:p-8 shadow-sm mb-8 fade-in-up">
                    <div className="flex items-center gap-3 mb-4">
                        <Archive className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                        <h2 className="text-xl sm:text-2xl font-light text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('about.mission.title', language)}
                        </h2>
                    </div>
                    <p className="text-sm sm:text-base text-foreground/80 leading-relaxed font-light">
                        {t('about.mission.text', language)}
                    </p>
                </div>

                {/* What We Are */}
                <div className="bg-card rounded-xl p-6 sm:p-8 shadow-sm mb-8 fade-in-up fade-in-up-delay-1">
                    <div className="flex items-center gap-3 mb-4">
                        <BookOpen className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                        <h2 className="text-xl sm:text-2xl font-light text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('about.whatWeAre.title', language)}
                        </h2>
                    </div>
                    <p className="text-sm sm:text-base text-foreground/80 leading-relaxed font-light">
                        {t('about.whatWeAre.text', language)}
                    </p>
                </div>

                {/* The Authenticity Framework */}
                <div className="bg-card rounded-xl p-6 sm:p-8 shadow-sm mb-8 fade-in-up fade-in-up-delay-2">
                    <div className="flex items-center gap-3 mb-4">
                        <Shield className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                        <h2 className="text-xl sm:text-2xl font-light text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('about.authenticity.title', language)}
                        </h2>
                    </div>
                    <p className="text-sm sm:text-base text-foreground/80 leading-relaxed mb-6 font-light">
                        {t('about.authenticity.intro', language)}
                    </p>

                    <div className="space-y-6">
                        {/* Level 1: Official */}
                        <div className="bg-muted rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">1</span>
                                <h3 className="text-lg font-semibold text-primary">
                                    {t('about.authenticity.level1.title', language)}
                                </h3>
                            </div>
                            <p className="text-foreground/70 ml-10">
                                {t('about.authenticity.level1.text', language)}
                            </p>
                        </div>

                        {/* Level 2: Traditional */}
                        <div className="bg-muted rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center font-bold text-sm">2</span>
                                <h3 className="text-lg font-semibold text-secondary">
                                    {t('about.authenticity.level2.title', language)}
                                </h3>
                            </div>
                            <p className="text-foreground/70 ml-10">
                                {t('about.authenticity.level2.text', language)}
                            </p>
                        </div>

                        {/* Level 3: Regional Variation */}
                        <div className="bg-muted rounded-lg p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="w-8 h-8 rounded-full bg-accent text-accent-foreground flex items-center justify-center font-bold text-sm">3</span>
                                <h3 className="text-lg font-semibold text-accent">
                                    {t('about.authenticity.level3.title', language)}
                                </h3>
                            </div>
                            <p className="text-foreground/70 ml-10">
                                {t('about.authenticity.level3.text', language)}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Who is Sous Chef Linguine */}
                <div className="bg-card rounded-xl p-6 sm:p-8 shadow-sm fade-in-up fade-in-up-delay-3">
                    <div className="flex items-center gap-3 mb-4">
                        <ChefHat className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                        <h2 className="text-xl sm:text-2xl font-light text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('about.whoIs.title', language)}
                        </h2>
                    </div>
                    <p className="text-sm sm:text-base text-foreground/80 leading-relaxed font-light">
                        {t('about.whoIs.text', language)}
                    </p>
                </div>

                {/* Link to Editorial Policy */}
                <div className="mt-12 text-center">
                    <Link 
                        to={getLocalizedPath('/editorial-policy')}
                        className="inline-flex items-center gap-2 text-primary hover:underline font-medium"
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
