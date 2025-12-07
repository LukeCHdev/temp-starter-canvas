import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/utils/api';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { Heart } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const FavoritesPage = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [favorites, setFavorites] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            navigate('/');
            return;
        }
        loadFavorites();
    }, [user, navigate]);

    const loadFavorites = async () => {
        try {
            const res = await api.get('/favorites');
            setFavorites(res.data.recipes || []);
        } catch (error) {
            toast.error('Failed to load favorites');
        } finally {
            setLoading(false);
        }
    };

    if (!user) {
        return null;
    }

    return (
        <div className="min-h-screen" data-testid="favorites-page">
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-16 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <Heart className="h-12 w-12 mx-auto text-[#6A1F2E] mb-4" />
                    <h1 className="mb-4 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        My Favorite Recipes
                    </h1>
                    <div className="gold-divider"></div>
                    <p className="narrative-text text-lg mt-6">
                        Your personal collection of authentic culinary treasures.
                    </p>
                </div>
            </section>

            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                {loading ? (
                    <div className="text-center py-12">
                        <p className="text-[#1E1E1E]/60">Loading favorites...</p>
                    </div>
                ) : favorites.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {favorites.map((recipe) => (
                            <RecipeCard key={recipe.slug} recipe={recipe} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 card-elegant">
                        <Heart className="h-16 w-16 mx-auto text-[#CBA55B]/30 mb-4" />
                        <p className="text-[#1E1E1E]/60 mb-2">No favorites yet</p>
                        <p className="text-sm text-[#1E1E1E]/50">
                            Start exploring recipes and save your favorites!
                        </p>
                    </div>
                )}
            </section>
        </div>
    );
};

export default FavoritesPage;
