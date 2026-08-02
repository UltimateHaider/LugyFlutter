"""
LugyFlutter - الاستثناءات المخصصة (Custom Exceptions)
نظام متكامل لإدارة الأخطاء والاستثناءات في LugyFlutter
"""

from typing import Optional, Dict, Any


class LugyFlutterError(Exception):
    """
    الاستثناء الأساسي لجميع أخطاء LugyFlutter
    جميع الاستثناءات الأخرى ترث من هذا الاستثناء
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - التفاصيل: {self.details}"
        return self.message


# ============================================================
# 1. أخطاء الإعدادات والتهيئة (Configuration Errors)
# ============================================================

class ConfigError(LugyFlutterError):
    """أخطاء في الإعدادات أو ملف .env"""
    pass


class APIKeyError(ConfigError):
    """أخطاء متعلقة بمفتاح API"""
    
    def __init__(self, message: str = "مفتاح API غير صالح أو غير موجود", details: Optional[Dict] = None):
        super().__init__(message, details)


class EnvironmentError(ConfigError):
    """أخطاء في البيئة أو المتغيرات"""
    pass


# ============================================================
# 2. أخطاء المتصفح (Browser Errors)
# ============================================================

class BrowserError(LugyFlutterError):
    """أخطاء متعلقة بالمتصفح"""
    pass


class BrowserInitializationError(BrowserError):
    """أخطاء في تهيئة المتصفح"""
    
    def __init__(self, message: str = "فشل تهيئة المتصفح", details: Optional[Dict] = None):
        super().__init__(message, details)


class BrowserNavigationError(BrowserError):
    """أخطاء في التنقل بين الصفحات"""
    
    def __init__(self, url: str, message: str = "فشل التنقل إلى الصفحة", details: Optional[Dict] = None):
        self.url = url
        super().__init__(f"{message}: {url}", details)


class ElementNotFoundError(BrowserError):
    """عنصر غير موجود في الصفحة"""
    
    def __init__(self, selector: str, message: str = "العنصر غير موجود", details: Optional[Dict] = None):
        self.selector = selector
        super().__init__(f"{message}: {selector}", details)


class ElementInteractionError(BrowserError):
    """أخطاء في التفاعل مع العناصر (نقر، كتابة، إلخ)"""
    
    def __init__(self, action: str, message: str = "فشل التفاعل مع العنصر", details: Optional[Dict] = None):
        self.action = action
        super().__init__(f"{message} - الإجراء: {action}", details)


class TimeoutError(BrowserError):
    """انتهاء وقت الانتظار"""
    
    def __init__(self, timeout: int, message: str = "انتهى وقت الانتظار", details: Optional[Dict] = None):
        self.timeout = timeout
        super().__init__(f"{message} - المهلة: {timeout} ثانية", details)


# ============================================================
# 3. أخطاء استخراج المعلومات (Extraction Errors)
# ============================================================

class ExtractionError(LugyFlutterError):
    """أخطاء في استخراج المعلومات"""
    pass


class RegexExtractionError(ExtractionError):
    """فشل استخراج المعلومات باستخدام Regex"""
    
    def __init__(self, pattern: str, message: str = "فشل استخراج المعلومات باستخدام النمط", details: Optional[Dict] = None):
        self.pattern = pattern
        super().__init__(f"{message}: {pattern}", details)


class LLMExtractionError(ExtractionError):
    """فشل استخراج المعلومات باستخدام LLM"""
    
    def __init__(self, message: str = "فشل استخراج المعلومات باستخدام النموذج اللغوي", details: Optional[Dict] = None):
        super().__init__(message, details)


class ValidationError(ExtractionError):
    """فشل التحقق من صحة المعلومات المستخرجة"""
    
    def __init__(self, field: str, value: Any, message: str = "البيانات غير صالحة", details: Optional[Dict] = None):
        self.field = field
        self.value = value
        super().__init__(f"{message} - الحقل: {field}, القيمة: {value}", details)


# ============================================================
# 4. أخطاء نقاط التفتيش (Checkpoint Errors)
# ============================================================

class CheckpointError(LugyFlutterError):
    """أخطاء في نظام نقاط التفتيش"""
    pass


class CheckpointSaveError(CheckpointError):
    """فشل حفظ نقطة تفتيش"""
    
    def __init__(self, message: str = "فشل حفظ نقطة التفتيش", details: Optional[Dict] = None):
        super().__init__(message, details)


class CheckpointRestoreError(CheckpointError):
    """فشل استعادة نقطة تفتيش"""
    
    def __init__(self, checkpoint_id: str, message: str = "فشل استعادة نقطة التفتيش", details: Optional[Dict] = None):
        self.checkpoint_id = checkpoint_id
        super().__init__(f"{message}: {checkpoint_id}", details)


class CheckpointCorruptedError(CheckpointError):
    """نقطة تفتيش تالفة"""
    
    def __init__(self, checkpoint_id: str, message: str = "نقطة التفتيش تالفة", details: Optional[Dict] = None):
        self.checkpoint_id = checkpoint_id
        super().__init__(f"{message}: {checkpoint_id}", details)


class NoCheckpointError(CheckpointError):
    """لا توجد نقاط تفتيش للتراجع عنها"""
    
    def __init__(self, message: str = "لا توجد نقاط تفتيش متاحة", details: Optional[Dict] = None):
        super().__init__(message, details)


# ============================================================
# 5. أخطاء السياق والمشاريع (Context Errors)
# ============================================================

class ContextError(LugyFlutterError):
    """أخطاء في إدارة السياق"""
    pass


class ProjectNotFoundError(ContextError):
    """المشروع غير موجود"""
    
    def __init__(self, project_name: str, message: str = "المشروع غير موجود", details: Optional[Dict] = None):
        self.project_name = project_name
        super().__init__(f"{message}: {project_name}", details)


class ProjectCreationError(ContextError):
    """فشل إنشاء المشروع"""
    
    def __init__(self, project_name: str, message: str = "فشل إنشاء المشروع", details: Optional[Dict] = None):
        self.project_name = project_name
        super().__init__(f"{message}: {project_name}", details)


class RegistryError(ContextError):
    """أخطاء في سجل المشاريع"""
    pass


# ============================================================
# 6. أخطاء الشفاء الذاتي (Self-Healing Errors)
# ============================================================

class SelfHealingError(LugyFlutterError):
    """أخطاء في نظام الشفاء الذاتي"""
    pass


class VisionFallbackError(SelfHealingError):
    """فشل الشفاء الذاتي باستخدام الرؤية الحاسوبية"""
    
    def __init__(self, target: str, message: str = "فشل الكشف بالرؤية الحاسوبية", details: Optional[Dict] = None):
        self.target = target
        super().__init__(f"{message}: {target}", details)


class SelectorGenerationError(SelfHealingError):
    """فشل توليد محددات بديلة"""
    
    def __init__(self, element: str, message: str = "فشل توليد محددات بديلة", details: Optional[Dict] = None):
        self.element = element
        super().__init__(f"{message}: {element}", details)


# ============================================================
# 7. أخطاء الوكيل (Agent Errors)
# ============================================================

class AgentError(LugyFlutterError):
    """أخطاء في الوكيل الرئيسي"""
    pass


class TaskExecutionError(AgentError):
    """فشل تنفيذ المهمة"""
    
    def __init__(self, task: str, message: str = "فشل تنفيذ المهمة", details: Optional[Dict] = None):
        self.task = task
        super().__init__(f"{message}: {task}", details)


class TaskClassificationError(AgentError):
    """فشل تصنيف المهمة"""
    
    def __init__(self, user_input: str, message: str = "فشل تصنيف المهمة", details: Optional[Dict] = None):
        self.user_input = user_input
        super().__init__(f"{message}: {user_input}", details)


class InteractionError(AgentError):
    """أخطاء في التفاعل مع المستخدم"""
    
    def __init__(self, message: str = "فشل التفاعل مع المستخدم", details: Optional[Dict] = None):
        super().__init__(message, details)


# ============================================================
# 8. أخطاء الويب (Web Errors)
# ============================================================

class WebError(LugyFlutterError):
    """أخطاء في واجهات الويب"""
    pass


class DashboardError(WebError):
    """أخطاء في لوحة التحكم"""
    
    def __init__(self, message: str = "فشل تشغيل لوحة التحكم", details: Optional[Dict] = None):
        super().__init__(message, details)


class APIError(WebError):
    """أخطاء في واجهة API"""
    
    def __init__(self, endpoint: str, status_code: int, message: str = "خطأ في API", details: Optional[Dict] = None):
        self.endpoint = endpoint
        self.status_code = status_code
        super().__init__(f"{message} - {endpoint} (الحالة: {status_code})", details)


# ============================================================
# 9. أخطاء الملفات والتخزين (Storage Errors)
# ============================================================

class StorageError(LugyFlutterError):
    """أخطاء في التخزين والملفات"""
    pass


class FileNotFoundError(StorageError):
    """الملف غير موجود"""
    
    def __init__(self, file_path: str, message: str = "الملف غير موجود", details: Optional[Dict] = None):
        self.file_path = file_path
        super().__init__(f"{message}: {file_path}", details)


class FileReadError(StorageError):
    """فشل قراءة الملف"""
    
    def __init__(self, file_path: str, message: str = "فشل قراءة الملف", details: Optional[Dict] = None):
        self.file_path = file_path
        super().__init__(f"{message}: {file_path}", details)


class FileWriteError(StorageError):
    """فشل كتابة الملف"""
    
    def __init__(self, file_path: str, message: str = "فشل كتابة الملف", details: Optional[Dict] = None):
        self.file_path = file_path
        super().__init__(f"{message}: {file_path}", details)


# ============================================================
# 10. أخطاء الشبكة (Network Errors)
# ============================================================

class NetworkError(LugyFlutterError):
    """أخطاء في الشبكة"""
    pass


class ConnectionError(NetworkError):
    """فشل الاتصال بالخادم"""
    
    def __init__(self, url: str, message: str = "فشل الاتصال", details: Optional[Dict] = None):
        self.url = url
        super().__init__(f"{message}: {url}", details)


# ============================================================
# دوال مساعدة للتعامل مع الاستثناءات
# ============================================================

def handle_exception(error: Exception, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    معالجة الاستثناء وتحويله إلى قاموس للتسجيل أو العرض
    
    Args:
        error: الاستثناء المراد معالجته
        context: سياق إضافي (اختياري)
    
    Returns:
        قاموس يحتوي على معلومات الاستثناء
    """
    import traceback
    
    result = {
        "type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {}
    }
    
    # إضافة معلومات إضافية حسب نوع الاستثناء
    if isinstance(error, LugyFlutterError) and error.details:
        result["details"] = error.details
    
    if hasattr(error, "step"):
        result["step"] = error.step
    
    return result


