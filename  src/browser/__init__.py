"""
LugyFlutter - إدارة المتصفح ونظام الشفاء الذاتي
"""

from .browser_manager import BrowserManager
from .self_healing import SelfHealingSelector
from .vision_fallback import VisionFallback
from .selectors import SelectorManager

__all__ = [
    "BrowserManager",
    "SelfHealingSelector",
    "VisionFallback",
    "SelectorManager",
]