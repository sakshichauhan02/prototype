import httpx
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("aetheria.openrouter")

class OpenRouterService:
    # A robust list of free and uncensored fallback models in case the primary one fails
    FALLBACK_MODELS = [
        "venice/uncensored",
        "meta-llama/llama-3.1-8b-instruct:free",
        "openrouter/free"
    ]

    @staticmethod
    async def generate_openrouter_reply(
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        model_override: Optional[str] = None
    ) -> Optional[str]:
        """
        Sends conversation history to OpenRouter using configured model or fallbacks.
        Returns the text response, or None if the request failed completely.
        """
        if not settings.OPENROUTER_API_KEY or not settings.OPENROUTER_API_KEY.strip():
            logger.warning("OpenRouter API key is not configured.")
            return None

        # Build candidate model list
        primary_model = model_override or settings.OPENROUTER_MODEL or "cognitivecomputations/dolphin-mixtral-8x7b"
        
        # Ensure model list is unique but keeps order
        models_to_try = [primary_model]
        for fallback in OpenRouterService.FALLBACK_MODELS:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/aetheria-app/aetheria",
            "X-Title": "Aetheria Companion Core Engine",
        }

        for model in models_to_try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1024
            }
            logger.info(f"Attempting OpenRouter completion with model: {model}")
            
            try:
                # Use 15.0 seconds timeout for request handling
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            raw_content = choices[0]["message"].get("content")
                            content = str(raw_content).strip() if raw_content is not None else ""
                            if content:
                                logger.info(f"OpenRouter call succeeded with model: {model}")
                                return content
                        logger.warning(f"OpenRouter model {model} returned 200 OK but empty structure: {data}")
                    else:
                        logger.warning(
                            f"OpenRouter API error (status: {response.status_code}) for model {model}. "
                            f"Response: {response.text}"
                        )
            except httpx.TimeoutException:
                logger.error(f"Timeout occurred calling OpenRouter with model: {model}")
            except Exception as e:
                logger.error(f"Unexpected error calling OpenRouter with model {model}: {e}")

        logger.error("All OpenRouter API model attempts failed.")
        return None

openrouter_service = OpenRouterService()
