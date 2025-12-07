# AI Service using Emergent LLM with Retry Logic

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with Emergent LLM with robust retry logic."""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
        
        # Retry configuration
        self.max_attempts = 5
        self.initial_delay = 1  # seconds
        self.backoff_multiplier = 2
    
    async def _call_llm_with_retry(
        self, 
        system_message: str, 
        user_message: str, 
        session_id: str,
        context: Optional[Dict[str, str]] = None
    ) -> str:
        """Call LLM with exponential backoff retry logic."""
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"LLM call attempt {attempt}/{self.max_attempts}")
                if context:
                    logger.info(f"Context: {context}")
                
                chat = LlmChat(
                    api_key=self.api_key,
                    session_id=session_id,
                    system_message=system_message
                )
                
                # Use gpt-5.1 as default
                chat.with_model("openai", "gpt-5.1")
                
                message = UserMessage(text=user_message)
                response = await chat.send_message(message)
                
                # Validate response is not empty
                if not response or len(response.strip()) == 0:
                    raise ValueError("Empty response from LLM")
                
                logger.info(f"✓ LLM call succeeded on attempt {attempt}")
                return response
                
            except Exception as e:
                last_exception = e
                exception_type = type(e).__name__
                
                # Log failure with context
                log_data = {
                    "attempt": attempt,
                    "max_attempts": self.max_attempts,
                    "exception_type": exception_type,
                    "exception_message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
                if context:
                    log_data.update(context)
                
                logger.warning(f"LLM call failed: {json.dumps(log_data)}")
                
                # Check if we should retry
                should_retry = (
                    "502" in str(e) or 
                    "BadGateway" in exception_type or
                    "timeout" in str(e).lower() or
                    "Empty response" in str(e) or
                    "Model" in str(e)
                )
                
                if not should_retry or attempt >= self.max_attempts:
                    logger.error(f"✗ LLM call ABORTED after {attempt} attempts")
                    raise last_exception
                
                # Wait before retry with exponential backoff
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= self.backoff_multiplier
        
        # Should never reach here, but just in case
        raise last_exception
    
    async def generate_text(
        self, 
        system_message: str, 
        user_message: str, 
        session_id: str = "default",
        context: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate text using Emergent LLM with retry logic."""
        return await self._call_llm_with_retry(
            system_message=system_message,
            user_message=user_message,
            session_id=session_id,
            context=context
        )
    
    async def generate_json(
        self, 
        system_message: str, 
        user_message: str, 
        session_id: str = "default",
        context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON response with retry logic."""
        response_text = await self.generate_text(
            system_message=system_message,
            user_message=user_message,
            session_id=session_id,
            context=context
        )
        
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
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"AI did not return valid JSON: {str(e)}")

# Global AI service instance
ai_service = AIService()
