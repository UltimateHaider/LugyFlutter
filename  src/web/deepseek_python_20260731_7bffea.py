# LugyFlutter - نماذج البيانات (Models)
# تعريف نماذج Pydantic لاستخدامها في واجهات API والتطبيق

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator

from src.utils.validators import Validators


# ============================================================
# الأنواع الأساسية (Enums)
# ============================================================

class TaskTypeEnum(str, Enum):
    """أنواع المهام"""
    CREATE_NEW = "create_new"
    EDIT_EXISTING = "edit_existing"
    CLONE_FROM_FIGMA = "clone_from_figma"
    CLONE_FROM_LOVABLE = "clone_from_lovable"
    ANALYZE_DESIGN = "analyze_design"
    GENERATE_CODE = "generate_code"
    UNKNOWN = "unknown"


class InteractionModeEnum(str, Enum):
    """وضعيات التفاعل"""
    AUTO = "auto"
    CONFIRM_STEPS = "confirm_steps"
    ASK_CLARIFICATIONS = "ask_clarifications"
    FULL_INTERACTIVE = "full_interactive"
    DEBUG = "debug"


class ProjectStatusEnum(str, Enum):
    """حالات المشروع"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SourceTypeEnum(str, Enum):
    """أنواع المصادر"""
    FLUTTERFLOW = "flutterflow"
    FIGMA = "figma"
    LOVABLE = "lovable"
    CUSTOM = "custom"
    GITHUB = "github"
    LOCAL = "local"


class CheckpointStatusEnum(str, Enum):
    """حالات نقاط التفتيش"""
    SAVED = "saved"
    RESTORED = "restored"
    FAILED = "failed"
    CORRUPTED = "corrupted"


class LogLevelEnum(str, Enum):
    """مستويات التسجيل"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================
# نماذج المشاريع
# ============================================================

class ProjectBase(BaseModel):
    """نموذج أساسي للمشروع"""
    name: str = Field(..., description="اسم المشروع", min_length=2, max_length=50)
    description: Optional[str] = Field(None, description="وصف المشروع")
    status: ProjectStatusEnum = Field(ProjectStatusEnum.DRAFT, description="حالة المشروع")
    tags: List[str] = Field(default_factory=list, description="العلامات")
    
    @validator('name')
    def validate_name(cls, v):
        if not Validators.validate_project_name(v):
            raise ValueError("اسم المشروع غير صحيح. يجب أن يكون 2-50 حرفاً")
        return v


class ProjectCreate(ProjectBase):
    """نموذج إنشاء مشروع"""
    template: str = Field("blank", description="قالب المشروع", enum=["blank", "app", "game"])
    source_type: Optional[SourceTypeEnum] = Field(None, description="نوع المصدر")
    source_url: Optional[str] = Field(None, description="رابط المصدر")
    clone_source: Optional[str] = Field(None, description="مصدر النسخ")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="بيانات إضافية")


class ProjectUpdate(BaseModel):
    """نموذج تحديث مشروع"""
    name: Optional[str] = Field(None, description="اسم المشروع", min_length=2, max_length=50)
    description: Optional[str] = Field(None, description="وصف المشروع")
    status: Optional[ProjectStatusEnum] = Field(None, description="حالة المشروع")
    tags: Optional[List[str]] = Field(None, description="العلامات")
    metadata: Optional[Dict[str, Any]] = Field(None, description="بيانات إضافية")
    
    @validator('name')
    def validate_name(cls, v):
        if v and not Validators.validate_project_name(v):
            raise ValueError("اسم المشروع غير صحيح. يجب أن يكون 2-50 حرفاً")
        return v


class ProjectResponse(ProjectBase):
    """نموذج استجابة المشروع"""
    project_id: str = Field(..., description="معرف المشروع")
    source_type: Optional[SourceTypeEnum] = Field(None, description="نوع المصدر")
    source_url: Optional[str] = Field(None, description="رابط المصدر")
    clone_source: Optional[str] = Field(None, description="مصدر النسخ")
    modifications_count: int = Field(0, description="عدد التعديلات")
    created_at: str = Field(..., description="تاريخ الإنشاء")
    updated_at: str = Field(..., description="تاريخ التحديث")
    last_accessed: str = Field(..., description="آخر وصول")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="بيانات إضافية")


