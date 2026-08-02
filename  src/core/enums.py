"""
LugyFlutter - الأنواع العامة (Enums)
"""

from enum import Enum


class TaskType(Enum):
    """أنواع المهام التي يمكن للوكيل تنفيذها"""
    CREATE_NEW = "create_new"
    EDIT_EXISTING = "edit_existing"
    CLONE_FROM_FIGMA = "clone_from_figma"
    CLONE_FROM_LOVABLE = "clone_from_lovable"
    ANALYZE_DESIGN = "analyze_design"
    GENERATE_CODE = "generate_code"
    UNKNOWN = "unknown"


class InteractionMode(Enum):
    """مستويات التفاعل مع المستخدم"""
    AUTO = "auto"  # تنفيذ تلقائي بالكامل
    CONFIRM_STEPS = "confirm_steps"  # تأكيد قبل كل خطوة
    ASK_CLARIFICATIONS = "ask_clarifications"  # سؤال عند الغموض فقط
    FULL_INTERACTIVE = "full_interactive"  # تفاعل كامل
    DEBUG = "debug"  # وضع التصحيح خطوة بخطوة


class BrowserStatus(Enum):
    """حالة المتصفح"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


class CheckpointStatus(Enum):
    """حالة نقاط التفتيش"""
    SAVED = "saved"
    RESTORED = "restored"
    FAILED = "failed"
    CORRUPTED = "corrupted"