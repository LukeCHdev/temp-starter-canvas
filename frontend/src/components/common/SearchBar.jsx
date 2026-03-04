import React, { useState, useCallback } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI } from '@/utils/api';
import { toast } from 'sonner';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';

export const SearchBar = ({ className = '' }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { language, getLocalizedPath } = useLanguage();
    const { t: i18nT } = useTranslation();
    const lang = language || 'en';

    const handleSearch = useCallback(async (e) => {
        e.preventDefault();
        const query = searchQuery.trim();
        if (!query || query.length < 2) return;

        setLoading(true);
        try {
            const res = await recipeAPI.search(query, lang);
            const data = res.data;

            if (data.found && data.recipes && data.recipes.length > 0) {
                // Navigate to the first (best) match
                const recipePath = getLocalizedPath(`/recipe/${data.recipes[0].slug}`);
                navigate(recipePath);
            } else {
                toast.info(i18nT('search.noResults'));
            }

        } catch (error) {
            if (error.response && error.response.status === 429) {
                toast.error(i18nT('search.rateLimited', 'Too many searches. Please wait.'));
            } else if (error.code === 'ECONNABORTED') {
                toast.error(i18nT('search.timeout', 'Search timed out. Please try again.'));
            } else {
                toast.error(i18nT('search.failed'));
            }
        } finally {
            setLoading(false);
        }
    }, [searchQuery, navigate, i18nT, getLocalizedPath, lang]);

    return (
        <form onSubmit={handleSearch} className={`flex gap-2 ${className}`} data-testid="search-form">
            <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#9C9C9C]" />
                <Input
                    type="text"
                    placeholder={t('homepage.hero.searchPlaceholder', lang)}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    maxLength={80}
                    className="pl-12 bg-white border-[#E8E4DC] focus:border-[#6A1F2E] focus:ring-[#6A1F2E]/20 h-14 text-base font-light"
                    data-testid="search-input"
                    disabled={loading}
                />
            </div>
            <Button
                type="submit"
                className="bg-[#6A1F2E] hover:bg-[#8B2840] text-white h-14 px-8 font-light tracking-wide"
                data-testid="search-button"
                disabled={loading || searchQuery.trim().length < 2}
            >
                {loading ? (
                    <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {t('search.searching', lang)}
                    </>
                ) : (
                    t('search.button', lang)
                )}
            </Button>
        </form>
    );
};
