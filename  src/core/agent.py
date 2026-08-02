"""
LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow
"""

import asyncio
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, List, Any

from .enums import TaskType, InteractionMode
from .config import Config
from ..extraction.extractor import InformationExtractor
from ..browser.browser_manager import BrowserManager
from ..browser.self_healing import SelfHealingSelector
from ..checkpoint.checkpoint_manager import CheckpointManager
from ..context.context_manager import ContextManager
from ..context.conversation_logger import ConversationLogger
from ..context.project_registry import ProjectRegistry
from ..utils.colors import print_colored, Colors
from ..utils.safe_input import SafeInput


class LugyFlutter:
    """
    🤖 LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow
    """
    
    VERSION = "2.0.0"
    NAME = "LugyFlutter"
    
    def __init__(
        self,
        mode: InteractionMode = InteractionMode.FULL_INTERACTIVE,
        api_key: Optional[str] = None,
        log_dir: str = "logs"
    ):
        # ... (الكود الكامل كما في النسخة السابقة)
        pass
    
    # ... (جميع الدوال)