"""AI service integrating Groq for all AI-powered features."""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import structlog

from bot.groq_client import GroqClient
from bot.prompts import (
    chat_suggestions_prompt,
    compatibility_prompt,
    daily_tip_prompt,
    improve_profile_prompt,
    moderation_text_prompt,
)
from bot.utils.cache_manager import CacheManager

logger = structlog.get_logger(__name__)


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from Ollama response."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Try to extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


class AIService:
    def __init__(self, groq: GroqClient, cache: CacheManager) -> None:
        self.groq = groq
        self.cache = cache

    def _ai_available(self) -> bool:
        return bool(self.groq.api_key)

    async def calculate_compatibility(self, user: dict, candidate: dict) -> Dict[str, Any]:
        """Calculate compatibility score (0-100) between two profiles."""
        if not self._ai_available():
            return {"score": 75, "explanation": "AI анализ недоступен", "key_factors": []}

        cache_key = f"compat:{user.get('id')}:{candidate.get('id')}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Short prompt to avoid 400 errors
        prompt = (
            f"Оцени совместимость двух людей для знакомств (0-100).\n"
            f"Человек 1: возраст {user.get('age')}, цели: {user.get('relationship_goals') or 'не указаны'}, о себе: {str(user.get('about_me') or '')[:200]}\n"
            f"Человек 2: возраст {candidate.get('age')}, цели: {candidate.get('relationship_goals') or 'не указаны'}, о себе: {str(candidate.get('about_me') or '')[:200]}\n"
            f"Ответь в JSON: {{\"score\": число, \"explanation\": \"текст\", \"key_factors\": []}}"
        )
        try:
            response = await self.groq.generate(prompt, temperature=0.3, max_tokens=200)
            result = _parse_json(response) or {"score": 50, "explanation": "Анализ недоступен", "key_factors": []}
        except Exception as e:
            logger.error("compatibility_error", error=str(e))
            result = {"score": 50, "explanation": "AI временно недоступен", "key_factors": []}

        await self.cache.set(cache_key, result, ttl=86400)
        return result

    async def improve_profile(self, profile: dict) -> Dict[str, Any]:
        """Rewrite 'about me' and suggest tags using AI."""
        if not self._ai_available():
            return {"about_me": profile.get("about_me", ""), "suggested_tags": []}
        about_me = profile.get("about_me") or ""
        if not about_me.strip():
            return {"about_me": "", "suggested_tags": []}
        # Simple focused prompt to avoid 400 errors
        prompt = (
            f"Улучши текст 'О себе' для приложения знакомств. "
            f"Сделай его привлекательным и живым. "
            f"Текущий текст: {about_me[:500]}\n\n"
            f"Ответь в JSON: {{\"about_me\": \"улучшенный текст\", \"suggested_tags\": [\"тег1\", \"тег2\"]}}"
        )
        try:
            response = await self.groq.generate(prompt, temperature=0.7, max_tokens=300)
            result = _parse_json(response)
            if result:
                return result
        except Exception as e:
            logger.error("improve_profile_error", error=str(e))
        return {"about_me": about_me, "suggested_tags": []}

    async def generate_icebreakers(self, profile: dict, target_profile: dict) -> List[Dict[str, str]]:
        """Generate 5 icebreaker messages for starting a conversation."""
        prompt = icebreakers_prompt(profile, target_profile)
        try:
            response = await self.groq.generate(prompt, temperature=0.8)
            result = _parse_json(response)
            if result and "icebreakers" in result:
                return result["icebreakers"]
        except Exception as e:
            logger.error("icebreakers_error", error=str(e))
        return [{"style": "тёплый", "text": "Привет! Расскажи мне что-нибудь интересное о себе 😊"}]

    async def generate_chat_suggestions(
        self, chat_history: list, user_profile: dict, partner_profile: dict
    ) -> Tuple[str, str, str]:
        """Generate 3 response variants: bold, warm, playful."""
        prompt = chat_suggestions_prompt(chat_history, user_profile, partner_profile)
        try:
            response = await self.groq.generate(prompt, temperature=0.8)
            result = _parse_json(response)
            if result:
                return result.get("bold", ""), result.get("warm", ""), result.get("playful", "")
        except Exception as e:
            logger.error("chat_suggestions_error", error=str(e))
        return "Интересно! Расскажи подробнее 😏", "Это звучит здорово! Хочу узнать больше ❤️", "Хм, подозрительно... 😄"

    async def moderate_text(self, text: str) -> Dict[str, Any]:
        """Check if text message is appropriate."""
        prompt = moderation_text_prompt(text)
        try:
            response = await self.groq.generate(prompt, temperature=0.1)
            result = _parse_json(response)
            if result:
                return result
        except Exception as e:
            logger.error("moderate_text_error", error=str(e))
        return {"appropriate": True, "reason": None, "severity": None}

    async def moderate_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Check if image is appropriate for dating app."""
        prompt = moderation_image_prompt()
        try:
            response = await self.groq.generate_vision(prompt, image_bytes)
            result = _parse_json(response)
            if result:
                return result
        except Exception as e:
            logger.error("moderate_image_error", error=str(e))
        return {"has_face": True, "appropriate": True, "age_range": None, "concerns": []}

    async def verify_circle_gesture(self, image_bytes: bytes) -> Dict[str, Any]:
        """Check if person in image makes a circle gesture."""
        prompt = circle_gesture_prompt()
        try:
            response = await self.groq.generate_vision(prompt, image_bytes)
            result = _parse_json(response)
            if result:
                return result
        except Exception as e:
            logger.error("verify_circle_error", error=str(e))
        return {"has_person": False, "has_circle_gesture": False, "face_visible": False}

    async def verify_face_match(self, profile_image: bytes, verification_image: bytes) -> Dict[str, Any]:
        """Compare faces between profile photo and verification photo."""
        prompt = face_verification_prompt()
        try:
            # Use verification image for analysis
            response = await self.groq.generate_vision(prompt, verification_image)
            result = _parse_json(response)
            if result:
                return result
        except Exception as e:
            logger.error("face_match_error", error=str(e))
        return {"match": False, "confidence": 0, "reasoning": "Ошибка анализа"}

    async def deep_search(self, user_profile: dict, candidates: list) -> List[Dict[str, Any]]:
        """Find top-10 most compatible profiles using reasoning."""
        prompt = deep_search_prompt(user_profile, candidates)
        try:
            response = await self.groq.generate_reasoning(prompt)
            result = _parse_json(response)
            if result and "top_matches" in result:
                return result["top_matches"]
        except Exception as e:
            logger.error("deep_search_error", error=str(e))
        return []

    async def generate_daily_tip(self, user_stats: dict, profile: dict) -> Dict[str, str]:
        """Generate personalized daily tip for improving profile performance."""
        prompt = daily_tip_prompt(user_stats, profile)
        try:
            response = await self.groq.generate(prompt, temperature=0.6)
            result = _parse_json(response)
            if result:
                return result
        except Exception as e:
            logger.error("daily_tip_error", error=str(e))
        return {"tip": "Добавьте больше фото в профиль!", "action": "Загрузите 2-3 новых фото"}

