"""
LugyFlutter - إدارة الإعدادات من .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """إدارة الإعدادات من .env مع قيم افتراضية"""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """تحميل الإعدادات من .env"""
        if self._loaded:
            return
        
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
        else:
            self._create_default_env(env_file)
            load_dotenv(env_file)
        
        # قراءة الإعدادات
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.CHROME_USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR", "")
        self.BROWSER_HEADLESS = self._get_bool("BROWSER_HEADLESS", False)
        self.BROWSER_TIMEOUT = self._get_int("BROWSER_TIMEOUT", 30)
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.MAX_STEPS = self._get_int("MAX_STEPS", 30)
        self.RETRY_DELAY = self._get_int("RETRY_DELAY", 3)
        self.SAVE_SCREENSHOTS = self._get_bool("SAVE_SCREENSHOTS", True)
        
        # إعدادات الويب
        self.WEB_DASHBOARD_ENABLED = self._get_bool("WEB_DASHBOARD_ENABLED", True)
        self.WEB_DASHBOARD_PORT = self._get_int("WEB_DASHBOARD_PORT", 8501)
        self.API_ENABLED = self._get_bool("API_ENABLED", False)
        self.API_PORT = self._get_int("API_PORT", 8000)
        
        # إعدادات متقدمة
        self.AUTO_HEALING_ENABLED = self._get_bool("AUTO_HEALING_ENABLED", True)
        self.VISION_FALLBACK_ENABLED = self._get_bool("VISION_FALLBACK_ENABLED", True)
        self.CONTEXT_MEMORY_SIZE = self._get_int("CONTEXT_MEMORY_SIZE", 100)
        self.MAX_CHECKPOINTS = self._get_int("MAX_CHECKPOINTS", 20)
        
        self._loaded = True
    
    def _create_default_env(self, env_file: Path):
        """إنشاء ملف .env افتراضي"""
        default_content = """
# LugyFlutter - ملف الإعدادات
# =============================

# إعدادات Google Gemini API
GOOGLE_API_KEY=your_api_key_here

# إعدادات المتصفح
CHROME_USER_DATA_DIR=
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30

# إعدادات LugyFlutter
LOG_LEVEL=INFO
MAX_STEPS=30
RETRY_DELAY=3
SAVE_SCREENSHOTS=true

# إعدادات الويب
WEB_DASHBOARD_ENABLED=true
WEB_DASHBOARD_PORT=8501
API_ENABLED=false
API_PORT=8000

# إعدادات متقدمة
AUTO_HEALING_ENABLED=true
VISION_FALLBACK_ENABLED=true
CONTEXT_MEMORY_SIZE=100
MAX_CHECKPOINTS=20
"""
        env_file.write_text(default_content.strip(), encoding='utf-8')
        print_colored(f"✅ تم إنشاء ملف .env افتراضي في {env_file}", Colors.GREEN)
    
    @staticmethod
    def _get_bool(key: str, default: bool) -> bool:
        value = os.getenv(key, str(default)).lower()
        return value in ["true", "1", "yes", "y"]
    
    @staticmethod
    def _get_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default


# إنشاء كائن مفرد (Singleton)
config = Config()