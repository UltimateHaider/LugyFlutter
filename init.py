"""
LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow
"""

__version__ = "2.0.0"
__author__ = "LugyFlutter Team"
__description__ = "وكيل ذكي لأتمتة وتطوير تطبيقات FlutterFlow"

from .src.core.agent import LugyFlutter
from .src.core.enums import TaskType, InteractionMode

__all__ = [
    "LugyFlutter",
    "TaskType",
    "InteractionMode",
]