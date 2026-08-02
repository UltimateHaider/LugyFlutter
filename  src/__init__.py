"""
LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow
الحزمة الرئيسية
"""

from .core.agent import LugyFlutter
from .core.enums import TaskType, InteractionMode
from .core.config import config
from .utils.colors import Colors, print_colored
from .utils.safe_input import SafeInput

__version__ = "2.0.0"
__author__ = "LugyFlutter Team"
__description__ = "وكيل ذكي لأتمتة وتطوير تطبيقات FlutterFlow"

__all__ = [
    "LugyFlutter",
    "TaskType",
    "InteractionMode",
    "config",
    "Colors",
    "print_colored",
    "SafeInput",
]