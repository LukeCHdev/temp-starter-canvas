import React from 'react';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { useRelatedRecipes } from '@/hooks/useRelatedRecipes';

/**
 * RelatedRecipes — horizontal scroll on mobile, 4-col grid on desktop.
 * Placed at the bottom of the recipe page.
 */
const RelatedRecipes = ({ recipe, lang }) => {
  const { data: related, isLoading } = useRelatedRecipes(recipe, lang);

  if (isLoading || !related || related.length === 0) return null;

  return (
    <section className="mt-8 sm:mt-12" data-testid="related-recipes-section">
      <h2
        className="text-xl sm:text-2xl font-light text-[#2C2C2C] mb-3"
        style={{ fontFamily: 'var(--font-heading)' }}
      >
        Related Recipes
      </h2>
      <div className="section-divider mb-6 sm:mb-8" style={{ marginLeft: 0 }}></div>

      {/* Desktop: 4-col grid */}
      <div className="hidden lg:grid grid-cols-4 gap-5" data-testid="related-recipes-grid">
        {related.map((r) => (
          <RecipeCard key={r.slug} recipe={r} variant="editorial" deferFavoriteCheck />
        ))}
      </div>

      {/* Mobile / Tablet: horizontal scroll */}
      <div className="lg:hidden scroll-container -mx-4 px-4" data-testid="related-recipes-scroll">
        {related.map((r) => (
          <div key={r.slug} className="min-w-[260px] max-w-[280px] flex-shrink-0">
            <RecipeCard recipe={r} variant="editorial" deferFavoriteCheck />
          </div>
        ))}
      </div>
    </section>
  );
};

export default RelatedRecipes;
