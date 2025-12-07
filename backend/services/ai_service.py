# AI Service using Emergent LLM

import os
import json
import logging
from typing import Dict, Any, Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with Emergent LLM."""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
    
    async def generate_text(self, system_message: str, user_message: str, session_id: str = "default") -> str:
        """Generate text using Emergent LLM."""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_message
            )
            
            # Use gpt-5.1 as default
            chat.with_model("openai", "gpt-5.1")
            
            message = UserMessage(text=user_message)
            response = await chat.send_message(message)
            
            return response
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            raise
    
    async def generate_json(self, system_message: str, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """Generate structured JSON response."""
        response_text = await self.generate_text(system_message, user_message, session_id)
        
        # Try to extract JSON from response
        try:
            # Look for JSON in code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
            else:
                # Try to parse entire response as JSON
                return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"AI did not return valid JSON: {str(e)}")

# Global AI service instance
ai_service = AIService()