# ============================================================
# نماذج نقاط التفتيش
# ============================================================

class CheckpointBase(BaseModel):
    """نموذج أساسي لنقطة تفتيش"""
    description: str = Field(..., description="وصف نقطة التفتيش", min_length=1, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="بيانات إضافية")


class CheckpointCreate(CheckpointBase):
    """نموذج إنشاء نقطة تفتيش"""
    step: Optional[int] = Field(None, description="رقم الخطوة")
    state: Optional[Dict[str, Any]] = Field(None, description="حالة النظام")
    screenshot: Optional[str] = Field(None, description="لقطة شاشة (Base64)")


class CheckpointResponse(CheckpointBase):
    """نموذج استجابة نقطة تفتيش"""
    checkpoint_id: str = Field(..., description="معرف نقطة التفتيش")
    step: int = Field(..., description="رقم الخطوة")
    parent_id: Optional[str] = Field(None, description="معرف النقطة السابقة")
    has_screenshot: bool = Field(False, description="وجود لقطة شاشة")
    timestamp: str = Field(..., description="وقت الإنشاء")
    state: Optional[Dict[str, Any]] = Field(None, description="حالة النظام")


class CheckpointListResponse(BaseModel):
    """نموذج قائمة نقاط التفتيش"""
    total: int = Field(..., description="العدد الإجمالي")
    current_index: int = Field(..., description="الفهرس الحالي")
    checkpoints: List[CheckpointResponse] = Field(..., description="قائمة النقاط")


# ============================================================
# نماذج المهام
# ============================================================

class TaskBase(BaseModel):
    """نموذج أساسي للمهمة"""
    user_input: str = Field(..., description="طلب المستخدم", min_length=1, max_length=1000)
    mode: InteractionModeEnum = Field(InteractionModeEnum.FULL_INTERACTIVE, description="وضع التفاعل")
    project_name: Optional[str] = Field(None, description="اسم المشروع")
    auto_execute: bool = Field(False, description="تنفيذ تلقائي")


class TaskCreate(TaskBase):
    """نموذج إنشاء مهمة"""
    background: bool = Field(True, description="تنفيذ في الخلفية")
    timeout: int = Field(300, description="مهلة التنفيذ بالثواني", ge=10, le=3600)


class TaskResponse(BaseModel):
    """نموذج استجابة مهمة"""
    task_id: str = Field(..., description="معرف المهمة")
    status: str = Field(..., description="حالة المهمة")
    result: Optional[str] = Field(None, description="نتيجة المهمة")
    error: Optional[str] = Field(None, description="رسالة الخطأ")
    progress: int = Field(0, description="نسبة التقدم", ge=0, le=100)
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="خطوات التنفيذ")
    started_at: str = Field(..., description="وقت البدء")
    updated_at: str = Field(..., description="آخر تحديث")
    completed_at: Optional[str] = Field(None, description="وقت الانتهاء")


class TaskListResponse(BaseModel):
    """نموذج قائمة المهام"""
    total: int = Field(..., description="العدد الإجمالي")
    tasks: List[TaskResponse] = Field(..., description="قائمة المهام")


# ============================================================
# نماذج المحادثة
# ============================================================

