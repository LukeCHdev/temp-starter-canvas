import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { favoritesAPI } from '@/utils/api';
import { Heart } from 'lucide-react';
import { cn } from '@/lib/utils';

const FavoriteButton = ({ slug, className, size = 'md', deferStatusCheck = false }) => {
    const { user } = useAuth();
    const { getLocalizedPath } = useLanguage();
    const navigate = useNavigate();
    const [favorited, setFavorited] = useState(false);
    const [loading, setLoading] = useState(false);
    const [statusChecked, setStatusChecked] = useState(false);

    // Only check favorite status when visible (not in bulk list views)
    useEffect(() => {
        if (!user || !slug || statusChecked) return;
        if (deferStatusCheck) return; // Skip on list pages — check on interaction
        let cancelled = false;
        favoritesAPI.status(slug).then(res => {
            if (!cancelled) {
                setFavorited(res.data.favorited);
                setStatusChecked(true);
            }
        }).catch(() => {});
        return () => { cancelled = true; };
    }, [user, slug, deferStatusCheck, statusChecked]);

    const toggle = useCallback(async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (!user) {
            const currentPath = window.location.pathname;
            navigate(getLocalizedPath(`/login?redirect=${encodeURIComponent(currentPath)}`));
            return;
        }

        if (loading) return;
        setLoading(true);

        // If status wasn't checked yet (deferred), check now before toggling
        if (!statusChecked) {
            try {
                const res = await favoritesAPI.status(slug);
                setFavorited(res.data.favorited);
                setStatusChecked(true);
                // Now toggle based on actual status
                const current = res.data.favorited;
                setFavorited(!current);
                if (current) {
                    await favoritesAPI.remove(slug);
                } else {
                    await favoritesAPI.add(slug);
                }
            } catch {
                // revert is not needed since we had no optimistic update
            } finally {
                setLoading(false);
            }
            return;
        }

        const prev = favorited;
        setFavorited(!prev); // optimistic

        try {
            if (prev) {
                await favoritesAPI.remove(slug);
            } else {
                await favoritesAPI.add(slug);
            }
        } catch {
            setFavorited(prev); // revert
        } finally {
            setLoading(false);
        }
    }, [user, slug, favorited, loading, navigate, getLocalizedPath, statusChecked]);

    const iconSize = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';
    const btnSize = size === 'sm' ? 'w-8 h-8' : 'w-10 h-10';

    return (
        <button
            onClick={toggle}
            disabled={loading}
            data-testid={`favorite-btn-${slug}`}
            aria-label={favorited ? 'Remove from favorites' : 'Add to favorites'}
            className={cn(
                'flex items-center justify-center rounded-full transition-all duration-200',
                btnSize,
                favorited
                    ? 'bg-red-50 text-red-500 hover:bg-red-100'
                    : 'bg-white/80 text-[#7C7C7C] hover:text-red-500 hover:bg-red-50',
                'backdrop-blur-sm shadow-sm border border-[#E8E4DC]/50',
                className
            )}
        >
            <Heart
                className={cn(iconSize, favorited && 'fill-current')}
            />
        </button>
    );
};

export default FavoriteButton;
