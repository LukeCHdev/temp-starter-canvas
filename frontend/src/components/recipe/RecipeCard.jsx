import React from 'react';
import { Link } from 'react-router-dom';
import { Clock, ChefHat, Globe, Star } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';

export const RecipeCard = ({ recipe }) => {
    const { getLocalizedPath } = useLanguage();
    
    // Handle both old and new schema
    const title = recipe.recipe_name || recipe.title_translated?.en || recipe.title_original || 'Unknown Recipe';
    const country = recipe.origin_country || recipe.country || 'Unknown';
    const region = recipe.origin_region || recipe.region || 'Unknown';
    const authenticityLevel = recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;
    const description = recipe.history_summary || recipe.characteristic_profile || recipe.origin_story || '';
    
    const levelColors = {
        1: 'bg-[#6A1F2E] text-white',
        2: 'bg-[#3F4A3C] text-white',
        3: 'bg-[#CBA55B] text-white',
        4: 'bg-gray-500 text-white',
        5: 'bg-gray-400 text-white',
    };
    
    const levelLabels = {
        1: 'Official',
        2: 'Traditional',
        3: 'Local',
        4: 'Recognized',
        5: 'Modern',
    };

    // Get photo if available
    const photoUrl = recipe.photos && recipe.photos.length > 0 && recipe.photos[0].image_url 
        ? recipe.photos[0].image_url 
        : null;

    return (
        <Link to={getLocalizedPath(`/recipe/${recipe.slug}`)} data-testid={`recipe-card-${recipe.slug}`}>
            <Card className="card-elegant group cursor-pointer h-full flex flex-col">
                <div className="relative overflow-hidden rounded-sm mb-4 h-48 bg-[#F5F2E8]">
                    {photoUrl ? (
                        <img 
                            src={photoUrl} 
                            alt={title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <ChefHat className="h-16 w-16 text-[#CBA55B]/30" />
                        </div>
                    )}
                    <Badge className={`absolute top-3 right-3 ${levelColors[authenticityLevel] || levelColors[3]}`}>
                        <Star className="h-3 w-3 mr-1" />
                        {levelLabels[authenticityLevel] || 'Traditional'}
                    </Badge>
                </div>
                
                <div className="flex-1 flex flex-col">
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors line-clamp-2">
                        {title}
                    </h3>
                    
                    <p className="text-sm text-[#1E1E1E]/60 mb-3 flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        {country} • {region}
                    </p>
                    
                    {description && (
                        <p className="narrative-text text-sm line-clamp-3 flex-1">
                            {description.substring(0, 150)}{description.length > 150 ? '...' : ''}
                        </p>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] flex items-center justify-between text-sm text-[#1E1E1E]/60">
                        {recipe.ingredients && (
                            <span>{recipe.ingredients.length} ingredients</span>
                        )}
                        {recipe.gpt_used && (
                            <Badge variant="outline" className="text-xs">
                                {recipe.gpt_used}
                            </Badge>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
};
