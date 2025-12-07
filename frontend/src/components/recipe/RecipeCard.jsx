import React from 'react';
import { Link } from 'react-router-dom';
import { Clock, ChefHat } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const RecipeCard = ({ recipe }) => {
    const title = recipe.title_translated?.en || recipe.title_original;
    const authenticityRank = recipe.source_validation?.authenticity_rank || 1;
    
    const rankColors = {
        1: 'bg-[#CBA55B] text-white',
        2: 'bg-[#3F4A3C] text-white',
        3: 'bg-[#6A1F2E] text-white',
    };
    
    const rankLabels = {
        1: 'Official',
        2: 'Traditional',
        3: 'Modern',
    };

    return (
        <Link to={`/recipe/${recipe.slug}`} data-testid={`recipe-card-${recipe.slug}`}>
            <Card className="card-elegant group cursor-pointer h-full flex flex-col">
                <div className="relative overflow-hidden rounded-sm mb-4 h-48 bg-[#F5F2E8]">
                    <div className="absolute inset-0 flex items-center justify-center">
                        <ChefHat className="h-16 w-16 text-[#CBA55B]/30" />
                    </div>
                    <Badge className={`absolute top-3 right-3 ${rankColors[authenticityRank]}`}>
                        {rankLabels[authenticityRank]}
                    </Badge>
                </div>
                
                <div className="flex-1 flex flex-col">
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors">
                        {title}
                    </h3>
                    
                    <p className="text-sm text-[#1E1E1E]/60 mb-3">
                        {recipe.country} • {recipe.region}
                    </p>
                    
                    <p className="narrative-text text-sm line-clamp-3 flex-1">
                        {recipe.origin_story?.substring(0, 150)}...
                    </p>
                    
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] flex items-center text-sm text-[#1E1E1E]/60">
                        <Clock className="h-4 w-4 mr-1" />
                        <span>{recipe.authenticity_levels?.length || 1} variations</span>
                    </div>
                </div>
            </Card>
        </Link>
    );
};