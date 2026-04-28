"""Unit tests for keyboard builders."""
import pytest
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.swipe import swipe_keyboard
from bot.keyboards.settings import settings_keyboard
from bot.keyboards.premium import premium_keyboard


@pytest.mark.unit
class TestMainMenuKeyboard:
    """Test main menu keyboard builder."""
    
    def test_main_menu_keyboard_free_user(self):
        """Test main menu keyboard for free user."""
        keyboard = main_menu_keyboard(is_premium=False)
        
        assert isinstance(keyboard, ReplyKeyboardMarkup)
        assert keyboard.resize_keyboard is True
        
        # Check that keyboard has buttons
        assert len(keyboard.keyboard) > 0
        
        # Flatten all buttons
        all_buttons = [btn.text for row in keyboard.keyboard for btn in row]
        
        # Check essential buttons exist
        assert any("Поиск" in btn or "❤️" in btn for btn in all_buttons)
        assert any("Профиль" in btn or "👤" in btn for btn in all_buttons)
        assert any("Настройки" in btn or "⚙️" in btn for btn in all_buttons)
    
    def test_main_menu_keyboard_premium_user(self):
        """Test main menu keyboard for premium user."""
        keyboard = main_menu_keyboard(is_premium=True)
        
        assert isinstance(keyboard, ReplyKeyboardMarkup)
        
        all_buttons = [btn.text for row in keyboard.keyboard for btn in row]
        
        # Premium users should have all buttons
        assert len(all_buttons) >= 5


@pytest.mark.unit
class TestSwipeKeyboard:
    """Test swipe keyboard builder."""
    
    def test_swipe_keyboard_basic(self):
        """Test basic swipe keyboard."""
        keyboard = swipe_keyboard()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Flatten all buttons
        all_buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]
        
        # Check essential swipe buttons
        assert any("❤️" in btn or "Лайк" in btn for btn in all_buttons)
        assert any("❌" in btn or "Пропустить" in btn for btn in all_buttons)
        assert any("⭐" in btn or "SuperSwipe" in btn for btn in all_buttons)


@pytest.mark.unit
class TestSettingsKeyboard:
    """Test settings keyboard builder."""
    
    def test_settings_keyboard_reports_enabled(self):
        """Test settings keyboard with daily reports enabled."""
        keyboard = settings_keyboard(daily_report_enabled=True)
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Check that keyboard has buttons
        assert len(keyboard.inline_keyboard) > 0
    
    def test_settings_keyboard_reports_disabled(self):
        """Test settings keyboard with daily reports disabled."""
        keyboard = settings_keyboard(daily_report_enabled=False)
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0


@pytest.mark.unit
class TestPremiumKeyboard:
    """Test premium keyboard builder."""
    
    def test_premium_keyboard(self):
        """Test premium subscription keyboard."""
        keyboard = premium_keyboard()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Flatten all buttons
        all_buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]
        
        # Check that there are subscription options
        assert len(all_buttons) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
