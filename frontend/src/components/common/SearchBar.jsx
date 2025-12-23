import React, { useState, useCallback } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI } from '@/utils/api';
import { toast } from 'sonner';
import { useLanguage } from '@/context/LanguageContext';

export const SearchBar = ({ className = '' }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { language, getLocalizedPath } = useLanguage();
    const { t } = useTranslation();

    const handleSearch = useCallback(async (e) => {
        e.preventDefault();
        const query = searchQuery.trim();
        if (!query) return;

        setLoading(true);
        try {
            // Use current language from route for search results
            const res = await recipeAPI.search(query, true, language);
            const data = res.data;

            console.log('Search response:', data);

            if (data.found && data.recipe && data.recipe.slug) {
                if (data.generated) {
                    toast.success(t('search.generatedSuccess'));
                }
                const recipePath = getLocalizedPath(`/recipe/${data.recipe.slug}`);
                console.log('Navigating to:', recipePath);
                navigate(recipePath);
            } else if (data.message) {
                toast.error(data.message);
            } else {
                toast.info(t('search.noResults'));
            }

        } catch (error) {
            console.error("Search error:", error);
            if (error.code === 'ECONNABORTED') {
                toast.error(t('search.timeout', 'Search timed out. Please try again.'));
            } else {
                toast.error(t('search.failed'));
            }
        } finally {
            setLoading(false);
        }
    }, [searchQuery, navigate, t, getLocalizedPath, language]);

    return (
        <form onSubmit={handleSearch} className={`flex gap-2 ${className}`} data-testid="search-form">
            <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#1E1E1E]/40" />
                <Input
                    type="text"
                    placeholder={t('search.placeholder')}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-white border-[#E5DCC3] focus:border-[#CBA55B] rounded-none h-12"
                    data-testid="search-input"
                    disabled={loading}
                />
            </div>
            <Button
                type="submit"
                className="bg-[#6A1F2E] hover:bg-[#8B2840] text-white rounded-none h-12 px-8"
                data-testid="search-button"
                disabled={loading}
            >
                {loading ? (
                    <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {t('search.searching')}
                    </>
                ) : (
                    t('search.button')
                )}
            </Button>
        </form>
    );
};
