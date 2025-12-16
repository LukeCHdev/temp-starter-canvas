# Document Import Service for PDF/ODF Recipe Extraction
# Extracts multiple recipes from documents, processes with AI, saves to DB

import logging
import re
import io
import httpx
import pdfplumber
from odf import text as odf_text
from odf.opendocument import load as load_odf
from langdetect import detect, LangDetectException
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Configurable batch size for AI processing
DEFAULT_BATCH_SIZE = 5


class DocumentParser:
    """Parse PDF and ODF documents to extract text."""
    
    @staticmethod
    async def parse_from_url(url: str) -> Tuple[str, str]:
        """Download and parse document from URL.
        
        Returns: (extracted_text, detected_format)
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            content = response.content
            content_type = response.headers.get('content-type', '').lower()
        
        # Detect format
        if 'pdf' in content_type or url.lower().endswith('.pdf'):
            return DocumentParser.parse_pdf(io.BytesIO(content)), 'pdf'
        elif 'opendocument' in content_type or url.lower().endswith('.odt'):
            return DocumentParser.parse_odf(io.BytesIO(content)), 'odf'
        else:
            raise ValueError(f"Unsupported document format: {content_type}")
    
    @staticmethod
    def parse_pdf(file_obj) -> str:
        """Extract text from PDF file."""
        full_text = []
        
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)
        
        return '\n\n'.join(full_text)
    
    @staticmethod
    def parse_odf(file_obj) -> str:
        """Extract text from ODF (ODT) file."""
        doc = load_odf(file_obj)
        paragraphs = []
        
        for element in doc.getElementsByType(odf_text.P):
            text_content = ''.join(
                node.data for node in element.childNodes
                if node.nodeType == node.TEXT_NODE
            )
            if text_content.strip():
                paragraphs.append(text_content.strip())
        
        return '\n\n'.join(paragraphs)
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect the language of the text."""
        try:
            # Use first 1000 chars for detection
            sample = text[:1000]
            lang = detect(sample)
            return lang
        except LangDetectException:
            return 'en'  # Default to English