def format_exception_for_user(error: Exception) -> str:
    """
    تنسيق الاستثناء لعرضه للمستخدم بشكل مفهوم
    
    Args:
        error: الاستثناء المراد تنسيقه
    
    Returns:
        رسالة مبسطة للمستخدم
    """
    if isinstance(error, APIKeyError):
        return f"🔑 {error.message}\n💡 تأكد من صحة مفتاح API في ملف .env"
    
    elif isinstance(error, BrowserInitializationError):
        return f"🌐 {error.message}\n💡 تأكد من تثبيت Playwright ووجود متصفح Chrome"
    
    elif isinstance(error, ElementNotFoundError):
        return f"🔍 {error.message}\n💡 قد يكون التصميم قد تغير، جرب استخدام وصف أكثر دقة"
    
    elif isinstance(error, TimeoutError):
        return f"⏰ {error.message}\n💡 قد تكون الصفحة بطيئة، حاول مرة أخرى"
    
    elif isinstance(error, TaskExecutionError):
        return f"❌ {error.message}\n💡 تأكد من صحة التعليمات وجرب مرة أخرى"
    
    elif isinstance(error, CheckpointError):
        return f"💾 {error.message}\n💡 قد تكون نقاط التفتيش تالفة، جرب البدء من جديد"
    
    elif isinstance(error, ConfigError):
        return f"⚙️ {error.message}\n💡 تأكد من ملف .env والإعدادات"
    
    elif isinstance(error, KeyboardInterrupt):
        return "👋 تم إلغاء العملية بواسطة المستخدم"
    
    else:
        return f"❌ حدث خطأ: {str(error)}\n💡 راجع السجلات لمزيد من التفاصيل"


