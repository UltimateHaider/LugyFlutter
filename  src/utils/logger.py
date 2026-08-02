"""
LugyFlutter - نظام التسجيل المتقدم (Logger)
إدارة السجلات مع دعم متعدد المستويات والتنسيقات
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .colors import Colors, print_colored


class LoggerManager:
    """
    مدير التسجيل المتقدم لـ LugyFlutter
    الميزات:
    - مستويات تسجيل متعددة (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - تسجيل في ملفات مع تدوير تلقائي
    - تسجيل ملون في المحطة الطرفية
    - تتبع الوقت والموقع
    - تصدير السجلات بتنسيقات مختلفة
    - تصفية السجلات حسب المستوى
    - دعم سياقات متعددة
    """
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    _log_dir: Path = Path("logs")
    
    # مستويات التسجيل
    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # ألوان المستويات
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED
    }
    
    # رموز المستويات
    LEVEL_ICONS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💀"
    }
    
    # أسماء المستويات
    LEVEL_NAMES = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL"
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # تكوين التسجيل الأساسي
        self._configure_root_logger()
        
        print_colored(f"✅ تم تهيئة نظام التسجيل في: {self._log_dir}", Colors.GREEN)
    
    def _configure_root_logger(self):
        """تكوين الـ Logger الأساسي"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # إزالة المعالجات الافتراضية
        root_logger.handlers.clear()
        
        # إضافة معالج للملف الرئيسي
        self._add_file_handler(root_logger, "lugyflutter.log", logging.DEBUG)
        
        # إضافة معالج للأخطاء
        self._add_file_handler(root_logger, "errors.log", logging.ERROR)
        
        # إضافة معالج للمحطة
        self._add_console_handler(root_logger)
        
        # إضافة معالج للتدوير اليومي
        self._add_daily_handler(root_logger)
    
    def _add_file_handler(self, logger: logging.Logger, filename: str, level: int):
        """إضافة معالج لتسجيل في ملف"""
        file_path = self._log_dir / filename
        
        handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def _add_console_handler(self, logger: logging.Logger):
        """إضافة معالج للمحطة الطرفية مع ألوان"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                level_color = LoggerManager.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
                icon = LoggerManager.LEVEL_ICONS.get(record.levelno, "")
                level_name = LoggerManager.LEVEL_NAMES.get(record.levelno, "UNKNOWN")
                
                # تنسيق الرسالة
                message = record.getMessage()
                
                # إضافة تتبع الأخطاء
                if record.exc_info:
                    import traceback
                    message += "\n" + "".join(traceback.format_exception(*record.exc_info))
                
                # تلوين حسب المستوى
                timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
                
                if record.levelno >= logging.ERROR:
                    return f"{icon} [{timestamp}] {level_color}{level_name}{Colors.END}: {level_color}{message}{Colors.END}"
                elif record.levelno == logging.WARNING:
                    return f"{icon} [{timestamp}] {level_color}{level_name}{Colors.END}: {message}"
                else:
                    return f"{icon} [{timestamp}] {level_color}{level_name}{Colors.END}: {message}"
        
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
    
    def _add_daily_handler(self, logger: logging.Logger):
        """إضافة معالج للتدوير اليومي"""
        file_path = self._log_dir / "lugyflutter_daily.log"
        
        handler = TimedRotatingFileHandler(
            file_path,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def get_logger(self, name: str = "LugyFlutter", level: str = "INFO") -> logging.Logger:
        """
        الحصول على كائن Logger باسم محدد
        
        Args:
            name: اسم الـ Logger
            level: مستوى التسجيل الافتراضي
        
        Returns:
            logging.Logger: كائن الـ Logger
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.LEVELS.get(level.upper(), logging.INFO))
        
        # إضافة معالج للملف الخاص بهذا الـ Logger
        self._add_file_handler(logger, f"{name.lower()}.log", logging.DEBUG)
        
        self._loggers[name] = logger
        return logger
    
    def set_level(self, level: str):
        """
        تغيير مستوى التسجيل لجميع الـ Loggers
        
        Args:
            level: المستوى الجديد (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = self.LEVELS.get(level.upper(), logging.INFO)
        
        for logger in self._loggers.values():
            logger.setLevel(log_level)
        
        logging.getLogger().setLevel(log_level)
        print_colored(f"✅ تم تغيير مستوى التسجيل إلى: {level}", Colors.CYAN)
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التسجيل"""
        stats = {
            "log_dir": str(self._log_dir),
            "loggers": len(self._loggers),
            "logger_names": list(self._loggers.keys()),
            "files": []
        }
        
        # معلومات الملفات
        for file_path in self._log_dir.glob("*.log*"):
            if file_path.is_file():
                stats["files"].append({
                    "name": file_path.name,
                    "size": self._get_file_size(file_path),
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return stats
    
    def _get_file_size(self, file_path: Path) -> str:
        """الحصول على حجم الملف بتنسيق مقروء"""
        if not file_path.exists():
            return "0 B"
        
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def export_logs(self, export_path: Optional[str] = None) -> str:
        """
        تصدير جميع السجلات إلى ملف واحد
        
        Args:
            export_path: مسار ملف التصدير (اختياري)
        
        Returns:
            str: مسار الملف المصدر
        """
        if not export_path:
            export_path = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        export_path = Path(export_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(export_path, 'w', encoding='utf-8') as output:
                output.write(f"# LugyFlutter Logs Export\n")
                output.write(f"# Exported at: {datetime.now().isoformat()}\n")
                output.write(f"# Log directory: {self._log_dir}\n")
                output.write("=" * 80 + "\n\n")
                
                # جمع جميع ملفات السجلات
                for log_file in sorted(self._log_dir.glob("*.log*")):
                    if log_file.is_file() and not log_file.name.endswith('.bak'):
                        output.write(f"\n\n{'='*80}\n")
                        output.write(f"FILE: {log_file.name}\n")
                        output.write(f"{'='*80}\n\n")
                        
                        try:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                output.write(f.read())
                        except Exception as e:
                            output.write(f"Error reading file: {e}\n")
            
            print_colored(f"✅ تم تصدير السجلات إلى: {export_path}", Colors.GREEN)
            return str(export_path)
            
        except Exception as e:
            print_colored(f"❌ فشل تصدير السجلات: {e}", Colors.RED)
            return ""
    
    def clear_logs(self):
        """مسح جميع ملفات السجلات"""
        try:
            count = 0
            for file_path in self._log_dir.glob("*.log*"):
                if file_path.is_file():
                    file_path.unlink()
                    count += 1
            
            print_colored(f"✅ تم مسح {count} ملف سجل", Colors.GREEN)
            
        except Exception as e:
            print_colored(f"❌ فشل مسح السجلات: {e}", Colors.RED)
    
    def search_logs(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        البحث في ملفات السجلات
        
        Args:
            query: نص البحث
            case_sensitive: تمييز حالة الأحرف
        
        Returns:
            List[Dict]: نتائج البحث
        """
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for log_file in self._log_dir.glob("*.log*"):
            if not log_file.is_file() or log_file.name.endswith('.bak'):
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        search_line = line if case_sensitive else line.lower()
                        if query in search_line:
                            results.append({
                                "file": log_file.name,
                                "line": line_num,
                                "content": line.strip()
                            })
            except Exception as e:
                print_colored(f"⚠️ فشل قراءة {log_file.name}: {e}", Colors.YELLOW)
        
        return results


# دوال مساعدة للاستخدام السريع
_logger_manager = LoggerManager()


def get_logger(name: str = "LugyFlutter") -> logging.Logger:
    """الحصول على كائن Logger"""
    return _logger_manager.get_logger(name)


def debug(message: str, *args, **kwargs):
    """تسجيل رسالة تصحيح"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """تسجيل رسالة معلومات"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """تسجيل رسالة تحذير"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """تسجيل رسالة خطأ"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """تسجيل رسالة حرجة"""
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """تسجيل استثناء مع تتبع كامل"""
    get_logger().exception(message, *args, **kwargs)


def set_log_level(level: str):
    """تغيير مستوى التسجيل"""
    _logger_manager.set_level(level)


def export_logs(export_path: Optional[str] = None) -> str:
    """تصدير السجلات"""
    return _logger_manager.export_logs(export_path)


def clear_logs():
    """مسح السجلات"""
    _logger_manager.clear_logs()


def search_logs(query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """البحث في السجلات"""
    return _logger_manager.search_logs(query, case_sensitive)


__all__ = [
    "LoggerManager",
    "get_logger",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
    "set_log_level",
    "export_logs",
    "clear_logs",
    "search_logs"
]