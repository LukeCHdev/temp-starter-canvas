import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { favoritesAPI } from '@/utils/api';
import RecipeCard from '@/components/recipe/RecipeCard';
import { Button } from '@/components/ui/button';
import { Heart, Loader2, ChefHat } from 'lucide-react';

const FavoritesPage = () => {
    const { user } = useAuth();
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';

    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            if (!user) { setLoading(false); return; }
            try {
                const res = await favoritesAPI.myFavorites();
                setRecipes(res.data.recipes || []);
            } catch {
                setRecipes([]);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [user]);

    if (!user) {
        return (
            <div className="min-h-screen bg-[#FDFBF7] flex items-center justify-center px-4">
                <div className="text-center max-w-md" data-testid="favorites-login-prompt">
                    <Heart className="w-12 h-12 text-[#6A1F2E] mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('favorites.loginRequired', lang)}
                    </h2>
                    <p className="text-[#7C7C7C] mb-6">{t('favorites.loginDescription', lang)}</p>
                    <Link to={getLocalizedPath(`/login?redirect=${encodeURIComponent(getLocalizedPath('/favorites'))}`)}>
                        <Button className="bg-[#6A1F2E] hover:bg-[#8B2840]">
                            {t('auth.login', lang)}
                        </Button>
                    </Link>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-[#FDFBF7] flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#6A1F2E]" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#FDFBF7]" data-testid="favorites-page">
            <div className="max-w-6xl mx-auto px-4 py-12">
                <div className="flex items-center gap-3 mb-8">
                    <Heart className="w-7 h-7 text-[#6A1F2E]" />
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('favorites.title', lang)}
                    </h1>
                    {recipes.length > 0 && (
                        <span className="text-sm text-[#7C7C7C] bg-[#F0ECE3] px-3 py-1 rounded-full">
                            {recipes.length}
                        </span>
                    )}
                </div>

                {recipes.length === 0 ? (
                    <div className="text-center py-20" data-testid="favorites-empty">
                        <ChefHat className="w-16 h-16 text-[#D4CFC4] mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('favorites.empty', lang)}
                        </h2>
                        <p className="text-[#7C7C7C] mb-6">{t('favorites.emptyDescription', lang)}</p>
                        <Link to={getLocalizedPath('/explore')}>
                            <Button variant="outline" className="border-[#6A1F2E] text-[#6A1F2E]">
                                {t('favorites.exploreRecipes', lang)}
                            </Button>
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {recipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.slug}
                                recipe={recipe}
                                lang={lang}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FavoritesPage;
