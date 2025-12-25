"""
Prerender Service - Serves prerendered HTML to search engine crawlers

This service detects bot/crawler requests and serves prerendered HTML content
from an external prerendering service (Prerender.io or equivalent).

For production, set PRERENDER_TOKEN in your environment.
"""

import os
import httpx
import logging
from typing import Optional, Tuple
import re

logger = logging.getLogger(__name__)

# Known crawler user agents
CRAWLER_USER_AGENTS = [
    'googlebot',
    'bingbot', 
    'yandex',
    'baiduspider',
    'facebookexternalhit',
    'twitterbot',
    'rogerbot',
    'linkedinbot',
    'embedly',
    'quora link preview',
    'showyoubot',
    'outbrain',
    'pinterest',
    'slackbot',
    'vkshare',
    'w3c_validator',
    'redditbot',
    'applebot',
    'whatsapp',
    'flipboard',
    'tumblr',
    'bitlybot',
    'skypeuripreview',
    'nuzzel',
    'discordbot',
    'google page speed',
    'qwantify',
    'pinterestbot',
    'bitrix link preview',
    'xing-contenttabreceiver',
    'chrome-lighthouse',
    'telegrambot',
    'integration testing',  # For our own testing
]

# File extensions to ignore (not HTML pages)
IGNORED_EXTENSIONS = [
    '.js', '.css', '.xml', '.less', '.png', '.jpg', '.jpeg', '.gif', 
    '.pdf', '.doc', '.txt', '.ico', '.rss', '.zip', '.mp3', '.mp4',
    '.rar', '.exe', '.wmv', '.avi', '.ppt', '.tif', '.wav', '.mov',
    '.psd', '.ai', '.xls', '.webp', '.svg', '.woff', '.woff2', '.ttf',
    '.eot', '.json', '.map'
]

# Routes that should be prerendered (public frontend routes)
PUBLIC_ROUTES = [
    r'^/$',
    r'^/(en|es|it|fr|de)/?$',
    r'^/(en|es|it|fr|de)/explore',
    r'^/(en|es|it|fr|de)/recipe/',
    r'^/(en|es|it|fr|de)/about',
    r'^/(en|es|it|fr|de)/techniques',
    r'^/(en|es|it|fr|de)/privacy',
    r'^/(en|es|it|fr|de)/terms',
    r'^/(en|es|it|fr|de)/cookies',
    r'^/(en|es|it|fr|de)/contact',
    r'^/(en|es|it|fr|de)/editorial-policy',
    r'^/(en|es|it|fr|de)/regions',
    r'^/(en|es|it|fr|de)/country/',
    r'^/(en|es|it|fr|de)/for-ai',
]


