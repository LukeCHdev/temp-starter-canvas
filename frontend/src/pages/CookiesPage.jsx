import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ChevronRight, Cookie } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const CookiesPage = () => {
    const { language } = useLanguage();
    
    const content = {
        whatAreCookies: {
            title: {
                en: 'What Are Cookies?',
                it: 'Cosa Sono i Cookie?',
                fr: 'Que Sont les Cookies ?',
                es: '¿Qué Son las Cookies?',
                de: 'Was Sind Cookies?'
            },
            text: {
                en: 'Cookies are small text files that are stored on your device when you visit a website. They are widely used to make websites work more efficiently and provide information to website owners.',
                it: 'I cookie sono piccoli file di testo che vengono memorizzati sul tuo dispositivo quando visiti un sito web. Sono ampiamente utilizzati per far funzionare i siti web in modo più efficiente e fornire informazioni ai proprietari dei siti.',
                fr: 'Les cookies sont de petits fichiers texte qui sont stockés sur votre appareil lorsque vous visitez un site web. Ils sont largement utilisés pour faire fonctionner les sites web plus efficacement et fournir des informations aux propriétaires de sites.',
                es: 'Las cookies son pequeños archivos de texto que se almacenan en su dispositivo cuando visita un sitio web. Se utilizan ampliamente para hacer que los sitios web funcionen de manera más eficiente y proporcionar información a los propietarios de sitios web.',
                de: 'Cookies sind kleine Textdateien, die auf Ihrem Gerät gespeichert werden, wenn Sie eine Website besuchen. Sie werden häufig verwendet, um Websites effizienter zu gestalten und den Website-Eigentümern Informationen zu liefern.'
            }
        },
        howWeUse: {
            title: {
                en: 'How We Use Cookies',
                it: 'Come Utilizziamo i Cookie',
                fr: 'Comment Nous Utilisons les Cookies',
                es: 'Cómo Usamos las Cookies',
                de: 'Wie Wir Cookies Verwenden'
            },
            intro: {
                en: 'Sous Chef Linguine uses cookies for the following purposes:',
                it: 'Sous Chef Linguine utilizza i cookie per i seguenti scopi:',
                fr: 'Sous Chef Linguine utilise des cookies aux fins suivantes :',
                es: 'Sous Chef Linguine utiliza cookies para los siguientes propósitos:',
                de: 'Sous Chef Linguine verwendet Cookies für folgende Zwecke:'
            },
            essential: {
                title: {
                    en: 'Essential Cookies',
                    it: 'Cookie Essenziali',
                    fr: 'Cookies Essentiels',
                    es: 'Cookies Esenciales',
                    de: 'Essentielle Cookies'
                },
                text: {
                    en: 'Required for the website to function. These include authentication cookies that keep you logged in and remember your preferences.',
                    it: 'Necessari per il funzionamento del sito web. Questi includono cookie di autenticazione che ti mantengono connesso e ricordano le tue preferenze.',
                    fr: 'Nécessaires au fonctionnement du site web. Ceux-ci incluent les cookies d\'authentification qui vous maintiennent connecté et mémorisent vos préférences.',
                    es: 'Necesarias para que el sitio web funcione. Estas incluyen cookies de autenticación que lo mantienen conectado y recuerdan sus preferencias.',
                    de: 'Erforderlich für das Funktionieren der Website. Dazu gehören Authentifizierungs-Cookies, die Sie eingeloggt halten und Ihre Einstellungen speichern.'
                }
            },
            preference: {
                title: {
                    en: 'Preference Cookies',
                    it: 'Cookie di Preferenza',
                    fr: 'Cookies de Préférence',
                    es: 'Cookies de Preferencia',
                    de: 'Präferenz-Cookies'
                },
                text: {
                    en: 'Remember your settings such as language preference, measurement units (metric/imperial), and display preferences.',
                    it: 'Ricordano le tue impostazioni come la preferenza della lingua, le unità di misura (metriche/imperiali) e le preferenze di visualizzazione.',
                    fr: 'Mémorisent vos paramètres tels que la préférence de langue, les unités de mesure (métriques/impériales) et les préférences d\'affichage.',
                    es: 'Recuerdan sus configuraciones como preferencia de idioma, unidades de medida (métricas/imperiales) y preferencias de visualización.',
                    de: 'Speichern Ihre Einstellungen wie Spracheinstellung, Maßeinheiten (metrisch/imperial) und Anzeigeeinstellungen.'
                }
            },
            analytics: {
                title: {
                    en: 'Analytics Cookies',
                    it: 'Cookie Analitici',
                    fr: 'Cookies Analytiques',
                    es: 'Cookies Analíticas',
                    de: 'Analyse-Cookies'
                },
                text: {
                    en: 'Help us understand how visitors use our website by collecting anonymous statistics about page visits, search queries, and navigation patterns.',
                    it: 'Ci aiutano a capire come i visitatori utilizzano il nostro sito web raccogliendo statistiche anonime su visite alle pagine, query di ricerca e modelli di navigazione.',
                    fr: 'Nous aident à comprendre comment les visiteurs utilisent notre site web en collectant des statistiques anonymes sur les visites de pages, les requêtes de recherche et les habitudes de navigation.',
                    es: 'Nos ayudan a entender cómo los visitantes usan nuestro sitio web al recopilar estadísticas anónimas sobre visitas a páginas, consultas de búsqueda y patrones de navegación.',
                    de: 'Helfen uns zu verstehen, wie Besucher unsere Website nutzen, indem sie anonyme Statistiken über Seitenbesuche, Suchanfragen und Navigationsmuster sammeln.'
                }
            }
        },
        cookiesWeUse: {
            title: {
                en: 'Cookies We Use',
                it: 'Cookie che Utilizziamo',
                fr: 'Cookies que Nous Utilisons',
                es: 'Cookies que Usamos',
                de: 'Cookies, die Wir Verwenden'
            },
            headers: {
                name: {
                    en: 'Cookie Name',
                    it: 'Nome Cookie',
                    fr: 'Nom du Cookie',
                    es: 'Nombre de Cookie',
                    de: 'Cookie-Name'
                },
                purpose: {
                    en: 'Purpose',
                    it: 'Scopo',
                    fr: 'But',
                    es: 'Propósito',
                    de: 'Zweck'
                },
                duration: {
                    en: 'Duration',
                    it: 'Durata',
                    fr: 'Durée',
                    es: 'Duración',
                    de: 'Dauer'
                }
            },
            cookies: [
                {
                    name: 'auth_token',
                    purpose: {
                        en: 'Authentication',
                        it: 'Autenticazione',
                        fr: 'Authentification',
                        es: 'Autenticación',
                        de: 'Authentifizierung'
                    },
                    duration: {
                        en: 'Session',
                        it: 'Sessione',
                        fr: 'Session',
                        es: 'Sesión',
                        de: 'Sitzung'
                    }
                },
                {
                    name: 'language',
                    purpose: {
                        en: 'Language preference',
                        it: 'Preferenza lingua',
                        fr: 'Préférence de langue',
                        es: 'Preferencia de idioma',
                        de: 'Spracheinstellung'
                    },
                    duration: {
                        en: '1 year',
                        it: '1 anno',
                        fr: '1 an',
                        es: '1 año',
                        de: '1 Jahr'
                    }
                },
                {
                    name: 'units',
                    purpose: {
                        en: 'Measurement units',
                        it: 'Unità di misura',
                        fr: 'Unités de mesure',
                        es: 'Unidades de medida',
                        de: 'Maßeinheiten'
                    },
                    duration: {
                        en: '1 year',
                        it: '1 anno',
                        fr: '1 an',
                        es: '1 año',
                        de: '1 Jahr'
                    }
                }
            ]
        },
        managing: {
            title: {
                en: 'Managing Cookies',
                it: 'Gestione dei Cookie',
                fr: 'Gestion des Cookies',
                es: 'Gestión de Cookies',
                de: 'Cookies Verwalten'
            },
            intro: {
                en: 'You can control and manage cookies in various ways:',
                it: 'Puoi controllare e gestire i cookie in vari modi:',
                fr: 'Vous pouvez contrôler et gérer les cookies de différentes manières :',
                es: 'Puede controlar y gestionar las cookies de varias maneras:',
                de: 'Sie können Cookies auf verschiedene Weise kontrollieren und verwalten:'
            },
            items: {
                en: ['Most browsers allow you to refuse or accept cookies', 'You can delete cookies that have already been set', 'You can set your browser to notify you when cookies are being set'],
                it: ['La maggior parte dei browser ti permette di rifiutare o accettare i cookie', 'Puoi eliminare i cookie già impostati', 'Puoi impostare il tuo browser per notificarti quando vengono impostati i cookie'],
                fr: ['La plupart des navigateurs vous permettent de refuser ou d\'accepter les cookies', 'Vous pouvez supprimer les cookies déjà définis', 'Vous pouvez configurer votre navigateur pour vous avertir lorsque des cookies sont définis'],
                es: ['La mayoría de los navegadores le permiten rechazar o aceptar cookies', 'Puede eliminar las cookies que ya se han establecido', 'Puede configurar su navegador para que le notifique cuando se establecen cookies'],
                de: ['Die meisten Browser erlauben es Ihnen, Cookies abzulehnen oder zu akzeptieren', 'Sie können bereits gesetzte Cookies löschen', 'Sie können Ihren Browser so einstellen, dass er Sie benachrichtigt, wenn Cookies gesetzt werden']
            },
            note: {
                en: 'Note: Disabling cookies may affect the functionality of our website, particularly features that require you to be logged in.',
                it: 'Nota: Disabilitare i cookie potrebbe influenzare la funzionalità del nostro sito web, in particolare le funzionalità che richiedono l\'accesso.',
                fr: 'Remarque : Désactiver les cookies peut affecter la fonctionnalité de notre site web, en particulier les fonctionnalités qui nécessitent que vous soyez connecté.',
                es: 'Nota: Deshabilitar las cookies puede afectar la funcionalidad de nuestro sitio web, particularmente las características que requieren que esté conectado.',
                de: 'Hinweis: Das Deaktivieren von Cookies kann die Funktionalität unserer Website beeinträchtigen, insbesondere Funktionen, die eine Anmeldung erfordern.'
            }
        },
        contact: {
            title: {
                en: 'Contact Us',
                it: 'Contattaci',
                fr: 'Contactez-Nous',
                es: 'Contáctenos',
                de: 'Kontaktieren Sie Uns'
            },
            text: {
                en: 'If you have questions about our use of cookies, please contact us through our',
                it: 'Se hai domande sull\'uso dei cookie, contattaci tramite la nostra',
                fr: 'Si vous avez des questions sur notre utilisation des cookies, veuillez nous contacter via notre',
                es: 'Si tiene preguntas sobre nuestro uso de cookies, contáctenos a través de nuestra',
                de: 'Wenn Sie Fragen zur Verwendung von Cookies haben, kontaktieren Sie uns bitte über unsere'
            },
            link: {
                en: 'Contact page',
                it: 'pagina Contatti',
                fr: 'page Contact',
                es: 'página de Contacto',
                de: 'Kontaktseite'
            }
        }
    };

    return (
        <div className="min-h-screen bg-[#FAF7F0]">
            {/* Header */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <nav className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-6">
                        <Link to="/" className="hover:text-[#6A1F2E] flex items-center gap-1">
                            <Home className="h-4 w-4" /> {t('common.home', language)}
                        </Link>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-[#6A1F2E] font-medium">{t('cookies.title', language)}</span>
                    </nav>
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E]" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('cookies.title', language)}
                    </h1>
                    <p className="text-[#1E1E1E]/70 mt-4">{t('cookies.lastUpdated', language)}</p>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-xl p-8 shadow-sm space-y-8">
                    
                    {/* What Are Cookies */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {content.whatAreCookies.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.whatAreCookies.text[language]}
                        </p>
                    </section>

                    {/* How We Use Cookies */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {content.howWeUse.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed mb-4">
                            {content.howWeUse.intro[language]}
                        </p>
                        
                        <div className="space-y-4">
                            <div className="bg-[#F5F2E8] rounded-lg p-4">
                                <h3 className="font-semibold text-[#1E1E1E] mb-2">{content.howWeUse.essential.title[language]}</h3>
                                <p className="text-[#1E1E1E]/70 text-sm">{content.howWeUse.essential.text[language]}</p>
                            </div>
                            
                            <div className="bg-[#F5F2E8] rounded-lg p-4">
                                <h3 className="font-semibold text-[#1E1E1E] mb-2">{content.howWeUse.preference.title[language]}</h3>
                                <p className="text-[#1E1E1E]/70 text-sm">{content.howWeUse.preference.text[language]}</p>
                            </div>
                            
                            <div className="bg-[#F5F2E8] rounded-lg p-4">
                                <h3 className="font-semibold text-[#1E1E1E] mb-2">{content.howWeUse.analytics.title[language]}</h3>
                                <p className="text-[#1E1E1E]/70 text-sm">{content.howWeUse.analytics.text[language]}</p>
                            </div>
                        </div>
                    </section>

                    {/* Cookies We Use */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {content.cookiesWeUse.title[language]}
                        </h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[#E5DCC3]">
                                        <th className="text-left py-3 px-4 font-semibold">{content.cookiesWeUse.headers.name[language]}</th>
                                        <th className="text-left py-3 px-4 font-semibold">{content.cookiesWeUse.headers.purpose[language]}</th>
                                        <th className="text-left py-3 px-4 font-semibold">{content.cookiesWeUse.headers.duration[language]}</th>
                                    </tr>
                                </thead>
                                <tbody className="text-[#1E1E1E]/70">
                                    {content.cookiesWeUse.cookies.map((cookie, i) => (
                                        <tr key={i} className="border-b border-[#E5DCC3]/50">
                                            <td className="py-3 px-4">{cookie.name}</td>
                                            <td className="py-3 px-4">{cookie.purpose[language]}</td>
                                            <td className="py-3 px-4">{cookie.duration[language]}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Managing Cookies */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {content.managing.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed mb-4">
                            {content.managing.intro[language]}
                        </p>
                        <ul className="list-disc pl-6 space-y-2 text-[#1E1E1E]/80">
                            {content.managing.items[language].map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                        <p className="text-[#1E1E1E]/70 text-sm mt-4 italic">
                            {content.managing.note[language]}
                        </p>
                    </section>

                    {/* Contact Us */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {content.contact.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.contact.text[language]} <Link to="/contact" className="text-[#6A1F2E] hover:underline">{content.contact.link[language]}</Link>.
                        </p>
                    </section>

                </div>
            </section>
        </div>
    );
};

export default CookiesPage;
