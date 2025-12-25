"""
Prerender Middleware for FastAPI

This middleware intercepts requests from search engine crawlers and serves
prerendered HTML content, while passing regular user requests through normally.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse
import logging

from services.prerender_service import prerender_service

logger = logging.getLogger(__name__)


class PrerenderMiddleware(BaseHTTPMiddleware):
    """
    Middleware that serves prerendered content to search engine crawlers.
    
    For regular users: passes through to the SPA
    For crawlers: serves prerendered HTML with full content
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        user_agent = request.headers.get('user-agent', '')
        
        # Check if this request should be prerendered
        if prerender_service.should_prerender(path, user_agent):
            logger.info(f"Prerendering request for crawler: {path}")
            
            # Try to get prerendered content from external service
            html_content, status_code = await prerender_service.get_prerendered_content(path)
            
            if html_content and status_code == 200:
                logger.info(f"Serving prerendered content for {path}")
                return HTMLResponse(
                    content=html_content,
                    status_code=200,
                    headers={
                        'X-Prerendered': 'true',
                        'Cache-Control': 'public, max-age=3600'
                    }
                )
            else:
                # Fallback: generate static HTML
                logger.info(f"Prerender service unavailable, using fallback HTML for {path}")
                fallback_html = prerender_service.generate_static_html(path)
                return HTMLResponse(
                    content=fallback_html,
                    status_code=200,
                    headers={
                        'X-Prerendered': 'fallback',
                        'Cache-Control': 'public, max-age=300'
                    }
                )
        
        # Regular request - pass through
        response = await call_next(request)
        return response
