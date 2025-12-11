# AI Service - Legacy service (now replaced by Sous-Chef Linguine GPT)
# This service is kept for backward compatibility with other services

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class AIService:
    """Legacy service - kept for backward compatibility.
    
    NOTE: This service previously used Emergent LLM. 
    It now delegates to Sous-Chef Linguine GPT via OpenAI.
    """
    
    def __init__(self):
        # Check for OpenAI key instead
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment - AI features will be limited")
        
        # Retry configuration
        self.max_attempts = 5
        self.initial_delay = 1  # seconds
        self.backoff_multiplier = 2
    
    async def generate_text(
        self, 
        system_message: str, 
        user_message: str, 
        session_id: str = "default",
        context: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate text using OpenAI."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required but not configured")
        
        # Import and use Sous Chef AI
        from services.sous_chef_ai import sous_chef_ai
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": "gpt-4.1",
                        "input": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ]
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "output" in data and len(data["output"]) > 0:
                    output_content = data["output"][0]
                    if "content" in output_content and len(output_content["content"]) > 0:
                        return output_content["content"][0].get("text", "")
                
                raise ValueError("Unexpected API response format")
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            raise
    
    async def generate_json(
        self, 
        system_message: str, 
        user_message: str, 
        session_id: str = "default",
        context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON response."""
        response_text = await self.generate_text(
            system_message=system_message,
            user_message=user_message,
            session_id=session_id,
            context=context
        )
        
        # Try to extract JSON from response
        try:
            # Clean up the response
            text = response_text.strip()
            
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            raise ValueError(f"AI did not return valid JSON: {str(e)}")

# Global AI service instance
ai_service = AIService()