class PrerenderService:
    """Service to handle prerendering for SEO"""
    
    def __init__(self):
        self.prerender_url = os.getenv('PRERENDER_URL', 'https://service.prerender.io/')
        self.prerender_token = os.getenv('PRERENDER_TOKEN', '')
        self.site_url = os.getenv('SITE_URL', 'https://www.souscheflinguine.com')
        self.enabled = os.getenv('PRERENDER_ENABLED', 'true').lower() == 'true'
        
    def is_crawler(self, user_agent: str) -> bool:
        """Check if the user agent is a known crawler/bot"""
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        
        for crawler in CRAWLER_USER_AGENTS:
            if crawler in user_agent_lower:
                logger.info(f"Detected crawler: {crawler} in {user_agent[:50]}")
                return True
        
        return False
    
    def should_prerender(self, path: str, user_agent: str) -> bool:
        """Determine if the request should be prerendered"""
        if not self.enabled:
            return False
            
        # Don't prerender API routes
        if path.startswith('/api'):
            return False
        
        # Don't prerender admin routes
        if path.startswith('/admin'):
            return False
        
        # Don't prerender static files
        for ext in IGNORED_EXTENSIONS:
            if path.lower().endswith(ext):
                return False
        
        # Check if it's a crawler
        if not self.is_crawler(user_agent):
            return False
        
        # Check if it's a public route that should be prerendered
        for pattern in PUBLIC_ROUTES:
            if re.match(pattern, path):
                return True
        
        # Default: prerender any non-API, non-admin route for crawlers
        return True
    
    async def get_prerendered_content(self, path: str) -> Tuple[Optional[str], int]:
        """
        Fetch prerendered content from the prerender service
        
        Returns:
            Tuple of (html_content, status_code)
        """
        try:
            # Build the full URL to prerender
            full_url = f"{self.site_url.rstrip('/')}{path}"
            prerender_request_url = f"{self.prerender_url.rstrip('/')}/{full_url}"
            
            logger.info(f"Fetching prerendered content for: {full_url}")
            
            headers = {
                'User-Agent': 'Prerender Service',
            }
            
            # Add token if configured
            if self.prerender_token:
                headers['X-Prerender-Token'] = self.prerender_token
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(prerender_request_url, headers=headers)
                
                if response.status_code == 200:
                    html_content = response.text
                    logger.info(f"Successfully fetched prerendered content ({len(html_content)} bytes)")
                    return html_content, 200
                else:
                    logger.warning(f"Prerender service returned status {response.status_code}")
                    return None, response.status_code
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching prerendered content for {path}")
            return None, 504
        except Exception as e:
            logger.error(f"Error fetching prerendered content: {e}")
            return None, 500
    
    def generate_static_html(self, path: str, language: str = 'en') -> str:
        """
        Generate static HTML for SEO when prerender service is unavailable.
        This is a fallback that provides basic SEO content.
        """
        # Extract language from path
        lang_match = re.match(r'^/(en|es|it|fr|de)/', path)
        if lang_match:
            language = lang_match.group(1)
        
        # Determine page type and generate appropriate content
        page_content = self._get_page_content(path, language)
        
        return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_content['title']}</title>
    <meta name="description" content="{page_content['description']}">
    <link rel="canonical" href="{self.site_url}{path}">
    
    <!-- Hreflang tags -->
    <link rel="alternate" hreflang="en" href="{self.site_url}/en{page_content['base_path']}">
    <link rel="alternate" hreflang="es" href="{self.site_url}/es{page_content['base_path']}">
    <link rel="alternate" hreflang="it" href="{self.site_url}/it{page_content['base_path']}">
    <link rel="alternate" hreflang="fr" href="{self.site_url}/fr{page_content['base_path']}">
    <link rel="alternate" hreflang="de" href="{self.site_url}/de{page_content['base_path']}">
    <link rel="alternate" hreflang="x-default" href="{self.site_url}/en{page_content['base_path']}">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {page_content['json_ld']}
    </script>
</head>
<body>
    <header>
        <nav>
            <a href="/{language}/">Sous Chef Linguine</a>
            <a href="/{language}/explore">Explore</a>
            <a href="/{language}/techniques">Techniques</a>
            <a href="/{language}/about">About</a>
        </nav>
    </header>
    
    <main>
        <h1>{page_content['h1']}</h1>
        <p>{page_content['intro']}</p>
        {page_content['body']}
    </main>
    
    <footer>
        <nav>
            <a href="/{language}/privacy">Privacy Policy</a>
            <a href="/{language}/terms">Terms of Service</a>
            <a href="/{language}/cookies">Cookie Policy</a>
            <a href="/{language}/editorial-policy">Editorial Policy</a>
            <a href="/{language}/contact">Contact</a>
        </nav>
        <p>© 2025 Sous Chef Linguine. All rights reserved.</p>
    </footer>
    
    <div id="root"></div>
    <noscript>JavaScript is required for full functionality.</noscript>