class MessageRoleEnum(str, Enum):
    """أدوار الرسائل"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class MessageBase(BaseModel):
    """نموذج أساسي للرسالة"""
    role: MessageRoleEnum = Field(..., description="دور المرسل")
    content: str = Field(..., description="محتوى الرسالة", min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="بيانات إضافية")


class MessageCreate(MessageBase):
    """نموذج إنشاء رسالة"""
    parent_id: Optional[str] = Field(None, description="معرف الرسالة السابقة")


class MessageResponse(MessageBase):
    """نموذج استجابة رسالة"""
    message_id: str = Field(..., description="معرف الرسالة")
    parent_id: Optional[str] = Field(None, description="معرف الرسالة السابقة")
    timestamp: str = Field(..., description="وقت الإرسال")


class ConversationResponse(BaseModel):
    """نموذج استجابة محادثة"""
    total: int = Field(..., description="العدد الإجمالي")
    messages: List[MessageResponse] = Field(..., description="قائمة الرسائل")
    summary: Dict[str, Any] = Field(default_factory=dict, description="ملخص المحادثة")


# ============================================================
# نماذج النسخ من المصادر
# ============================================================

class CloneSourceBase(BaseModel):
    """نموذج أساسي للنسخ من مصدر"""
    source_url: str = Field(..., description="رابط المصدر")
    source_type: SourceTypeEnum = Field(..., description="نوع المصدر")
    project_name: str = Field(..., description="اسم المشروع الجديد", min_length=2, max_length=50)
    
    @validator('source_url')
    def validate_source_url(cls, v, values):
        if 'source_type' in values:
            if values['source_type'] == SourceTypeEnum.FIGMA:
                if not Validators.validate_figma_url(v):
                    raise ValueError("رابط Figma غير صحيح")
            elif values['source_type'] == SourceTypeEnum.LOVABLE:
                if not Validators.validate_lovable_url(v):
                    raise ValueError("رابط Lovable غير صحيح")
        return v
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if not Validators.validate_project_name(v):
            raise ValueError("اسم المشروع غير صحيح. يجب أن يكون 2-50 حرفاً")
        return v


class CloneFromFigma(CloneSourceBase):
    """النسخ من Figma"""
    source_type: SourceTypeEnum = Field(SourceTypeEnum.FIGMA, description="نوع المصدر")
    node_id: Optional[str] = Field(None, description="معرف العقدة في Figma")
    include_images: bool = Field(True, description="تضمين الصور")


class CloneFromLovable(CloneSourceBase):
    """النسخ من Lovable"""
    source_type: SourceTypeEnum = Field(SourceTypeEnum.LOVABLE, description="نوع المصدر")
    include_components: bool = Field(True, description="تضمين المكونات")


class CloneResponse(BaseModel):
    """نموذج استجابة النسخ"""
    status: str = Field(..., description="حالة العملية")
    message: str = Field(..., description="رسالة النتيجة")
    project: ProjectResponse = Field(..., description="المشروع الجديد")
    source_analysis: Optional[Dict[str, Any]] = Field(None, description="تحليل المصدر")


# ============================================================
# نماذج السجلات
# ============================================================

class LogEntry(BaseModel):
    """نموذج مدخل سجل"""
    timestamp: str = Field(..., description="الوقت")
    level: LogLevelEnum = Field(..., description="المستوى")
    message: str = Field(..., description="الرسالة")
    source: Optional[str] = Field(None, description="المصدر")
    details: Optional[Dict[str, Any]] = Field(None, description="تفاصيل إضافية")


class LogSearchRequest(BaseModel):
    """نموذج طلب بحث في السجلات"""
    query: str = Field(..., description="نص البحث", min_length=1)
    level: Optional[LogLevelEnum] = Field(None, description="المستوى")
    start_date: Optional[str] = Field(None, description="تاريخ البداية")
    end_date: Optional[str] = Field(None, description="تاريخ النهاية")
    limit: int = Field(100, description="الحد الأقصى للنتائج", ge=1, le=1000)


class LogSearchResponse(BaseModel):
    """نموذج استجابة بحث في السجلات"""
    total: int = Field(..., description="العدد الإجمالي")
    results: List[LogEntry] = Field(..., description="نتائج البحث")


class LogExportResponse(BaseModel):
    """نموذج استجابة تصدير السجلات"""
    status: str = Field(..., description="حالة التصدير")
    file_path: str = Field(..., description="مسار الملف المصدر")
    file_size: str = Field(..., description="حجم الملف")
    message: str = Field(..., description="رسالة النتيجة")


# ============================================================
# نماذج النظام
# ============================================================

class SystemInfo(BaseModel):
    """نموذج معلومات النظام"""
    system: str = Field(..., description="نظام التشغيل")
    release: str = Field(..., description="الإصدار")
    version: str = Field(..., description="النسخة")
    machine: str = Field(..., description="نوع الجهاز")
    processor: str = Field(..., description="المعالج")
    python: str = Field(..., description="نسخة Python")
    cpu_count: int = Field(..., description="عدد الأنوية")
    memory_total: str = Field(..., description="إجمالي الذاكرة")
    memory_available: str = Field(..., description="الذاكرة المتاحة")
    disk_usage: str = Field(..., description="استخدام القرص")


class HealthResponse(BaseModel):
    """نموذج استجابة فحص الصحة"""
    status: str = Field(..., description="حالة الخدمة")
    version: str = Field(..., description="الإصدار")
    timestamp: str = Field(..., description="الوقت")
    system_info: SystemInfo = Field(..., description="معلومات النظام")
    agent_initialized: bool = Field(False, description="تهيئة الوكيل")
    browser_ready: bool = Field(False, description="المتصفح جاهز")


class StatusResponse(BaseModel):
    """نموذج استجابة الحالة العامة"""
    status: str = Field(..., description="الحالة")
    name: str = Field(..., description="الاسم")
    version: str = Field(..., description="الإصدار")
    uptime: Optional[str] = Field(None, description="مدة التشغيل")
    context: Optional[Dict[str, Any]] = Field(None, description="السياق")
    stats: Optional[Dict[str, Any]] = Field(None, description="الإحصائيات")
    checkpoints: int = Field(0, description="عدد نقاط التفتيش")
    projects: int = Field(0, description="عدد المشاريع")
    tasks: int = Field(0, description="عدد المهام")
    browser_ready: bool = Field(False, description="المتصفح جاهز")


# ============================================================
# نماذج الأخطاء
# ============================================================

class ErrorResponse(BaseModel):
    """نموذج استجابة خطأ"""
    status: str = Field("error", description="الحالة")
    code: int = Field(..., description="رمز الخطأ")
    message: str = Field(..., description="رسالة الخطأ")
    details: Optional[Dict[str, Any]] = Field(None, description="تفاصيل إضافية")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="الوقت")


class ValidationError(BaseModel):
    """نموذج خطأ التحقق"""
    field: str = Field(..., description="الحقل")
    message: str = Field(..., description="رسالة الخطأ")
    value: Optional[Any] = Field(None, description="القيمة المدخلة")


class ValidationErrorResponse(ErrorResponse):
    """نموذج استجابة خطأ التحقق"""
    errors: List[ValidationError] = Field(..., description="أخطاء التحقق")


# ============================================================
# نماذج الإعدادات
# ============================================================

class SettingsBase(BaseModel):
    """نموذج أساسي للإعدادات"""
    log_level: LogLevelEnum = Field(LogLevelEnum.INFO, description="مستوى التسجيل")
    max_checkpoints: int = Field(20, description="الحد الأقصى لنقاط التفتيش", ge=5, le=100)
    max_steps: int = Field(30, description="الحد الأقصى للخطوات", ge=5, le=100)
    retry_delay: int = Field(3, description="التأخير بين المحاولات بالثواني", ge=1, le=10)
    save_screenshots: bool = Field(True, description="حفظ لقطات الشاشة")
    auto_healing_enabled: bool = Field(True, description="تفعيل الشفاء الذاتي")
    vision_fallback_enabled: bool = Field(True, description="تفعيل الرؤية الحاسوبية")


class SettingsUpdate(BaseModel):
    """نموذج تحديث الإعدادات"""
    log_level: Optional[LogLevelEnum] = Field(None, description="مستوى التسجيل")
    max_checkpoints: Optional[int] = Field(None, description="الحد الأقصى لنقاط التفتيش", ge=5, le=100)
    max_steps: Optional[int] = Field(None, description="الحد الأقصى للخطوات", ge=5, le=100)
    retry_delay: Optional[int] = Field(None, description="التأخير بين المحاولات بالثواني", ge=1, le=10)
    save_screenshots: Optional[bool] = Field(None, description="حفظ لقطات الشاشة")
    auto_healing_enabled: Optional[bool] = Field(None, description="تفعيل الشفاء الذاتي")
    vision_fallback_enabled: Optional[bool] = Field(None, description="تفعيل الرؤية الحاسوبية")


class SettingsResponse(SettingsBase):
    """نموذج استجابة الإعدادات"""
    google_api_key_configured: bool = Field(..., description="تم تكوين مفتاح API")
    browser_configured: bool = Field(..., description="تم تكوين المتصفح")
    web_dashboard_enabled: bool = Field(..., description="تفعيل لوحة التحكم")
    api_enabled: bool = Field(..., description="تفعيل واجهة API")


# ============================================================
# نماذج متقدمة
# ============================================================

class TaskSuggestion(BaseModel):
    """نموذج اقتراح مهمة"""
    text: str = Field(..., description="نص الاقتراح")
    type: TaskTypeEnum = Field(..., description="نوع المهمة")
    confidence: float = Field(..., description="نسبة الثقة", ge=0, le=1)
    examples: List[str] = Field(default_factory=list, description="أمثلة")


class WidgetInfo(BaseModel):
    """نموذج معلومات Widget"""
    name: str = Field(..., description="اسم الـ Widget")
    type: str = Field(..., description="النوع")
    properties: Dict[str, Any] = Field(default_factory=dict, description="الخصائص")
    children: List['WidgetInfo'] = Field(default_factory=list, description="الـ Widgets الفرعية")


class DesignAnalysis(BaseModel):
    """نموذج تحليل التصميم"""
    widgets: List[WidgetInfo] = Field(default_factory=list, description="الـ Widgets")
    colors: List[str] = Field(default_factory=list, description="الألوان المستخدمة")
    fonts: List[str] = Field(default_factory=list, description="الخطوط المستخدمة")
    spacing: Dict[str, int] = Field(default_factory=dict, description="التباعد")
    layout: str = Field("", description="نوع التخطيط")
    complexity: str = Field("", description="مستوى التعقيد")
    suggestions: List[str] = Field(default_factory=list, description="اقتراحات التحسين")


# ============================================================
# تصدير النماذج
# ============================================================

__all__ = [
    # الأنواع الأساسية
    "TaskTypeEnum",
    "InteractionModeEnum",
    "ProjectStatusEnum",
    "SourceTypeEnum",
    "CheckpointStatusEnum",
    "LogLevelEnum",
    
    # نماذج المشاريع
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    
    # نماذج نقاط التفتيش
    "CheckpointBase",
    "CheckpointCreate",
    "CheckpointResponse",
    "CheckpointListResponse",
    
    # نماذج المهام
    "TaskBase",
    "TaskCreate",
    "TaskResponse",
    "TaskListResponse",
    
    # نماذج المحادثة
    "MessageRoleEnum",
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ConversationResponse",
    
    # نماذج النسخ
    "CloneSourceBase",
    "CloneFromFigma",
    "CloneFromLovable",
    "CloneResponse",
    
    # نماذج السجلات
    "LogEntry",
    "LogSearchRequest",
    "LogSearchResponse",
    "LogExportResponse",
    
    # نماذج النظام
    "SystemInfo",
    "HealthResponse",
    "StatusResponse",
    
    # نماذج الأخطاء
    "ErrorResponse",
    "ValidationError",
    "ValidationErrorResponse",
    
    # نماذج الإعدادات
    "SettingsBase",
    "SettingsUpdate",
    "SettingsResponse",
    
    # نماذج متقدمة
    "TaskSuggestion",
    "WidgetInfo",
    "DesignAnalysis"
]

# حل المشكلة المرجعية لـ WidgetInfo.children
WidgetInfo.model_rebuild()