class RecipeDetector:
    """Detect and split individual recipes from document text."""
    
    # Common recipe title patterns
    RECIPE_PATTERNS = [
        # Numbered recipes: "1. Recipe Name", "Recipe 1:", etc.
        r'^\s*(?:\d+[\.\)\-]?\s*)?(?:Receta|Recipe|Ricetta|Rezept)?\s*:?\s*([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñüÜ\s\-]+)',
        # All caps titles
        r'^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\-]{3,50})$',
        # Bold/prominent titles (often followed by ingredients)
        r'^([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñüÜ\s\-]{3,60})\s*$',
    ]
    
    # Keywords that indicate recipe content
    RECIPE_KEYWORDS = {
        'es': ['ingredientes', 'preparación', 'elaboración', 'modo de preparar', 'procedimiento'],
        'en': ['ingredients', 'instructions', 'preparation', 'method', 'directions'],
        'it': ['ingredienti', 'preparazione', 'procedimento'],
        'fr': ['ingrédients', 'préparation', 'méthode'],
        'de': ['zutaten', 'zubereitung', 'anleitung'],
    }
    
    @staticmethod
    def detect_recipes(text: str, language: str = 'es') -> List[Dict[str, Any]]:
        """Detect and split individual recipes from text.
        
        Returns list of {title, raw_text, start_pos, end_pos}
        """
        recipes = []
        lines = text.split('\n')
        
        # Find potential recipe boundaries
        boundaries = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if this line looks like a recipe title
            is_title = RecipeDetector._is_recipe_title(line_stripped, language)
            if is_title:
                boundaries.append({
                    'line_num': i,
                    'title': RecipeDetector._clean_title(line_stripped),
                    'raw_line': line_stripped
                })
        
        # Extract recipes based on boundaries
        for idx, boundary in enumerate(boundaries):
            start_line = boundary['line_num']
            end_line = boundaries[idx + 1]['line_num'] if idx + 1 < len(boundaries) else len(lines)
            
            # Get raw text for this recipe
            raw_text = '\n'.join(lines[start_line:end_line]).strip()
            
            # Validate it looks like a recipe (has ingredients/instructions)
            if RecipeDetector._looks_like_recipe(raw_text, language):
                recipes.append({
                    'title': boundary['title'],
                    'raw_text': raw_text,
                    'line_start': start_line,
                    'line_end': end_line
                })
        
        # If no recipes detected with boundaries, try alternative detection
        if not recipes:
            recipes = RecipeDetector._fallback_detection(text, language)
        
        return recipes
    
    @staticmethod
    def _is_recipe_title(line: str, language: str) -> bool:
        """Check if a line looks like a recipe title."""
        # Too short or too long
        if len(line) < 3 or len(line) > 80:
            return False
        
        # Check for recipe keywords in the line (not a title)
        keywords = RecipeDetector.RECIPE_KEYWORDS.get(language, RecipeDetector.RECIPE_KEYWORDS['en'])
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            return False
        
        # Check patterns
        for pattern in RecipeDetector.RECIPE_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE | re.MULTILINE):
                return True
        
        # Check if it's a title-case line (likely a heading)
        words = line.split()
        if len(words) >= 1 and len(words) <= 8:
            # Most words start with capital or are short connectors
            caps_count = sum(1 for w in words if w[0].isupper() or len(w) <= 3)
            if caps_count >= len(words) * 0.6:
                return True
        
        return False
    
    @staticmethod
    def _clean_title(title: str) -> str:
        """Clean up a recipe title."""
        # Remove numbering
        title = re.sub(r'^\s*\d+[\.\)\-]?\s*', '', title)
        # Remove "Receta:", "Recipe:", etc.
        title = re.sub(r'^(?:Receta|Recipe|Ricetta|Rezept)\s*:?\s*', '', title, flags=re.IGNORECASE)
        return title.strip()
    
    @staticmethod
    def _looks_like_recipe(text: str, language: str) -> bool:
        """Check if text block looks like a recipe."""
        text_lower = text.lower()
        keywords = RecipeDetector.RECIPE_KEYWORDS.get(language, RecipeDetector.RECIPE_KEYWORDS['en'])
        
        # Must contain at least one recipe keyword
        has_keyword = any(kw in text_lower for kw in keywords)
        
        # Must have reasonable length
        has_content = len(text) > 100
        
        return has_keyword and has_content
    
    @staticmethod
    def _fallback_detection(text: str, language: str) -> List[Dict[str, Any]]:
        """Fallback recipe detection when boundary detection fails."""
        recipes = []
        
        # Try splitting by double newlines and looking for recipe blocks
        blocks = re.split(r'\n\s*\n\s*\n', text)
        
        for i, block in enumerate(blocks):
            block = block.strip()
            if RecipeDetector._looks_like_recipe(block, language):
                # Try to extract title from first line
                lines = block.split('\n')
                title = lines[0].strip() if lines else f"Recipe {i+1}"
                title = RecipeDetector._clean_title(title)
                
                recipes.append({
                    'title': title,
                    'raw_text': block,
                    'line_start': 0,
                    'line_end': 0
                })
        
        return recipes