# ============================================================
# 11. فئة مساعدة لإدارة الاستثناءات في التنفيذ
# ============================================================

class ExceptionManager:
    """
    مدير الاستثناءات لإدارة الأخطاء أثناء التنفيذ
    """
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.last_error = None
    
    def capture(self, error: Exception, context: Optional[Dict] = None):
        """
        تسجيل استثناء للتحليل لاحقاً
        
        Args:
            error: الاستثناء المسجل
            context: سياق إضافي
        """
        self.errors.append({
            "error": error,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
        self.last_error = error
    
    def capture_warning(self, warning: str, context: Optional[Dict] = None):
        """تسجيل تحذير"""
        self.warnings.append({
            "warning": warning,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def clear(self):
        """مسح السجل"""
        self.errors.clear()
        self.warnings.clear()
        self.last_error = None
    
    def get_last_error(self) -> Optional[Exception]:
        """الحصول على آخر استثناء"""
        return self.last_error
    
    def has_errors(self) -> bool:
        """التحقق من وجود أخطاء"""
        return len(self.errors) > 0
    
    def get_summary(self) -> Dict[str, int]:
        """الحصول على ملخص الأخطاء"""
        from collections import Counter
        
        error_types = Counter([type(e["error"]).__name__ for e in self.errors])
        
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "error_types": dict(error_types),
            "last_error": str(self.last_error) if self.last_error else None
        }


# استيراد datetime للاستخدام في ExceptionManager
from datetime import datetime


# ============================================================
# 12. زخارف (Decorators) للتعامل مع الاستثناءات
# ============================================================

def handle_errors(retry: int = 0, fallback_return: Any = None):
    """
    زخرفة للتعامل مع الاستثناءات وإعادة المحاولة
    
    Args:
        retry: عدد محاولات إعادة التنفيذ
        fallback_return: القيمة المرتجعة في حالة الفشل النهائي
    
    Example:
        @handle_errors(retry=3, fallback_return=[])
        def risky_function():
            return risky_operation()
    """
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            last_error = None
            
            while attempts <= retry:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    attempts += 1
                    if attempts <= retry:
                        time.sleep(1)
                        print_colored(f"⚠️ إعادة المحاولة {attempts}/{retry}", Colors.YELLOW)
            
            # في حالة فشل جميع المحاولات
            if fallback_return is not None:
                return fallback_return
            else:
                raise last_error
        
        return wrapper
    return decorator


def log_errors(logger=None):
    """
    زخرفة لتسجيل الاستثناءات تلقائياً
    
    Args:
        logger: كائن logger للاستخدام (اختياري)
    """
    import functools
    import logging
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger or logging.getLogger(__name__)
                log.error(f"خطأ في {func.__name__}: {e}")
                log.error(traceback.format_exc())
                raise
        
        return wrapper
    return decorator


# استيراد traceback للاستخدام في decorators
import traceback
from .colors import Colors, print_colored

__all__ = [
    # استثناءات أساسية
    "LugyFlutterError",
    
    # أخطاء الإعدادات
    "ConfigError",
    "APIKeyError",
    "EnvironmentError",
    
    # أخطاء المتصفح
    "BrowserError",
    "BrowserInitializationError",
    "BrowserNavigationError",
    "ElementNotFoundError",
    "ElementInteractionError",
    "TimeoutError",
    
    # أخطاء الاستخراج
    "ExtractionError",
    "RegexExtractionError",
    "LLMExtractionError",
    "ValidationError",
    
    # أخطاء نقاط التفتيش
    "CheckpointError",
    "CheckpointSaveError",
    "CheckpointRestoreError",
    "CheckpointCorruptedError",
    "NoCheckpointError",
    
    # أخطاء السياق
    "ContextError",
    "ProjectNotFoundError",
    "ProjectCreationError",
    "RegistryError",
    
    # أخطاء الشفاء الذاتي
    "SelfHealingError",
    "VisionFallbackError",
    "SelectorGenerationError",
    
    # أخطاء الوكيل
    "AgentError",
    "TaskExecutionError",
    "TaskClassificationError",
    "InteractionError",
    
    # أخطاء الويب
    "WebError",
    "DashboardError",
    "APIError",
    
    # أخطاء التخزين
    "StorageError",
    "FileNotFoundError",
    "FileReadError",
    "FileWriteError",
    
    # أخطاء الشبكة
    "NetworkError",
    "ConnectionError",
    
    # دوال مساعدة
    "handle_exception",
    "format_exception_for_user",
    "ExceptionManager",
    "handle_errors",
    "log_errors",
]