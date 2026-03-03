import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Star, MessageSquare, Send, Loader2, User, Edit2, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { recipeAPI } from '@/utils/api';
import { useLanguage } from '@/context/LanguageContext';
import { useAuth } from '@/context/AuthContext';
import { t } from '@/i18n/translations';

// Star Rating Input Component
const StarRatingInput = ({ rating, onRatingChange, disabled = false, lang = 'en' }) => {
    const [hoverRating, setHoverRating] = useState(0);

    return (
        <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
                <button
                    key={star}
                    type="button"
                    disabled={disabled}
                    className={`p-1 transition-colors ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                    onMouseEnter={() => !disabled && setHoverRating(star)}
                    onMouseLeave={() => !disabled && setHoverRating(0)}
                    onClick={() => !disabled && onRatingChange(star)}
                >
                    <Star
                        className={`w-7 h-7 transition-colors ${
                            star <= (hoverRating || rating)
                                ? 'fill-amber-400 text-amber-400'
                                : 'text-gray-300'
                        }`}
                    />
                </button>
            ))}
            {rating > 0 && (
                <span className="ml-2 text-sm text-gray-600">
                    {rating} {rating === 1 ? t('review.star', lang) : t('review.stars', lang)}
                </span>
            )}
        </div>
    );
};

// Star Rating Display Component
const StarRatingDisplay = ({ rating, size = 'md' }) => {
    const starSize = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    return (
        <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map((star) => (
                <Star
                    key={star}
                    className={`${starSize} ${
                        star <= fullStars
                            ? 'fill-amber-400 text-amber-400'
                            : star === fullStars + 1 && hasHalfStar
                            ? 'fill-amber-400/50 text-amber-400'
                            : 'text-gray-300'
                    }`}
                />
            ))}
        </div>
    );
};

// Single Review Card
const ReviewCard = ({ review, lang = 'en', isOwn = false, onEdit, onDelete }) => {
    // Format date according to locale
    const dateLocales = {
        en: 'en-US',
        es: 'es-ES',
        it: 'it-IT',
        fr: 'fr-FR',
        de: 'de-DE'
    };
    
    const formattedDate = new Date(review.created_at).toLocaleDateString(dateLocales[lang] || 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });

    return (
        <div className={`py-4 border-b border-gray-100 last:border-0 ${isOwn ? 'bg-amber-50/50 -mx-2 px-2 rounded' : ''}`}>
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center overflow-hidden">
                        {review.avatar_url ? (
                            <img src={review.avatar_url} alt={review.username} className="w-full h-full object-cover" />
                        ) : (
                            <User className="w-4 h-4 text-amber-700" />
                        )}
                    </div>
                    <div>
                        <p className="text-sm font-medium text-[#2C2C2C]">{review.username}</p>
                        <div className="flex items-center gap-2">
                            <StarRatingDisplay rating={review.rating} size="sm" />
                            <span className="text-xs text-gray-500">{formattedDate}</span>
                        </div>
                    </div>
                </div>
                {isOwn && (
                    <div className="flex items-center gap-1">
                        <button 
                            onClick={onEdit}
                            className="p-1 text-[#6A1F2E] hover:bg-[#6A1F2E]/10 rounded"
                            title={t('review.editReview', lang)}
                        >
                            <Edit2 className="w-4 h-4" />
                        </button>
                        <button 
                            onClick={onDelete}
                            className="p-1 text-red-600 hover:bg-red-50 rounded"
                            title={t('review.deleteReview', lang)}
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>
            {review.comment && (
                <p className="text-gray-700 text-sm leading-relaxed ml-11">
                    {review.comment}
                </p>
            )}
        </div>
    );
};

// Login Prompt Component
const LoginPrompt = ({ lang, redirectPath, getLocalizedPath }) => (
    <div className="text-center py-8 bg-[#F5F2EC] rounded-lg">
        <Star className="w-10 h-10 text-[#6A1F2E] mx-auto mb-3" />
        <p className="text-[#2C2C2C] font-medium mb-2">
            {t('review.loginRequired', lang)}
        </p>
        <div className="flex justify-center gap-3 mt-4">
            <Link to={getLocalizedPath(`/login?redirect=${encodeURIComponent(redirectPath)}`)}>
                <Button variant="outline" className="border-[#6A1F2E] text-[#6A1F2E] hover:bg-[#6A1F2E] hover:text-white">
                    {t('auth.login', lang)}
                </Button>
            </Link>
            <Link to={getLocalizedPath(`/signup?redirect=${encodeURIComponent(redirectPath)}`)}>
                <Button className="bg-[#6A1F2E] hover:bg-[#8B2840]">
                    {t('auth.signUp', lang)}
                </Button>
            </Link>
        </div>
    </div>
);

// Main Review Section Component
export const ReviewSection = ({ slug, initialRating = 0, initialCount = 0 }) => {
    const [reviews, setReviews] = useState([]);
    const [userReview, setUserReview] = useState(null);
    const [averageRating, setAverageRating] = useState(initialRating);
    const [ratingsCount, setRatingsCount] = useState(initialCount);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    
    // Form state
    const [userRating, setUserRating] = useState(0);
    const [userComment, setUserComment] = useState('');
    
    const { language, getLocalizedPath } = useLanguage();
    const { user, isAuthenticated } = useAuth();
    const lang = language || 'en';
    
    // Current path for redirect
    const currentPath = `/recipe/${slug}`;

    useEffect(() => {
        loadReviews();
    }, [slug]);
    
    // Pre-fill form if user has existing review
    useEffect(() => {
        if (userReview && isEditing) {
            setUserRating(userReview.rating);
            setUserComment(userReview.comment || '');
        } else if (!isEditing) {
            if (userReview) {
                setUserRating(userReview.rating);
                setUserComment(userReview.comment || '');
            } else {
                setUserRating(0);
                setUserComment('');
            }
        }
    }, [userReview, isEditing]);

    const loadReviews = async () => {
        try {
            const res = await recipeAPI.getReviews(slug);
            setReviews(res.data.reviews || []);
            setAverageRating(res.data.average_rating || 0);
            setRatingsCount(res.data.ratings_count || 0);
            setUserReview(res.data.user_review || null);
        } catch (error) {
            console.error('Failed to load reviews:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitReview = async (e) => {
        e.preventDefault();
        
        if (userRating === 0) {
            toast.error(t('review.selectRating', lang));
            return;
        }

        setSubmitting(true);
        try {
            const res = await recipeAPI.createReview(slug, {
                rating: userRating,
                comment: userComment.trim() || null
            });

            if (res.data.success) {
                toast.success(t('review.thankYou', lang));
                setAverageRating(res.data.average_rating);
                setRatingsCount(res.data.ratings_count);
                setUserReview(res.data.review);
                setIsEditing(false);
                // Reload reviews to show the new one
                loadReviews();
            }
        } catch (error) {
            const msg = error.response?.data?.detail || t('review.submitError', lang);
            toast.error(msg);
            console.error('Review submission error:', error);
        } finally {
            setSubmitting(false);
        }
    };

    const handleEditReview = () => {
        setIsEditing(true);
    };

    const handleDeleteReview = async () => {
        if (!window.confirm(t('review.deleteConfirm', lang))) {
            return;
        }
        
        try {
            const res = await recipeAPI.deleteReview(slug);
            if (res.data.success) {
                toast.success(t('review.deleteReview', lang));
                setUserReview(null);
                setUserRating(0);
                setUserComment('');
                setAverageRating(res.data.average_rating);
                setRatingsCount(res.data.ratings_count);
                loadReviews();
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to delete review');
        }
    };

    const handleCancelEdit = () => {
        setIsEditing(false);
        if (userReview) {
            setUserRating(userReview.rating);
            setUserComment(userReview.comment || '');
        }
    };

    return (
        <Card className="bg-white border-[#6A1F2E]/10" id="reviews">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-[#1E1E1E]">
                    <MessageSquare className="h-5 w-5 text-[#6A1F2E]" />
                    {t('review.title', lang)}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {/* Rating Summary */}
                <div className="flex items-center gap-6 mb-6 p-4 bg-amber-50/50 rounded-lg">
                    <div className="text-center">
                        <div className="text-4xl font-bold text-[#6A1F2E]">
                            {averageRating > 0 ? averageRating.toFixed(1) : '—'}
                        </div>
                        <StarRatingDisplay rating={averageRating} />
                        <p className="text-sm text-gray-500 mt-1">
                            {ratingsCount} {ratingsCount === 1 ? t('review.rating', lang) : t('review.ratings', lang)}
                        </p>
                    </div>
                    <Separator orientation="vertical" className="h-20" />
                    <div className="flex-1">
                        <p className="text-sm text-gray-600">
                            {ratingsCount === 0 
                                ? t('review.beFirstToRate', lang)
                                : t('review.shareExperience', lang)}
                        </p>
                    </div>
                </div>

                {/* Review Form or Login Prompt */}
                {!isAuthenticated ? (
                    <LoginPrompt 
                        lang={lang} 
                        redirectPath={currentPath}
                        getLocalizedPath={getLocalizedPath}
                    />
                ) : userReview && !isEditing ? (
                    // Show existing review
                    <div className="mb-6">
                        <h4 className="font-medium text-gray-900 mb-3">{t('review.yourReview', lang).replace(' (optional)', '')}</h4>
                        <ReviewCard 
                            review={userReview} 
                            lang={lang} 
                            isOwn={true}
                            onEdit={handleEditReview}
                            onDelete={handleDeleteReview}
                        />
                        <Button 
                            variant="outline" 
                            className="mt-3 border-[#6A1F2E] text-[#6A1F2E]"
                            onClick={handleEditReview}
                        >
                            <Edit2 className="w-4 h-4 mr-2" />
                            {t('review.editReview', lang)}
                        </Button>
                    </div>
                ) : (
                    // Show review form
                    <form onSubmit={handleSubmitReview} className="mb-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-8 h-8 rounded-full bg-[#6A1F2E] flex items-center justify-center overflow-hidden">
                                {user?.avatar_url ? (
                                    <img src={user.avatar_url} alt={user.username} className="w-full h-full object-cover" />
                                ) : (
                                    <span className="text-white text-sm font-medium">
                                        {user?.username?.[0]?.toUpperCase() || 'U'}
                                    </span>
                                )}
                            </div>
                            <span className="text-sm text-gray-600">{user?.username}</span>
                        </div>
                        
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('review.yourRating', lang)} *
                            </label>
                            <StarRatingInput
                                rating={userRating}
                                onRatingChange={setUserRating}
                                disabled={submitting}
                                lang={lang}
                            />
                        </div>
                        
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('review.yourReview', lang)}
                            </label>
                            <Textarea
                                placeholder={t('review.placeholder', lang)}
                                value={userComment}
                                onChange={(e) => setUserComment(e.target.value)}
                                disabled={submitting}
                                className="resize-none"
                                rows={3}
                                maxLength={2000}
                            />
                            <p className="text-xs text-gray-400 mt-1 text-right">
                                {userComment.length}/2000
                            </p>
                        </div>
                        
                        <div className="flex gap-2">
                            <Button 
                                type="submit" 
                                disabled={submitting || userRating === 0}
                                className="bg-[#6A1F2E] hover:bg-[#5A1525] text-white"
                            >
                                {submitting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        {isEditing ? t('review.updating', lang) : t('review.submitting', lang)}
                                    </>
                                ) : (
                                    <>
                                        <Send className="w-4 h-4 mr-2" />
                                        {isEditing ? t('review.editReview', lang) : t('review.submit', lang)}
                                    </>
                                )}
                            </Button>
                            {isEditing && (
                                <Button 
                                    type="button"
                                    variant="outline"
                                    onClick={handleCancelEdit}
                                    disabled={submitting}
                                >
                                    Cancel
                                </Button>
                            )}
                        </div>
                    </form>
                )}

                <Separator className="my-6" />

                {/* Reviews List */}
                <div>
                    <h4 className="font-medium text-gray-900 mb-4">
                        {t('review.recentReviews', lang)} ({reviews.length})
                    </h4>
                    
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-[#6A1F2E]" />
                        </div>
                    ) : reviews.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p>{t('review.noReviews', lang)}</p>
                        </div>
                    ) : (
                        <div className="max-h-[400px] overflow-y-auto pr-2">
                            {reviews.map((review) => (
                                <ReviewCard 
                                    key={review.id} 
                                    review={review} 
                                    lang={lang}
                                    isOwn={user && review.user_id === user.user_id}
                                    onEdit={handleEditReview}
                                    onDelete={handleDeleteReview}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};

export default ReviewSection;
