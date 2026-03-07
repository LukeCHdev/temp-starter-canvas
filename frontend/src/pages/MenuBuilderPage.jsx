import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { menuAPI, countryAPI } from '@/utils/api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Loader2, Globe } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';

const MenuBuilderPage = () => {
    const { t } = useTranslation();
    const { language } = useLanguage();
    const [countries, setCountries] = useState([]);
    const [selectedCountry, setSelectedCountry] = useState('');
    const [menu, setMenu] = useState(null);
    const [loading, setLoading] = useState(false);

    // Localized UI text
    const uiText = {
        en: {
            title: 'AI-Powered Menu Builder',
            subtitle: 'Let Sous Chef Linguine create a culturally coherent menu from authentic country recipes.',
            selectCountry: 'Select a Country',
            placeholder: 'Choose a country...',
            generateBtn: 'Generate Menu',
            selectError: 'Please select a country',
            loadError: 'Failed to load countries',
            generateError: 'Failed to generate menu. Try adding more recipes from this country.',
            success: 'Menu generated successfully!',
            winePairing: 'Wine Pairing'
        },
        it: {
            title: 'Generatore di Menu con IA',
            subtitle: 'Lascia che Sous Chef Linguine crei un menu culturalmente coerente da ricette autentiche del paese.',
            selectCountry: 'Seleziona un Paese',
            placeholder: 'Scegli un paese...',
            generateBtn: 'Genera Menu',
            selectError: 'Seleziona un paese',
            loadError: 'Impossibile caricare i paesi',
            generateError: 'Impossibile generare il menu. Prova ad aggiungere più ricette da questo paese.',
            success: 'Menu generato con successo!',
            winePairing: 'Abbinamento Vini'
        },
        fr: {
            title: 'Générateur de Menu IA',
            subtitle: 'Laissez Sous Chef Linguine créer un menu culturellement cohérent à partir de recettes authentiques du pays.',
            selectCountry: 'Sélectionnez un Pays',
            placeholder: 'Choisissez un pays...',
            generateBtn: 'Générer le Menu',
            selectError: 'Veuillez sélectionner un pays',
            loadError: 'Échec du chargement des pays',
            generateError: 'Échec de la génération du menu. Essayez d\'ajouter plus de recettes de ce pays.',
            success: 'Menu généré avec succès!',
            winePairing: 'Accord Mets-Vins'
        },
        es: {
            title: 'Generador de Menú con IA',
            subtitle: 'Deja que Sous Chef Linguine cree un menú culturalmente coherente con recetas auténticas del país.',
            selectCountry: 'Selecciona un País',
            placeholder: 'Elige un país...',
            generateBtn: 'Generar Menú',
            selectError: 'Por favor selecciona un país',
            loadError: 'Error al cargar los países',
            generateError: 'Error al generar el menú. Intenta agregar más recetas de este país.',
            success: '¡Menú generado con éxito!',
            winePairing: 'Maridaje de Vinos'
        },
        de: {
            title: 'KI-gestützter Menü-Generator',
            subtitle: 'Lassen Sie Sous Chef Linguine ein kulturell stimmiges Menü aus authentischen Länderrezepten erstellen.',
            selectCountry: 'Wählen Sie ein Land',
            placeholder: 'Land auswählen...',
            generateBtn: 'Menü Generieren',
            selectError: 'Bitte wählen Sie ein Land',
            loadError: 'Länder konnten nicht geladen werden',
            generateError: 'Menü konnte nicht generiert werden. Versuchen Sie, mehr Rezepte aus diesem Land hinzuzufügen.',
            success: 'Menü erfolgreich generiert!',
            winePairing: 'Weinempfehlung'
        }
    };

    const txt = uiText[language] || uiText.en;

    useEffect(() => {
        loadCountries();
    }, []);

    const loadCountries = async () => {
        try {
            const res = await countryAPI.getAll();
            // Sort countries alphabetically by name
            const sortedCountries = (res.data.countries || []).sort((a, b) => 
                a.name.localeCompare(b.name)
            );
            setCountries(sortedCountries);
        } catch (error) {
            toast.error(txt.loadError);
        }
    };

    // Translate country name based on current language
    const getLocalizedCountryName = (countryName) => {
        return t(`countries.${countryName}`, { defaultValue: countryName });
    };

    const generateMenu = async () => {
        if (!selectedCountry) {
            toast.error(txt.selectError);
            return;
        }

        setLoading(true);
        try {
            // Pass country to the menu builder API
            const res = await menuAPI.build(selectedCountry);
            setMenu(res.data);
            toast.success(txt.success);
        } catch (error) {
            toast.error(error.response?.data?.detail || txt.generateError);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen" data-testid="menu-builder-page">
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-16 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="mb-4 text-[#1E1E1E]" style={{ fontFamily: 'var(--font-heading)' }}>
                        {txt.title}
                    </h1>
                    <div className="gold-divider"></div>
                    <p className="narrative-text text-lg mt-6">
                        {txt.subtitle}
                    </p>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="card-elegant mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <Globe className="h-5 w-5 text-[#6A1F2E]" />
                        {txt.selectCountry}
                    </h2>
                    <div className="flex gap-4">
                        <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                            <SelectTrigger className="flex-1" data-testid="country-select">
                                <SelectValue placeholder={txt.placeholder} />
                            </SelectTrigger>
                            <SelectContent>
                                {countries.map((country) => (
                                    <SelectItem key={country.slug} value={country.slug}>
                                        {getLocalizedCountryName(country.name)}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <Button 
                            onClick={generateMenu} 
                            disabled={loading || !selectedCountry}
                            className="btn-elegant"
                            data-testid="generate-menu-btn"
                        >
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {txt.generateBtn}
                        </Button>
                    </div>
                </div>

                {menu && (
                    <div className="card-elegant" data-testid="generated-menu">
                        <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                            {menu.menu_title}
                        </h2>
                        <p className="narrative-text mb-6">{menu.cultural_context}</p>

                        <div className="space-y-6">
                            {menu.courses.map((course, index) => (
                                <div key={index} className="border-l-4 border-[#CBA55B] pl-4" data-testid={`course-${course.course_type}`}>
                                    <h3 className="font-semibold text-lg capitalize mb-2">{course.course_type}</h3>
                                    <p className="text-[#1E1E1E] font-medium mb-1">{course.recipe_title}</p>
                                    <p className="narrative-text text-sm">{course.pairing_justification}</p>
                                </div>
                            ))}
                        </div>

                        {menu.wine_pairing && (
                            <div className="mt-6 pt-6 border-t border-[#E5DCC3]">
                                <h3 className="font-semibold mb-2">{txt.winePairing}</h3>
                                <p className="narrative-text text-sm">{menu.wine_pairing}</p>
                            </div>
                        )}
                    </div>
                )}
            </section>
        </div>
    );
};

export default MenuBuilderPage;
