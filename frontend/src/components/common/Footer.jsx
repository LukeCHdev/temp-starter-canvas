import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

export const Footer = () => {
    const { language, getLocalizedPath } = useLanguage();

    return (
        <footer className="border-t border-border py-16 px-6" data-testid="main-footer">
            <div className="container mx-auto">
                <div className="grid md:grid-cols-3 gap-12">
                    {/* Brand */}
                    <div>
                        <h3 className="text-2xl font-semibold text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            SOUS CHEF <span className="text-primary">LINGUINE</span>
                        </h3>
                        <p className="text-sm text-muted-foreground leading-relaxed" style={{ fontFamily: 'var(--font-body)' }}>
                            {t('footer.tagline', language)}
                        </p>
                    </div>

                    {/* Explore */}
                    <div>
                        <h4 className="text-lg text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('footer.explore', language)}
                        </h4>
                        <div className="space-y-2">
                            {[
                                { path: '/', label: t('common.home', language) },
                                { path: '/explore', label: t('footer.exploreRecipes', language) },
                                { path: '/menu-builder', label: t('nav.menuBuilder', language) },
                                { path: '/techniques', label: t('nav.techniques', language) },
                                { path: '/about', label: t('nav.about', language) },
                                { path: '/contact', label: t('nav.contact', language) },
                            ].map((item) => (
                                <Link 
                                    key={item.path} 
                                    to={getLocalizedPath(item.path)} 
                                    className="block text-sm text-muted-foreground hover:text-primary transition-colors"
                                    style={{ fontFamily: 'var(--font-body)' }}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </div>
                    </div>

                    {/* Legal */}
                    <div>
                        <h4 className="text-lg text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('footer.legal', language)}
                        </h4>
                        <div className="space-y-2">
                            {[
                                { path: '/editorial-policy', label: t('footer.editorial', language) },
                                { path: '/privacy', label: t('footer.privacy', language) },
                                { path: '/terms', label: t('footer.terms', language) },
                                { path: '/cookies', label: t('footer.cookies', language) },
                                { path: '/for-ai', label: t('footer.forAI', language) },
                            ].map((item) => (
                                <Link 
                                    key={item.path} 
                                    to={getLocalizedPath(item.path)} 
                                    className="block text-sm text-muted-foreground hover:text-primary transition-colors"
                                    style={{ fontFamily: 'var(--font-body)' }}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="border-t border-border mt-12 pt-8 text-center">
                    <p className="text-xs text-muted-foreground" style={{ fontFamily: 'var(--font-body)' }}>
                        © {new Date().getFullYear()} {t('footer.copyright', language)}
                    </p>
                </div>
            </div>
        </footer>
    );
};
