import { useQuery } from '@tanstack/react-query';
import { translationAPI, recipeAPI } from '@/utils/api';

/**
 * useRecipe — React Query hook for fetching recipe data.
 * Caches per [slug, lang] with 10-minute staleTime.
 */
export function useRecipe(slug, lang = 'en') {
  return useQuery({
    queryKey: ['recipe', slug, lang],
    queryFn: async () => {
      // Step 1: Try pre-translated content (fast)
      try {
        const translationRes = await translationAPI.getRecipe(slug, lang);
        const td = translationRes.data;

        if (td.status === 'ready' && td.content) {
          return {
            recipe: { ...td.content, ...td.metadata, slug: td.slug },
            contentLanguage: td.lang,
            translationStatus: 'ready',
          };
        }
      } catch {
        // fall through to step 2
      }

      // Step 2: Fetch with on-the-fly translation
      const res = await recipeAPI.getBySlug(slug, lang);
      const data = res.data;
      const displayLang = (data._display_lang || data.content_language || 'en').slice(0, 2).toLowerCase();
      const isMatch = displayLang === lang || data._translated;

      return {
        recipe: data,
        contentLanguage: displayLang,
        translationStatus: isMatch ? 'ready' : 'fallback',
      };
    },
    enabled: !!slug,
  });
}
