import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ChevronRight } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';

const PrivacyPage = () => {
    const { language } = useLanguage();
    
    // Translated content for all sections
    const content = {
        intro: {
            en: 'Sous Chef Linguine ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website and use our services.',
            it: 'Sous Chef Linguine ("noi", "nostro" o "ci") si impegna a proteggere la tua privacy. Questa Informativa sulla Privacy spiega come raccogliamo, utilizziamo, divulghiamo e proteggiamo le tue informazioni quando visiti il nostro sito web e utilizzi i nostri servizi.',
            fr: 'Sous Chef Linguine ("nous", "notre" ou "nos") s\'engage à protéger votre vie privée. Cette Politique de Confidentialité explique comment nous collectons, utilisons, divulguons et protégeons vos informations lorsque vous visitez notre site web et utilisez nos services.',
            es: 'Sous Chef Linguine ("nosotros", "nuestro" o "nos") se compromete a proteger su privacidad. Esta Política de Privacidad explica cómo recopilamos, usamos, divulgamos y protegemos su información cuando visita nuestro sitio web y utiliza nuestros servicios.',
            de: 'Sous Chef Linguine ("wir", "unser" oder "uns") verpflichtet sich, Ihre Privatsphäre zu schützen. Diese Datenschutzrichtlinie erklärt, wie wir Ihre Informationen sammeln, verwenden, offenlegen und schützen, wenn Sie unsere Website besuchen und unsere Dienste nutzen.'
        },
        sections: {
            infoCollect: {
                title: {
                    en: 'Information We Collect',
                    it: 'Informazioni che Raccogliamo',
                    fr: 'Informations que Nous Collectons',
                    es: 'Información que Recopilamos',
                    de: 'Informationen, die Wir Sammeln'
                },
                personal: {
                    title: {
                        en: 'Personal Information',
                        it: 'Informazioni Personali',
                        fr: 'Informations Personnelles',
                        es: 'Información Personal',
                        de: 'Persönliche Informationen'
                    },
                    items: {
                        en: ['Email address (when you create an account)', 'Password (securely hashed)', 'Saved recipes and favorites', 'Ratings and comments you submit'],
                        it: ['Indirizzo email (quando crei un account)', 'Password (crittografata in modo sicuro)', 'Ricette salvate e preferiti', 'Valutazioni e commenti che invii'],
                        fr: ['Adresse email (lors de la création d\'un compte)', 'Mot de passe (hashé de manière sécurisée)', 'Recettes sauvegardées et favoris', 'Notes et commentaires que vous soumettez'],
                        es: ['Dirección de correo electrónico (cuando creas una cuenta)', 'Contraseña (encriptada de forma segura)', 'Recetas guardadas y favoritos', 'Calificaciones y comentarios que envías'],
                        de: ['E-Mail-Adresse (bei Kontoerstellung)', 'Passwort (sicher verschlüsselt)', 'Gespeicherte Rezepte und Favoriten', 'Bewertungen und Kommentare, die Sie einreichen']
                    }
                },
                auto: {
                    title: {
                        en: 'Automatically Collected Information',
                        it: 'Informazioni Raccolte Automaticamente',
                        fr: 'Informations Collectées Automatiquement',
                        es: 'Información Recopilada Automáticamente',
                        de: 'Automatisch Gesammelte Informationen'
                    },
                    items: {
                        en: ['Browser type and version', 'Device information', 'IP address', 'Pages visited and time spent', 'Search queries'],
                        it: ['Tipo e versione del browser', 'Informazioni sul dispositivo', 'Indirizzo IP', 'Pagine visitate e tempo trascorso', 'Query di ricerca'],
                        fr: ['Type et version du navigateur', 'Informations sur l\'appareil', 'Adresse IP', 'Pages visitées et temps passé', 'Requêtes de recherche'],
                        es: ['Tipo y versión del navegador', 'Información del dispositivo', 'Dirección IP', 'Páginas visitadas y tiempo pasado', 'Consultas de búsqueda'],
                        de: ['Browsertyp und -version', 'Geräteinformationen', 'IP-Adresse', 'Besuchte Seiten und verbrachte Zeit', 'Suchanfragen']
                    }
                }
            },
            howWeUse: {
                title: {
                    en: 'How We Use Your Information',
                    it: 'Come Utilizziamo le Tue Informazioni',
                    fr: 'Comment Nous Utilisons Vos Informations',
                    es: 'Cómo Usamos Su Información',
                    de: 'Wie Wir Ihre Informationen Verwenden'
                },
                items: {
                    en: ['To provide and maintain our service', 'To personalize your experience', 'To save your favorite recipes', 'To improve our recipe recommendations', 'To analyze usage patterns and improve our platform', 'To communicate with you about updates and changes'],
                    it: ['Per fornire e mantenere il nostro servizio', 'Per personalizzare la tua esperienza', 'Per salvare le tue ricette preferite', 'Per migliorare i nostri consigli sulle ricette', 'Per analizzare i modelli di utilizzo e migliorare la nostra piattaforma', 'Per comunicare con te riguardo aggiornamenti e modifiche'],
                    fr: ['Pour fournir et maintenir notre service', 'Pour personnaliser votre expérience', 'Pour sauvegarder vos recettes favorites', 'Pour améliorer nos recommandations de recettes', 'Pour analyser les habitudes d\'utilisation et améliorer notre plateforme', 'Pour communiquer avec vous concernant les mises à jour et changements'],
                    es: ['Para proporcionar y mantener nuestro servicio', 'Para personalizar su experiencia', 'Para guardar sus recetas favoritas', 'Para mejorar nuestras recomendaciones de recetas', 'Para analizar patrones de uso y mejorar nuestra plataforma', 'Para comunicarnos con usted sobre actualizaciones y cambios'],
                    de: ['Um unseren Service bereitzustellen und zu pflegen', 'Um Ihre Erfahrung zu personalisieren', 'Um Ihre Lieblingsrezepte zu speichern', 'Um unsere Rezeptempfehlungen zu verbessern', 'Um Nutzungsmuster zu analysieren und unsere Plattform zu verbessern', 'Um mit Ihnen über Updates und Änderungen zu kommunizieren']
                }
            },
            ai: {
                title: {
                    en: 'AI-Generated Content',
                    it: 'Contenuti Generati dall\'IA',
                    fr: 'Contenu Généré par l\'IA',
                    es: 'Contenido Generado por IA',
                    de: 'KI-Generierte Inhalte'
                },
                text: {
                    en: 'Some recipes on our platform are generated by Sous-Chef Linguine AI. This AI system uses traditional authenticity ranking and validation to ensure recipe quality. Your search queries may be processed by AI systems to generate new recipes on demand. We do not use your personal information to train AI models.',
                    it: 'Alcune ricette sulla nostra piattaforma sono generate dall\'IA Sous-Chef Linguine. Questo sistema IA utilizza classificazione e validazione dell\'autenticità tradizionale per garantire la qualità delle ricette. Le tue query di ricerca potrebbero essere elaborate da sistemi IA per generare nuove ricette su richiesta. Non utilizziamo le tue informazioni personali per addestrare modelli IA.',
                    fr: 'Certaines recettes sur notre plateforme sont générées par l\'IA Sous-Chef Linguine. Ce système IA utilise un classement et une validation d\'authenticité traditionnels pour garantir la qualité des recettes. Vos requêtes de recherche peuvent être traitées par des systèmes IA pour générer de nouvelles recettes à la demande. Nous n\'utilisons pas vos informations personnelles pour entraîner des modèles IA.',
                    es: 'Algunas recetas en nuestra plataforma son generadas por la IA Sous-Chef Linguine. Este sistema de IA utiliza clasificación y validación de autenticidad tradicional para garantizar la calidad de las recetas. Sus consultas de búsqueda pueden ser procesadas por sistemas de IA para generar nuevas recetas bajo demanda. No utilizamos su información personal para entrenar modelos de IA.',
                    de: 'Einige Rezepte auf unserer Plattform werden von der Sous-Chef Linguine KI generiert. Dieses KI-System verwendet traditionelle Authentizitätsbewertung und -validierung, um die Rezeptqualität sicherzustellen. Ihre Suchanfragen können von KI-Systemen verarbeitet werden, um neue Rezepte auf Anfrage zu generieren. Wir verwenden Ihre persönlichen Daten nicht zum Trainieren von KI-Modellen.'
                }
            },
            sharing: {
                title: {
                    en: 'Data Sharing',
                    it: 'Condivisione dei Dati',
                    fr: 'Partage des Données',
                    es: 'Compartir Datos',
                    de: 'Datenweitergabe'
                },
                text: {
                    en: 'We do not sell your personal information. We may share anonymized, aggregated data for analytics purposes. Recipe ratings and comments may be publicly visible with your username.',
                    it: 'Non vendiamo le tue informazioni personali. Potremmo condividere dati anonimi e aggregati per scopi analitici. Le valutazioni e i commenti delle ricette potrebbero essere pubblicamente visibili con il tuo nome utente.',
                    fr: 'Nous ne vendons pas vos informations personnelles. Nous pouvons partager des données anonymisées et agrégées à des fins d\'analyse. Les notes et commentaires des recettes peuvent être publiquement visibles avec votre nom d\'utilisateur.',
                    es: 'No vendemos su información personal. Podemos compartir datos anónimos y agregados con fines analíticos. Las calificaciones y comentarios de recetas pueden ser públicamente visibles con su nombre de usuario.',
                    de: 'Wir verkaufen Ihre persönlichen Daten nicht. Wir können anonymisierte, aggregierte Daten für Analysezwecke teilen. Rezeptbewertungen und Kommentare können mit Ihrem Benutzernamen öffentlich sichtbar sein.'
                }
            },
            gdpr: {
                title: {
                    en: 'Your Rights (GDPR)',
                    it: 'I Tuoi Diritti (GDPR)',
                    fr: 'Vos Droits (RGPD)',
                    es: 'Sus Derechos (RGPD)',
                    de: 'Ihre Rechte (DSGVO)'
                },
                intro: {
                    en: 'If you are a resident of the European Economic Area (EEA), you have the following rights:',
                    it: 'Se sei residente nello Spazio Economico Europeo (SEE), hai i seguenti diritti:',
                    fr: 'Si vous êtes résident de l\'Espace Économique Européen (EEE), vous avez les droits suivants :',
                    es: 'Si es residente del Espacio Económico Europeo (EEE), tiene los siguientes derechos:',
                    de: 'Wenn Sie im Europäischen Wirtschaftsraum (EWR) ansässig sind, haben Sie folgende Rechte:'
                }
            },
            security: {
                title: {
                    en: 'Data Security',
                    it: 'Sicurezza dei Dati',
                    fr: 'Sécurité des Données',
                    es: 'Seguridad de Datos',
                    de: 'Datensicherheit'
                },
                text: {
                    en: 'We implement appropriate technical and organizational security measures to protect your personal information, including encryption of passwords and secure HTTPS connections.',
                    it: 'Implementiamo misure di sicurezza tecniche e organizzative appropriate per proteggere le tue informazioni personali, inclusa la crittografia delle password e connessioni HTTPS sicure.',
                    fr: 'Nous mettons en œuvre des mesures de sécurité techniques et organisationnelles appropriées pour protéger vos informations personnelles, y compris le chiffrement des mots de passe et des connexions HTTPS sécurisées.',
                    es: 'Implementamos medidas de seguridad técnicas y organizativas apropiadas para proteger su información personal, incluyendo el cifrado de contraseñas y conexiones HTTPS seguras.',
                    de: 'Wir setzen angemessene technische und organisatorische Sicherheitsmaßnahmen um, um Ihre persönlichen Daten zu schützen, einschließlich der Verschlüsselung von Passwörtern und sicherer HTTPS-Verbindungen.'
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
                    en: 'If you have questions about this Privacy Policy, please contact us through our',
                    it: 'Se hai domande su questa Informativa sulla Privacy, contattaci tramite la nostra',
                    fr: 'Si vous avez des questions sur cette Politique de Confidentialité, veuillez nous contacter via notre',
                    es: 'Si tiene preguntas sobre esta Política de Privacidad, por favor contáctenos a través de nuestra',
                    de: 'Wenn Sie Fragen zu dieser Datenschutzrichtlinie haben, kontaktieren Sie uns bitte über unsere'
                },
                link: {
                    en: 'Contact page',
                    it: 'pagina Contatti',
                    fr: 'page Contact',
                    es: 'página de Contacto',
                    de: 'Kontaktseite'
                }
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
                        <span className="text-[#6A1F2E] font-medium">{t('privacy.title', language)}</span>
                    </nav>
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E]" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('privacy.title', language)}
                    </h1>
                    <p className="text-[#1E1E1E]/70 mt-4">{t('privacy.lastUpdated', language)}</p>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-xl p-8 shadow-sm space-y-8">
                    
                    {/* Introduction */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            1. {language === 'en' ? 'Introduction' : language === 'it' ? 'Introduzione' : language === 'fr' ? 'Introduction' : language === 'es' ? 'Introducción' : 'Einführung'}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.intro[language]}
                        </p>
                    </section>

                    {/* Information We Collect */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            2. {content.sections.infoCollect.title[language]}
                        </h2>
                        <h3 className="text-lg font-semibold mt-4 mb-2">{content.sections.infoCollect.personal.title[language]}</h3>
                        <ul className="list-disc pl-6 space-y-2 text-[#1E1E1E]/80">
                            {content.sections.infoCollect.personal.items[language].map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                        
                        <h3 className="text-lg font-semibold mt-4 mb-2">{content.sections.infoCollect.auto.title[language]}</h3>
                        <ul className="list-disc pl-6 space-y-2 text-[#1E1E1E]/80">
                            {content.sections.infoCollect.auto.items[language].map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    </section>

                    {/* How We Use */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            3. {content.sections.howWeUse.title[language]}
                        </h2>
                        <ul className="list-disc pl-6 space-y-2 text-[#1E1E1E]/80">
                            {content.sections.howWeUse.items[language].map((item, i) => (
                                <li key={i}>{item}</li>
                            ))}
                        </ul>
                    </section>

                    {/* AI-Generated Content */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            4. {content.sections.ai.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.sections.ai.text[language]}
                        </p>
                    </section>

                    {/* Data Sharing */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            5. {content.sections.sharing.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.sections.sharing.text[language]}
                        </p>
                    </section>

                    {/* GDPR Rights */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            6. {content.sections.gdpr.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed mb-4">
                            {content.sections.gdpr.intro[language]}
                        </p>
                        <ul className="list-disc pl-6 space-y-2 text-[#1E1E1E]/80">
                            <li><strong>{language === 'en' ? 'Right to Access:' : language === 'it' ? 'Diritto di Accesso:' : language === 'fr' ? 'Droit d\'Accès :' : language === 'es' ? 'Derecho de Acceso:' : 'Recht auf Zugang:'}</strong> {language === 'en' ? 'Request copies of your personal data' : language === 'it' ? 'Richiedi copie dei tuoi dati personali' : language === 'fr' ? 'Demandez des copies de vos données personnelles' : language === 'es' ? 'Solicite copias de sus datos personales' : 'Fordern Sie Kopien Ihrer persönlichen Daten an'}</li>
                            <li><strong>{language === 'en' ? 'Right to Rectification:' : language === 'it' ? 'Diritto di Rettifica:' : language === 'fr' ? 'Droit de Rectification :' : language === 'es' ? 'Derecho de Rectificación:' : 'Recht auf Berichtigung:'}</strong> {language === 'en' ? 'Request correction of inaccurate data' : language === 'it' ? 'Richiedi la correzione di dati inesatti' : language === 'fr' ? 'Demandez la correction de données inexactes' : language === 'es' ? 'Solicite la corrección de datos inexactos' : 'Fordern Sie die Korrektur ungenauer Daten an'}</li>
                            <li><strong>{language === 'en' ? 'Right to Erasure:' : language === 'it' ? 'Diritto alla Cancellazione:' : language === 'fr' ? 'Droit à l\'Effacement :' : language === 'es' ? 'Derecho de Supresión:' : 'Recht auf Löschung:'}</strong> {language === 'en' ? 'Request deletion of your data' : language === 'it' ? 'Richiedi la cancellazione dei tuoi dati' : language === 'fr' ? 'Demandez la suppression de vos données' : language === 'es' ? 'Solicite la eliminación de sus datos' : 'Fordern Sie die Löschung Ihrer Daten an'}</li>
                            <li><strong>{language === 'en' ? 'Right to Data Portability:' : language === 'it' ? 'Diritto alla Portabilità:' : language === 'fr' ? 'Droit à la Portabilité :' : language === 'es' ? 'Derecho a la Portabilidad:' : 'Recht auf Datenübertragbarkeit:'}</strong> {language === 'en' ? 'Request transfer of your data' : language === 'it' ? 'Richiedi il trasferimento dei tuoi dati' : language === 'fr' ? 'Demandez le transfert de vos données' : language === 'es' ? 'Solicite la transferencia de sus datos' : 'Fordern Sie die Übertragung Ihrer Daten an'}</li>
                            <li><strong>{language === 'en' ? 'Right to Object:' : language === 'it' ? 'Diritto di Opposizione:' : language === 'fr' ? 'Droit d\'Opposition :' : language === 'es' ? 'Derecho de Oposición:' : 'Widerspruchsrecht:'}</strong> {language === 'en' ? 'Object to processing of your data' : language === 'it' ? 'Opponiti al trattamento dei tuoi dati' : language === 'fr' ? 'Opposez-vous au traitement de vos données' : language === 'es' ? 'Oponerse al procesamiento de sus datos' : 'Widersprechen Sie der Verarbeitung Ihrer Daten'}</li>
                        </ul>
                    </section>

                    {/* Data Security */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            7. {content.sections.security.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.sections.security.text[language]}
                        </p>
                    </section>

                    {/* Contact Us */}
                    <section>
                        <h2 className="text-2xl font-bold text-[#6A1F2E] mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            8. {content.sections.contact.title[language]}
                        </h2>
                        <p className="text-[#1E1E1E]/80 leading-relaxed">
                            {content.sections.contact.text[language]} <Link to="/contact" className="text-[#6A1F2E] hover:underline">{content.sections.contact.link[language]}</Link>.
                        </p>
                    </section>

                </div>
            </section>
        </div>
    );
};

export default PrivacyPage;
