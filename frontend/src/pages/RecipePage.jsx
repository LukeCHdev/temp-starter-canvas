import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { recipeAPI } from '@/utils/api';
import { AuthenticityBadge } from '@/components/recipe/AuthenticityBadge';
import { IngredientTable } from '@/components/recipe/IngredientTable';
import { InstructionSteps } from '@/components/recipe/InstructionSteps';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { toast } from 'sonner';

const RecipePage = () => {
    const { slug } = useParams();
    const [recipe, setRecipe] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadRecipe();
    }, [slug]);

    const loadRecipe = async () => {
        try {
            const res = await recipeAPI.getBySlug(slug);
            setRecipe(res.data);
        } catch (error) {
            toast.error('Recipe not found');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center" data-testid="loading-state">
                <p>Loading recipe...</p>
            </div>
        );
    }

    if (!recipe) {
        return (
            <div className="min-h-screen flex items-center justify-center" data-testid="not-found-state">
                <p>Recipe not found</p>
            </div>
        );
    }

    const title = recipe.title_translated?.en || recipe.title_original;

    return (
        <div className="min-h-screen" data-testid="recipe-page">
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <div className="mb-4">
                        <AuthenticityBadge 
                            rank={recipe.source_validation?.authenticity_rank || 2}
                            classification={recipe.authenticity_levels[0]?.classification || 'Traditional'}
                        />
                    </div>
                    <h1 className="mb-4 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {title}
                    </h1>
                    <p className="text-lg text-[#1E1E1E]/70">
                        {recipe.country} • {recipe.region}
                    </p>
                </div>
            </section>

            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="card-elegant mb-8">
                    <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Origin Story
                    </h2>
                    <p className="narrative-text">{recipe.origin_story}</p>
                </div>

                <div className="card-elegant mb-8">
                    <h2 className="text-2xl font-semibold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Cultural Background
                    </h2>
                    <p className="narrative-text">{recipe.cultural_background}</p>
                </div>

                <div className="mb-8">
                    <h2 className="text-3xl font-semibold mb-6" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Authenticity Levels
                    </h2>
                    <Accordion type="single" collapsible defaultValue="level-0">
                        {recipe.authenticity_levels.map((level, index) => (
                            <AccordionItem key={index} value={`level-${index}`} data-testid={`level-${level.level}`}>
                                <AccordionTrigger className="text-lg">
                                    Level {level.level}: {level.classification}
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="space-y-6 pt-4">
                                        <div>
                                            <p className="narrative-text mb-4">{level.cultural_explanation}</p>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold mb-3">Ingredients</h4>
                                            <IngredientTable ingredients={level.ingredients} />
                                        </div>

                                        <div>
                                            <h4 className="font-semibold mb-3">Instructions</h4>
                                            <InstructionSteps steps={level.method} />
                                        </div>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>
                        ))}
                    </Accordion>
                </div>
            </section>
        </div>
    );
};

export default RecipePage;