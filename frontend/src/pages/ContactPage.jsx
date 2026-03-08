import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ChevronRight, Mail, BookOpen, Wrench, MessageSquare, Clock } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const ContactPage = () => {
    const { language, getLocalizedPath } = useLanguage();

    const contactSections = [
        {
            icon: BookOpen,
            titleKey: 'contact.editorial.title',
            textKey: 'contact.editorial.text',
            email: 'editorial@souscheflinguine.com',
            colorClass: 'bg-primary'
        },
        {
            icon: Mail,
            titleKey: 'contact.contributions.title',
            textKey: 'contact.contributions.text',
            email: 'contributions@souscheflinguine.com',
            colorClass: 'bg-secondary'
        },
        {
            icon: Wrench,
            titleKey: 'contact.technical.title',
            textKey: 'contact.technical.text',
            email: 'support@souscheflinguine.com',
            colorClass: 'bg-accent'
        },
        {
            icon: MessageSquare,
            titleKey: 'contact.general.title',
            textKey: 'contact.general.text',
            email: 'contact@souscheflinguine.com',
            colorClass: 'bg-foreground'
        }
    ];

    return (
        <div className="min-h-screen bg-background" data-testid="contact-page">
            {/* Header */}
            <section className="bg-gradient-to-b from-muted to-background py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
                        <Link to={getLocalizedPath('/')} className="hover:text-primary flex items-center gap-1">
                            <Home className="h-4 w-4" /> {t('common.home', language)}
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-primary font-medium">{t('nav.contact', language)}</span>
                    </nav>
                    
                    <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('contact.title', language)}
                    </h1>
                    <p className="text-lg text-muted-foreground">
                        {t('contact.subtitle', language)}
                    </p>
                    <div className="w-24 h-1 bg-accent mt-6"></div>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid md:grid-cols-2 gap-6">
                    {contactSections.map((section, index) => (
                        <div key={index} className="bg-card rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex items-start gap-4">
                                <div className={`${section.colorClass} p-3 rounded-full`}>
                                    <section.icon className="h-6 w-6 text-primary-foreground" />
                                </div>
                                <div className="flex-1">
                                    <h2 className="text-xl font-semibold text-foreground mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {t(section.titleKey, language)}
                                    </h2>
                                    <p className="text-muted-foreground text-sm mb-4">
                                        {t(section.textKey, language)}
                                    </p>
                                    <a 
                                        href={`mailto:${section.email}`}
                                        className="inline-flex items-center text-primary hover:underline font-medium text-sm"
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
                <div className="mt-10 bg-muted rounded-xl p-6 text-center">
                    <Clock className="h-8 w-8 mx-auto text-primary mb-3" />
                    <p className="text-foreground/80 font-medium">
                        {t('contact.responseTime', language)}
                    </p>
                </div>

                {/* Address / Additional Info */}
                <div className="mt-10 bg-card rounded-xl p-8 shadow-sm">
                    <h3 className="text-xl font-semibold text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        Sous Chef Linguine
                    </h3>
                    <p className="text-muted-foreground mb-6">
                        {t('contact.description', language)}
                    </p>
                    
                    <div className="border-t border-border pt-6">
                        <p className="text-sm text-muted-foreground">
                            <strong>Website:</strong> <a href="https://www.souscheflinguine.com" className="text-primary hover:underline">www.souscheflinguine.com</a>
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default ContactPage;
