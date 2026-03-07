/**
 * Safe ingredient amount parser + formatter for client-side display.
 * Handles: "380", "1/2", "1 1/2", "2-3", "to taste", "½", "1.5"
 * Never crashes. Non-numeric strings pass through unchanged.
 */

const UNICODE_FRACTIONS = {
  '½': 0.5, '⅓': 1/3, '⅔': 2/3, '¼': 0.25, '¾': 0.75,
  '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8, '⅙': 1/6,
  '⅚': 5/6, '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875,
};

const NON_SCALABLE = ['to taste', 'pinch', 'dash', 'as needed', 'optional', 'some', 'few', 'q.b.', 'qb', 'a piacere'];

/**
 * Parse an amount string to a number. Returns null for non-numeric.
 */
export function parseAmount(raw) {
  if (!raw) return null;
  const s = String(raw).trim();
  if (!s) return null;

  // Non-scalable keywords
  const lower = s.toLowerCase();
  if (NON_SCALABLE.some(kw => lower.includes(kw))) return null;

  // Direct number
  const direct = Number(s);
  if (!isNaN(direct) && s !== '') return direct;

  // Unicode fraction: "½", "1½"
  for (const [char, val] of Object.entries(UNICODE_FRACTIONS)) {
    if (s.includes(char)) {
      const prefix = s.replace(char, '').trim();
      const whole = prefix ? Number(prefix) : 0;
      if (!isNaN(whole)) return whole + val;
    }
  }

  // Simple fraction: "1/2", "3/4"
  const fracMatch = s.match(/^(\d+)\s*\/\s*(\d+)$/);
  if (fracMatch) {
    const d = Number(fracMatch[2]);
    return d !== 0 ? Number(fracMatch[1]) / d : null;
  }

  // Mixed number: "1 1/2", "2 3/4"
  const mixedMatch = s.match(/^(\d+)\s+(\d+)\s*\/\s*(\d+)$/);
  if (mixedMatch) {
    const d = Number(mixedMatch[3]);
    return d !== 0 ? Number(mixedMatch[1]) + Number(mixedMatch[2]) / d : null;
  }

  // Range: "2-3" — not scalable, return null (keep original)
  if (/^\d+(\.\d+)?\s*-\s*\d+(\.\d+)?$/.test(s)) return null;

  // Leading number: "2 large"
  const leading = s.match(/^(\d+(?:\.\d+)?)/);
  if (leading) return Number(leading[1]);

  return null;
}

/**
 * Format a scaled number back to a readable string.
 */
export function formatAmount(value) {
  if (value == null) return '';
  if (value === Math.floor(value)) return String(Math.floor(value));

  const NICE = { 0.25: '1/4', 0.33: '1/3', 0.5: '1/2', 0.67: '2/3', 0.75: '3/4' };
  const whole = Math.floor(value);
  const dec = +(value - whole).toFixed(2);

  for (const [fv, fs] of Object.entries(NICE)) {
    if (Math.abs(dec - Number(fv)) < 0.05) {
      return whole === 0 ? fs : `${whole} ${fs}`;
    }
  }
  return value < 1 ? String(+value.toFixed(2)) : String(+value.toFixed(1));
}

/**
 * Scale a single ingredient object { item, amount, unit, notes }.
 * Returns new object with scaled amount (or original if non-scalable).
 */
export function scaleIngredient(ingredient, scaleFactor) {
  const ing = { ...ingredient };
  const parsed = parseAmount(ing.amount);

  if (parsed !== null && scaleFactor !== 1) {
    ing.amount = formatAmount(parsed * scaleFactor);
    ing._scaled = true;
  } else {
    ing._scaled = false;
  }
  return ing;
}

/**
 * Scale a list of ingredients by a factor.
 */
export function scaleIngredients(ingredients, scaleFactor) {
  if (!Array.isArray(ingredients)) return [];
  return ingredients.map(ing => scaleIngredient(ing, scaleFactor));
}