</body>
</html>"""

    def _get_page_content(self, path: str, language: str) -> dict:
        """Get page-specific content based on path and language"""
        
        # Default content
        base_path = re.sub(r'^/(en|es|it|fr|de)', '', path) or '/'
        
        # Language-specific titles
        titles = {
            'en': 'Sous Chef Linguine | Authentic Global Recipe Archive',
            'es': 'Sous Chef Linguine | Archivo de Recetas Auténticas Globales',
            'it': 'Sous Chef Linguine | Archivio di Ricette Autentiche Globali',
            'fr': 'Sous Chef Linguine | Archives de Recettes Authentiques du Monde',
            'de': 'Sous Chef Linguine | Authentisches Globales Rezeptarchiv'
        }
        
        descriptions = {
            'en': 'Discover authentic traditional recipes from around the world. Our editorial archive preserves culinary heritage with no adaptation or compromise.',
            'es': 'Descubre recetas tradicionales auténticas de todo el mundo. Nuestro archivo editorial preserva el patrimonio culinario sin adaptación ni compromiso.',
            'it': 'Scopri ricette tradizionali autentiche da tutto il mondo. Il nostro archivio editoriale preserva il patrimonio culinario senza adattamenti o compromessi.',
            'fr': 'Découvrez des recettes traditionnelles authentiques du monde entier. Nos archives éditoriales préservent le patrimoine culinaire sans adaptation ni compromis.',
            'de': 'Entdecken Sie authentische traditionelle Rezepte aus aller Welt. Unser redaktionelles Archiv bewahrt das kulinarische Erbe ohne Anpassung oder Kompromiss.'
        }
        
        h1_texts = {
            'en': 'Authentic Global Recipe Archive',
            'es': 'Archivo de Recetas Auténticas Globales',
            'it': 'Archivio di Ricette Autentiche Globali',
            'fr': 'Archives de Recettes Authentiques du Monde',
            'de': 'Authentisches Globales Rezeptarchiv'
        }
        
        intros = {
            'en': 'An editorial and cultural archive dedicated to preserving and documenting authentic traditional recipes from around the world.',
            'es': 'Un archivo editorial y cultural dedicado a preservar y documentar recetas tradicionales auténticas de todo el mundo.',
            'it': 'Un archivio editoriale e culturale dedicato alla conservazione e documentazione di ricette tradizionali autentiche da tutto il mondo.',
            'fr': 'Une archive éditoriale et culturelle dédiée à la préservation et à la documentation de recettes traditionnelles authentiques du monde entier.',
            'de': 'Ein redaktionelles und kulturelles Archiv, das der Bewahrung und Dokumentation authentischer traditioneller Rezepte aus aller Welt gewidmet ist.'
        }
        
        # Check for explore page
        if '/explore' in path:
            explore_h1 = {
                'en': 'Explore Recipes',
                'es': 'Explorar Recetas',
                'it': 'Esplora Ricette',
                'fr': 'Explorer les Recettes',
                'de': 'Rezepte Entdecken'
            }
            return {
                'title': f"{explore_h1.get(language, explore_h1['en'])} | Sous Chef Linguine",
                'description': descriptions.get(language, descriptions['en']),
                'h1': explore_h1.get(language, explore_h1['en']),
                'intro': f"Browse authentic recipes by region, country, or cuisine.",
                'body': '<section><h2>Browse by Continent</h2><ul><li><a href="/{}/explore/europe">Europe</a></li><li><a href="/{}/explore/americas">Americas</a></li><li><a href="/{}/explore/asia">Asia</a></li><li><a href="/{}/explore/africa">Africa</a></li><li><a href="/{}/explore/oceania">Oceania</a></li></ul></section>'.format(language, language, language, language, language),
                'base_path': '/explore',
                'json_ld': '{"@context":"https://schema.org","@type":"CollectionPage","name":"Explore Recipes","description":"Browse authentic recipes from around the world"}'
            }
        
        # Check for about page
        if '/about' in path:
            about_h1 = {
                'en': 'About Sous Chef Linguine',
                'es': 'Acerca de Sous Chef Linguine',
                'it': 'Chi Siamo - Sous Chef Linguine',
                'fr': 'À Propos de Sous Chef Linguine',
                'de': 'Über Sous Chef Linguine'
            }
            return {
                'title': f"{about_h1.get(language, about_h1['en'])} | Sous Chef Linguine",
                'description': 'Learn about our mission to preserve authentic culinary heritage from around the world.',
                'h1': about_h1.get(language, about_h1['en']),
                'intro': 'Our mission is to preserve and document authentic traditional recipes.',
                'body': '',
                'base_path': '/about',
                'json_ld': '{"@context":"https://schema.org","@type":"AboutPage","name":"About Sous Chef Linguine"}'
            }
        
        # Check for recipe page
        recipe_match = re.search(r'/recipe/([^/]+)', path)
        if recipe_match:
            recipe_slug = recipe_match.group(1)
            return {
                'title': f"Recipe | Sous Chef Linguine",
                'description': f"Authentic traditional recipe - {recipe_slug.replace('-', ' ').title()}",
                'h1': recipe_slug.replace('-', ' ').title(),
                'intro': 'Discover the authentic preparation of this traditional dish.',
                'body': '',
                'base_path': f'/recipe/{recipe_slug}',
                'json_ld': f'{{"@context":"https://schema.org","@type":"Recipe","name":"{recipe_slug.replace("-", " ").title()}"}}'
            }
        
        # Default homepage content
        return {
            'title': titles.get(language, titles['en']),
            'description': descriptions.get(language, descriptions['en']),
            'h1': h1_texts.get(language, h1_texts['en']),
            'intro': intros.get(language, intros['en']),
            'body': f'''<section>
                <h2>Featured Recipes</h2>
                <p>Explore our collection of authentic recipes from around the world.</p>
                <a href="/{language}/explore">Browse All Recipes</a>
            </section>''',
            'base_path': '/',
            'json_ld': f'{{"@context":"https://schema.org","@type":"WebSite","name":"Sous Chef Linguine","url":"{self.site_url}","description":"{descriptions.get(language, descriptions["en"])}"}}'
        }


# Global instance
prerender_service = PrerenderService()
