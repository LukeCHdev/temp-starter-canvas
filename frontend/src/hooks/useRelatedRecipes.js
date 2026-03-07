import { useQuery } from '@tanstack/react-query';
import { recipeAPI } from '@/utils/api';

/**
 * useRelatedRecipes — fetches and filters related recipes client-side.
 * Priority: same dish_type > same country > same continent.
 * Returns 4–8 recipes, excluding the current recipe.
 */
export function useRelatedRecipes(recipe, lang = 'en') {
  const slug = recipe?.slug;
  const dishType = recipe?.dish_type;
  const country = recipe?.origin_country || recipe?.country;
  const continent = recipe?.continent;

  return useQuery({
    queryKey: ['related-recipes', slug, lang],
    queryFn: async () => {
      const res = await recipeAPI.getFeatured(200, lang, 0);
      const all = (res.data.recipes || []).filter(r => r.slug !== slug);

      // Tier 1: same dish type
      const byDishType = dishType ? all.filter(r => r.dish_type === dishType) : [];
      // Tier 2: same country
      const byCountry = country ? all.filter(r => (r.origin_country || r.country) === country) : [];
      // Tier 3: same continent
      const byContinent = continent ? all.filter(r => r.continent === continent) : [];

      // Merge with dedup, respecting priority order
      const seen = new Set();
      const result = [];

      for (const pool of [byDishType, byCountry, byContinent]) {
        for (const r of pool) {
          if (!seen.has(r.slug)) {
            seen.add(r.slug);
            result.push(r);
          }
          if (result.length >= 8) break;
        }
        if (result.length >= 8) break;
      }

      // If still under 4, pad with random recipes
      if (result.length < 4) {
        for (const r of all) {
          if (!seen.has(r.slug)) {
            seen.add(r.slug);
            result.push(r);
          }
          if (result.length >= 8) break;
        }
      }

      return result.slice(0, 8);
    },
    enabled: !!slug,
  });
}