class ImportSession:
    """Manages a document import session with pause/resume capability."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid4())
        self.status = 'pending'  # pending, parsing, processing, completed, paused, error
        self.document_url = None
        self.document_language = 'en'
        self.total_recipes = 0
        self.processed_count = 0
        self.saved_count = 0
        self.skipped_count = 0
        self.duplicate_count = 0
        self.recipes = []  # List of recipe data with status
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage."""
        return {
            'session_id': self.session_id,
            'status': self.status,
            'document_url': self.document_url,
            'document_language': self.document_language,
            'total_recipes': self.total_recipes,
            'processed_count': self.processed_count,
            'saved_count': self.saved_count,
            'skipped_count': self.skipped_count,
            'duplicate_count': self.duplicate_count,
            'recipes': self.recipes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'error_message': self.error_message
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ImportSession':
        """Create session from dictionary."""
        session = ImportSession(session_id=data['session_id'])
        session.status = data.get('status', 'pending')
        session.document_url = data.get('document_url')
        session.document_language = data.get('document_language', 'en')
        session.total_recipes = data.get('total_recipes', 0)
        session.processed_count = data.get('processed_count', 0)
        session.saved_count = data.get('saved_count', 0)
        session.skipped_count = data.get('skipped_count', 0)
        session.duplicate_count = data.get('duplicate_count', 0)
        session.recipes = data.get('recipes', [])
        session.created_at = data.get('created_at')
        session.updated_at = data.get('updated_at')
        session.error_message = data.get('error_message')
        return session


# AI Prompt for recipe reorganization and expansion
DOCUMENT_RECIPE_PROMPT = """You are Sous-Chef Linguine, an expert in authentic global recipes.

You are given RAW TEXT extracted from a document containing a recipe. Your task is to:
1. REORGANIZE the information into the canonical recipe schema
2. EXPAND missing sections with culturally accurate information
3. PRESERVE the original recipe identity - do NOT change the dish

IMPORTANT:
- The document is in {language} language
- The recipe is from {country} (infer region if possible)
- Keep the recipe's cultural authenticity
- Do NOT invent a different dish

RAW RECIPE TEXT:
---
{raw_text}
---

You MUST return ONLY valid JSON matching this EXACT structure:

{{
  "recipe_name": "string - the dish name in its ORIGINAL language",
  "origin_country": "{country}",
  "origin_region": "string - specific region if identifiable",
  "origin_language": "{language_code}",
  "authenticity_level": 2,
  "history_summary": "string - brief history of the dish (expand if not in source)",
  "characteristic_profile": "string - taste and texture description",
  "no_no_rules": ["string - what NOT to do when making this dish"],
  "special_techniques": ["string - traditional cooking techniques"],
  "technique_links": [
    {{"technique": "technique name", "url": "", "description": "what this technique involves"}}
  ],
  "ingredients": [
    {{"item": "ingredient name", "amount": "quantity", "unit": "g/ml/tbsp/etc", "notes": "optional preparation notes"}}
  ],
  "instructions": ["Step 1...", "Step 2..."],
  "wine_pairing": {{
    "recommended_wines": [
      {{"name": "wine name", "region": "wine region", "reason": "why it pairs well"}}
    ],
    "notes": "general pairing notes"
  }}
}}

RULES:
- Return ONLY the JSON object, no markdown, no explanations
- Expand history_summary and characteristic_profile if not in source
- Add at least 2 no_no_rules based on traditional preparation
- Add special_techniques if the recipe involves any
- Wine pairing should be regionally appropriate
- authenticity_level: 2 (Traditional) for document-sourced recipes"""


async def process_recipe_with_ai(
    raw_text: str,
    title: str,
    language: str,
    country: str,
    ai_service
) -> Dict[str, Any]:
    """Process a single recipe with Sous-Chef AI.
    
    Args:
        raw_text: Raw extracted text for the recipe
        title: Detected title
        language: Document language (e.g., 'es')
        country: Origin country (e.g., 'Chile')
        ai_service: The Sous-Chef AI service instance
    
    Returns:
        Canonical recipe JSON
    """
    # Map language code to full name for the prompt
    language_names = {
        'es': 'Spanish', 'en': 'English', 'it': 'Italian',
        'fr': 'French', 'de': 'German', 'pt': 'Portuguese',
        'ja': 'Japanese', 'zh': 'Chinese', 'ko': 'Korean'
    }
    language_name = language_names.get(language, 'Spanish')
    
    prompt = DOCUMENT_RECIPE_PROMPT.format(
        language=language_name,
        country=country,
        raw_text=raw_text[:4000],  # Limit text length
        language_code=language
    )
    
    # Use the existing AI service
    try:
        recipe_json = await ai_service.generate_recipe(prompt)
        
        # Ensure the title matches if AI didn't capture it well
        if recipe_json and not recipe_json.get('recipe_name'):
            recipe_json['recipe_name'] = title
        
        return recipe_json
    except Exception as e:
        logger.error(f"AI processing failed for '{title}': {str(e)}")
        raise


# Export classes and functions
__all__ = [
    'DocumentParser',
    'RecipeDetector', 
    'ImportSession',
    'process_recipe_with_ai',
    'DEFAULT_BATCH_SIZE'
]
