"""
Prerender Routes - API endpoints for prerender verification and testing

These routes help verify that prerendering is working correctly.
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from services.prerender_service import prerender_service, CRAWLER_USER_AGENTS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prerender"])


@router.get("/prerender/test/{path:path}")
async def test_prerender(
    path: str,
    request: Request,
    simulate_bot: bool = Query(default=True, description="Simulate a crawler request")
):
    """
    Test endpoint to verify prerendering for a specific path.
    
    Use ?simulate_bot=true to see what Googlebot would receive.
    Use ?simulate_bot=false to see what regular users receive.
    """
    full_path = f"/{path}"
    
    if simulate_bot:
        # Simulate Googlebot
        user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    else:
        user_agent = request.headers.get('user-agent', 'Regular User')
    
    should_prerender = prerender_service.should_prerender(full_path, user_agent)
    is_crawler = prerender_service.is_crawler(user_agent)
    
    result = {
        "path": full_path,
        "user_agent": user_agent[:100],
        "is_crawler": is_crawler,
        "should_prerender": should_prerender,
        "prerender_enabled": prerender_service.enabled,
        "prerender_url": prerender_service.prerender_url,
        "site_url": prerender_service.site_url
    }
    
    if simulate_bot and should_prerender:
        # Try to get prerendered content
        html_content, status_code = await prerender_service.get_prerendered_content(full_path)
        
        if html_content:
            result["prerender_status"] = "success"
            result["content_length"] = len(html_content)
            result["has_h1"] = "<h1" in html_content.lower()
            result["has_json_ld"] = "application/ld+json" in html_content.lower()
            result["has_canonical"] = 'rel="canonical"' in html_content.lower()
            result["has_hreflang"] = "hreflang" in html_content.lower()
        else:
            # Use fallback
            fallback_html = prerender_service.generate_static_html(full_path)
            result["prerender_status"] = "fallback"
            result["fallback_content_length"] = len(fallback_html)
            result["fallback_has_h1"] = "<h1" in fallback_html.lower()
            result["fallback_has_json_ld"] = "application/ld+json" in fallback_html.lower()
    
    return JSONResponse(content=result)


@router.get("/prerender/verify/{path:path}")
async def verify_prerender(path: str):
    """
    Verify that a path would be prerendered correctly.
    Returns the actual HTML that would be served to crawlers.
    """
    full_path = f"/{path}"
    
    # Get prerendered content
    html_content, status_code = await prerender_service.get_prerendered_content(full_path)
    
    if html_content:
        return HTMLResponse(
            content=html_content,
            headers={"X-Prerendered": "true"}
        )
    else:
        # Return fallback HTML
        fallback_html = prerender_service.generate_static_html(full_path)
        return HTMLResponse(
            content=fallback_html,
            headers={"X-Prerendered": "fallback"}
        )


@router.get("/prerender/fallback/{path:path}")
async def get_fallback_html(path: str):
    """
    Get the fallback static HTML for a specific path.
    This is what crawlers would receive if the prerender service is unavailable.
    """
    full_path = f"/{path}"
    fallback_html = prerender_service.generate_static_html(full_path)
    
    return HTMLResponse(
        content=fallback_html,
        headers={
            "X-Prerendered": "fallback",
            "X-Path": full_path
        }
    )


@router.get("/prerender/status")
async def prerender_status():
    """
    Get the current status of the prerender service.
    """
    return {
        "enabled": prerender_service.enabled,
        "prerender_url": prerender_service.prerender_url,
        "site_url": prerender_service.site_url,
        "has_token": bool(prerender_service.prerender_token),
        "crawler_count": len(CRAWLER_USER_AGENTS),
        "sample_crawlers": CRAWLER_USER_AGENTS[:5]
    }


@router.get("/prerender/crawlers")
async def list_crawlers():
    """
    List all known crawler user agents that trigger prerendering.
    """
    return {
        "crawlers": CRAWLER_USER_AGENTS,
        "count": len(CRAWLER_USER_AGENTS)
    }
