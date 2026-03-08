import React from 'react';
import { Link } from 'react-router-dom';
import { ChefHat } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

export const Footer = () => {
    const { language, getLocalizedPath } = useLanguage();

    return (
        <footer className="bg-foreground text-primary-foregroundforeground mt-20" data-testid="main-footer">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                    {/* Brand */}
                    <div className="col-span-1 md:col-span-2">
                        <div className="flex items-center space-x-2 mb-4">
                            <ChefHat className="h-6accent-[#CBA55B]" />
                            <span className="text-xl font-light tracking-tight" style={{ fontFamily: 'var(--font-heading)' }}>
                                Sous Chef Linguine
                            </span>
                        </div>
                        <p className="text-primary-foreground/70 text-sm max-w-md mb-4">
                            {t('footer.tagline', language)}
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="font-medium mb-4 text-accent text-sm uppercase tracking-wider">{t('footer.explore', language)}</h3>
                        <ul className="space-y-2 text-sm">
                            <li><Link to={getLocalizedPath('/')} className="hover:text-accent transition-colors">{t('common.home', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/explore')} className="hover:text-accent transition-colors">{t('footer.exploreRecipes', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/menu-builder')} className="hover:text-accent transition-colors">{t('nav.menuBuilder', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/techniques')} className="hover:text-accent transition-colors">{t('nav.techniques', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/about')} className="hover:text-accent transition-colors">{t('nav.about', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/contact')} className="hover:text-accent transition-colors">{t('nav.contact', language)}</Link></li>
                        </ul>
                    </div>

                    {/* Legal */}
                    <div>
                        <h3 className="font-medium mb-4 text-[#CBA55B] text-sm uppercase tracking-wider">{t('footer.legal', language)}</h3>
                        <ul className="space-y-2 text-sm">
                            <li><Link to={getLocalizedPath('/editorial-policy')} className="hover:text-[#CBA55B] transition-colors">{t('footer.editorial', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/privacy')} className="hover:text-[#CBA55B] transition-colors">{t('footer.privacy', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/terms')} className="hover:text-[#CBA55B] transition-colors">{t('footer.terms', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/cookies')} className="hover:text-[#CBA55B] transition-colors">{t('footer.cookies', language)}</Link></li>
                            <li><Link to={getLocalizedPath('/for-ai')} className="hover:text-[#CBA55B] transition-colors">{t('footer.forAI', language)}</Link></li>
                        </ul>
                    </div>
                </div>

                <div className="border-t border-[#FAF7F0]/20 mt-8 pt-8 text-center text-sm text-[#FAF7F0]/60">
                    <p>© {new Date().getFullYear()} {t('footer.copyright', language)}</p>
                </div>
            </div>
        </footer>
    );
};
