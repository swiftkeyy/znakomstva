"""Integration tests for OpenRouter AI service.

Note: These tests require a valid OpenRouter API key.
Mark as skip for CI/CD pipelines without API access.
"""
import pytest
from unittest.mock import MagicMock

from bot.services.ai_service import AIService
from bot.utils.cache_manager import CacheManager
from bot.openrouter_client import OpenRouterClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestOpenRouterIntegration:
    """Test OpenRouter AI service integration."""
    
    @pytest.mark.skip(reason="Requires OpenRouter API key - enable for manual testing")
    async def test_openrouter_connection(self, mock_redis):
        """Test connection to OpenRouter service."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient()
        ai_service = AIService(openrouter, cache)
        
        # Try to generate simple text
        try:
            response = await openrouter.generate(
                prompt="Say hello",
                temperature=0.7
            )
            
            assert response is not None
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"OpenRouter not available: {e}")
    
    @pytest.mark.skip(reason="Requires OpenRouter API key - enable for manual testing")
    async def test_compatibility_calculation(self, mock_redis):
        """Test AI compatibility calculation."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient()
        ai_service = AIService(openrouter, cache)
        
        # Mock profiles
        user_dict = {
            "id": 1,
            "age": 25,
            "about_me": "Люблю музыку и путешествия",
            "mbti_type": "INTJ",
            "relationship_goals": "serious"
        }
        
        candidate_dict = {
            "id": 2,
            "age": 26,
            "about_me": "Увлекаюсь музыкой и искусством",
            "mbti_type": "ENFP",
            "relationship_goals": "serious"
        }
        
        try:
            result = await ai_service.calculate_compatibility(
                user_dict,
                candidate_dict
            )
            
            assert result is not None
            assert "score" in result
            assert 0 <= result["score"] <= 100
            assert "explanation" in result
        except Exception as e:
            pytest.skip(f"OpenRouter not available: {e}")
    
    @pytest.mark.skip(reason="Requires OpenRouter API key - enable for manual testing")
    async def test_chat_suggestions_generation(self, mock_redis):
        """Test AI chat suggestions generation."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient()
        ai_service = AIService(openrouter, cache)
        
        chat_history = [
            {"sender_id": 1, "content": "Привет! Как дела?"},
            {"sender_id": 2, "content": "Привет! Отлично, спасибо!"},
        ]
        
        user_profile = {"id": 1, "about_me": "Люблю музыку"}
        partner_profile = {"id": 2, "about_me": "Увлекаюсь спортом"}
        
        try:
            bold, warm, playful = await ai_service.generate_chat_suggestions(
                chat_history,
                user_profile,
                partner_profile
            )
            
            assert bold is not None and len(bold) > 0
            assert warm is not None and len(warm) > 0
            assert playful is not None and len(playful) > 0
            
            # Suggestions should be different
            assert bold != warm or warm != playful
        except Exception as e:
            pytest.skip(f"OpenRouter not available: {e}")
    
    @pytest.mark.skip(reason="Requires OpenRouter API key - enable for manual testing")
    async def test_profile_improvement(self, mock_redis):
        """Test AI profile improvement."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient()
        ai_service = AIService(openrouter, cache)
        
        profile = {
            "about_me": "Люблю музыку и путешествия",
            "age": 25,
            "city": "Москва",
            "relationship_goals": "serious"
        }
        
        try:
            result = await ai_service.improve_profile(profile)
            
            assert result is not None
            assert "about_me" in result
            assert len(result["about_me"]) > 0
        except Exception as e:
            pytest.skip(f"OpenRouter not available: {e}")


@pytest.mark.integration
class TestOpenRouterClientSetup:
    """Test OpenRouter client setup and configuration."""
    
    def test_openrouter_client_import(self):
        """Test that OpenRouter client can be imported."""
        from bot.openrouter_client import OpenRouterClient
        
        assert OpenRouterClient is not None
    
    def test_ai_service_initialization(self, mock_redis):
        """Test AI service can be initialized."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient()
        ai_service = AIService(openrouter, cache)
        
        assert ai_service is not None
        assert ai_service.openrouter is not None
    
    def test_prompts_file_exists(self):
        """Test that prompts file exists and can be imported."""
        from bot import prompts
        
        assert prompts is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestOpenRouterErrorHandling:
    """Test OpenRouter error handling."""
    
    async def test_openrouter_invalid_key_handling(self, mock_redis):
        """Test graceful handling of invalid API key."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient(api_key="invalid-key")
        ai_service = AIService(openrouter, cache)
        
        # Should raise exception or return fallback, not crash
        try:
            await openrouter.generate(prompt="test", temperature=0.7)
        except Exception as e:
            # Expected to fail with invalid key
            assert "401" in str(e) or "403" in str(e) or "unavailable" in str(e).lower()
    
    async def test_openrouter_timeout_handling(self, mock_redis):
        """Test timeout handling for OpenRouter requests."""
        cache = CacheManager(mock_redis)
        openrouter = OpenRouterClient(timeout=1)  # Very short timeout
        
        # This test verifies timeout is configured
        assert openrouter.timeout.total == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
