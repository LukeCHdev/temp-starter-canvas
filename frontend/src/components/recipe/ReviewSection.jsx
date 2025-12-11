import React, { useState, useEffect } from 'react';
import { Star, MessageSquare, Send, Loader2, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { recipeAPI } from '@/utils/api';
import { useLanguage } from '@/context/LanguageContext';

// Star Rating Input Component
const StarRatingInput = ({ rating, onRatingChange, disabled = false }) => {
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
                    {rating} star{rating !== 1 ? 's' : ''}
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
const ReviewCard = ({ review }) => {
    const formattedDate = new Date(review.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });

    return (
        <div className="py-4 border-b border-gray-100 last:border-0">
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                        <User className="w-4 h-4 text-amber-700" />
                    </div>
                    <div>
                        <StarRatingDisplay rating={review.rating} size="sm" />
                        <p className="text-xs text-gray-500 mt-0.5">{formattedDate}</p>
                    </div>
                </div>
                {review.language && review.language !== 'en' && (
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded uppercase">
                        {review.language}
                    </span>
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

// Main Review Section Component
export const ReviewSection = ({ slug, initialRating = 0, initialCount = 0 }) => {
    const [reviews, setReviews] = useState([]);
    const [averageRating, setAverageRating] = useState(initialRating);
    const [ratingsCount, setRatingsCount] = useState(initialCount);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    
    // Form state
    const [userRating, setUserRating] = useState(0);
    const [userComment, setUserComment] = useState('');
    
    const { language } = useLanguage();

    useEffect(() => {
        loadReviews();
    }, [slug]);

    const loadReviews = async () => {
        try {
            const res = await recipeAPI.getReviews(slug);
            setReviews(res.data.reviews || []);
            setAverageRating(res.data.average_rating || 0);
            setRatingsCount(res.data.ratings_count || 0);
        } catch (error) {
            console.error('Failed to load reviews:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitReview = async (e) => {
        e.preventDefault();
        
        if (userRating === 0) {
            toast.error('Please select a rating');
            return;
        }

        setSubmitting(true);
        try {
            const lang = language?.split('-')[0] || 'en';
            const res = await recipeAPI.createReview(slug, {
                rating: userRating,
                comment: userComment.trim() || null,
                language: lang
            });

            if (res.data.success) {
                toast.success('Thank you for your review!');
                setUserRating(0);
                setUserComment('');
                setAverageRating(res.data.average_rating);
                setRatingsCount(res.data.ratings_count);
                // Reload reviews to show the new one
                loadReviews();
            }
        } catch (error) {
            toast.error('Failed to submit review. Please try again.');
            console.error('Review submission error:', error);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Card className="bg-white border-[#6A1F2E]/10">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-[#1E1E1E]">
                    <MessageSquare className="h-5 w-5 text-[#6A1F2E]" />
                    Ratings & Reviews
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
                            {ratingsCount} {ratingsCount === 1 ? 'rating' : 'ratings'}
                        </p>
                    </div>
                    <Separator orientation="vertical" className="h-20" />
                    <div className="flex-1">
                        <p className="text-sm text-gray-600">
                            {ratingsCount === 0 
                                ? 'Be the first to rate this recipe!'
                                : 'Share your experience with this recipe'}
                        </p>
                    </div>
                </div>

                {/* Submit Review Form */}
                <form onSubmit={handleSubmitReview} className="mb-6">
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Your Rating *
                        </label>
                        <StarRatingInput
                            rating={userRating}
                            onRatingChange={setUserRating}
                            disabled={submitting}
                        />
                    </div>
                    
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Your Review (optional)
                        </label>
                        <Textarea
                            placeholder="Share your thoughts about this recipe..."
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
                    
                    <Button 
                        type="submit" 
                        disabled={submitting || userRating === 0}
                        className="bg-[#6A1F2E] hover:bg-[#5A1525] text-white"
                    >
                        {submitting ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Submitting...
                            </>
                        ) : (
                            <>
                                <Send className="w-4 h-4 mr-2" />
                                Submit Review
                            </>
                        )}
                    </Button>
                </form>

                <Separator className="my-6" />

                {/* Reviews List */}
                <div>
                    <h4 className="font-medium text-gray-900 mb-4">
                        Recent Reviews ({reviews.length})
                    </h4>
                    
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-[#6A1F2E]" />
                        </div>
                    ) : reviews.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p>No reviews yet. Be the first to share your thoughts!</p>
                        </div>
                    ) : (
                        <div className="max-h-[400px] overflow-y-auto pr-2">
                            {reviews.map((review) => (
                                <ReviewCard key={review.id} review={review} />
                            ))}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};

export default ReviewSection;
