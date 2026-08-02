"""
LugyFlutter - مدير السياق (Context Manager)
إدارة سياق المشروع والحالة العامة للوكيل
"""

import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

from ..core.config import config
from ..core.exceptions import ContextError, ProjectNotFoundError
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


@dataclass
class ProjectContext:
    """
    سياق المشروع الحالي - يحتوي على جميع معلومات المشروع وحالة التطوير
    """
    # معلومات المشروع الأساسية
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    project_url: Optional[str] = None
    
    # حالة التطوير
    current_view: str = "dashboard"  # dashboard, builder, properties, settings, code
    current_page: Optional[str] = None
    current_widget: Optional[str] = None
    selected_widgets: List[str] = field(default_factory=list)
    
    # التصميم والمصادر
    source_url: Optional[str] = None  # رابط Figma/Lovable
    design_analysis: Optional[Dict[str, Any]] = None
    design_reference: Optional[str] = None  # مسار أو رابط للتصميم المرجعي
    
    # التعديلات والتاريخ
    modifications_made: List[str] = field(default_factory=list)
    modifications_planned: List[str] = field(default_factory=list)
    undo_stack: List[Dict[str, Any]] = field(default_factory=list)
    
    # حالة التنفيذ
    current_step: int = 0
    total_steps: int = 0
    last_action: Optional[str] = None
    action_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # معلومات إضافية
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def update(self, **kwargs):
        """
        تحديث السياق بقيم جديدة
        
        Args:
            **kwargs: القيم المراد تحديثها
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now().isoformat()
        return self
    
    def add_modification(self, modification: str):
        """إضافة تعديل جديد إلى السجل"""
        self.modifications_made.append(modification)
        self.updated_at = datetime.now().isoformat()
    
    def add_action(self, action: str, details: Dict[str, Any] = None):
        """إضافة إجراء إلى تاريخ الإجراءات"""
        self.action_history.append({
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "step": self.current_step
        })
        self.last_action = action
        self.updated_at = datetime.now().isoformat()
    
    def increment_step(self):
        """زيادة رقم الخطوة الحالية"""
        self.current_step += 1
        self.total_steps += 1
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل السياق إلى قاموس"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """إنشاء سياق من قاموس"""
        return cls(**data)
    
    def get_summary(self) -> str:
        """الحصول على ملخص السياق"""
        summary = f"""
        📁 المشروع: {self.project_name or 'غير محدد'}
        📍 الصفحة الحالية: {self.current_page or 'غير محدد'}
        🎯 الخطوة: {self.current_step}/{self.total_steps}
        📝 التعديلات: {len(self.modifications_made)}
        🔄 آخر إجراء: {self.last_action or 'لا يوجد'}
        """
        return summary.strip()


class ContextManager:
    """
    مدير السياق المتقدم لإدارة حالة المشروع والتنقل بين السياقات
    الميزات:
    - إدارة سياق المشروع الحالي
    - حفظ واستعادة السياقات السابقة
    - دعم السياقات المتعددة (مشاريع متعددة)
    - تتبع التغييرات والإجراءات
    - تصدير واستيراد السياق
    """
    
    def __init__(self, storage_dir: str = "logs/context"):
        """
        تهيئة مدير السياق
        
        Args:
            storage_dir: مجلد تخزين السياقات
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # السياق الحالي
        self.current_context: Optional[ProjectContext] = None
        
        # السياقات السابقة (للرجوع)
        self.context_history: List[ProjectContext] = []
        self.history_limit = 20
        
        # السياقات المحفوظة (مشاريع متعددة)
        self.saved_contexts: Dict[str, ProjectContext] = {}
        
        # إحصائيات
        self.stats = {
            "contexts_created": 0,
            "contexts_restored": 0,
            "contexts_saved": 0,
            "actions_recorded": 0,
            "modifications": 0
        }
        
        # تحميل السياقات المحفوظة
        self._load_saved_contexts()
        
        logger.info("تم تهيئة ContextManager")
    
    def create_context(
        self,
        project_name: str = None,
        project_id: str = None,
        source_url: str = None,
        initial_state: Dict[str, Any] = None
    ) -> ProjectContext:
        """
        إنشاء سياق جديد
        
        Args:
            project_name: اسم المشروع
            project_id: معرف المشروع
            source_url: رابط المصدر (Figma/Lovable)
            initial_state: حالة أولية إضافية
        
        Returns:
            ProjectContext: السياق الجديد
        """
        # إذا كان هناك سياق حالياً، حفظه في التاريخ
        if self.current_context:
            self.context_history.append(self.current_context)
            if len(self.context_history) > self.history_limit:
                self.context_history.pop(0)
        
        # إنشاء السياق الجديد
        context = ProjectContext(
            project_name=project_name,
            project_id=project_id,
            source_url=source_url,
            metadata=initial_state or {}
        )
        
        if initial_state:
            for key, value in initial_state.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        
        # تعيين كسياق حالي
        self.current_context = context
        self.stats["contexts_created"] += 1
        
        # حفظ السياق
        self._save_context(context)
        
        logger.info(f"إنشاء سياق جديد: {project_name or 'غير مسمى'}")
        return context
    
    def get_context(self) -> Optional[ProjectContext]:
        """
        الحصول على السياق الحالي
        
        Returns:
            Optional[ProjectContext]: السياق الحالي
        """
        return self.current_context
    
    def update_context(self, **kwargs) -> ProjectContext:
        """
        تحديث السياق الحالي
        
        Args:
            **kwargs: القيم المراد تحديثها
        
        Returns:
            ProjectContext: السياق المحدث
        """
        if not self.current_context:
            raise ContextError("لا يوجد سياق حالي للتحديث")
        
        self.current_context.update(**kwargs)
        self._save_context(self.current_context)
        
        logger.debug(f"تحديث السياق: {kwargs}")
        return self.current_context
    
    def add_modification(self, modification: str):
        """
        إضافة تعديل إلى السياق الحالي
        
        Args:
            modification: وصف التعديل
        """
        if not self.current_context:
            raise ContextError("لا يوجد سياق حالي")
        
        self.current_context.add_modification(modification)
        self.stats["modifications"] += 1
        self._save_context(self.current_context)
        
        logger.debug(f"إضافة تعديل: {modification}")
    
    def record_action(self, action: str, details: Dict[str, Any] = None):
        """
        تسجيل إجراء في السياق الحالي
        
        Args:
            action: اسم الإجراء
            details: تفاصيل الإجراء
        """
        if not self.current_context:
            raise ContextError("لا يوجد سياق حالي")
        
        self.current_context.add_action(action, details)
        self.stats["actions_recorded"] += 1
        self._save_context(self.current_context)
        
        logger.debug(f"تسجيل إجراء: {action}")
    
    def restore_previous_context(self) -> Optional[ProjectContext]:
        """
        استعادة السياق السابق
        
        Returns:
            Optional[ProjectContext]: السياق المستعاد
        """
        if not self.context_history:
            logger.warning("لا يوجد سياقات سابقة للاستعادة")
            return None
        
        # حفظ السياق الحالي
        if self.current_context:
            self.saved_contexts[self.current_context.project_name or "current"] = self.current_context
        
        # استعادة السياق السابق
        previous = self.context_history.pop()
        self.current_context = previous
        self.stats["contexts_restored"] += 1
        
        logger.info(f"استعادة السياق السابق: {previous.project_name}")
        return previous
    
    def save_context(self, name: str = None) -> str:
        """
        حفظ السياق الحالي باسم معين
        
        Args:
            name: اسم السياق (افتراضي: اسم المشروع)
        
        Returns:
            str: اسم السياق المحفوظ
        """
        if not self.current_context:
            raise ContextError("لا يوجد سياق لحفظه")
        
        save_name = name or self.current_context.project_name or f"context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # حفظ السياق
        self.saved_contexts[save_name] = self.current_context
        self.stats["contexts_saved"] += 1
        
        # حفظ في الملف
        self._save_context(self.current_context, save_name)
        
        logger.info(f"حفظ السياق: {save_name}")
        return save_name
    
    def load_saved_context(self, name: str) -> Optional[ProjectContext]:
        """
        تحميل سياق محفوظ
        
        Args:
            name: اسم السياق
        
        Returns:
            Optional[ProjectContext]: السياق المحمّل
        """
        if name not in self.saved_contexts:
            logger.warning(f"السياق غير موجود: {name}")
            return None
        
        # حفظ السياق الحالي
        if self.current_context:
            self.context_history.append(self.current_context)
        
        # تحميل السياق
        self.current_context = self.saved_contexts[name]
        self.stats["contexts_restored"] += 1
        
        logger.info(f"تحميل السياق: {name}")
        return self.current_context
    
    def list_saved_contexts(self) -> List[Dict[str, Any]]:
        """
        قائمة السياقات المحفوظة
        
        Returns:
            List[Dict]: قائمة السياقات
        """
        return [
            {
                "name": name,
                "project_name": ctx.project_name,
                "project_id": ctx.project_id,
                "created_at": ctx.created_at,
                "updated_at": ctx.updated_at,
                "modifications_count": len(ctx.modifications_made),
                "steps": ctx.total_steps,
                "has_source": bool(ctx.source_url)
            }
            for name, ctx in self.saved_contexts.items()
        ]
    
    def get_context_history(self) -> List[Dict[str, Any]]:
        """
        الحصول على تاريخ السياقات
        
        Returns:
            List[Dict]: تاريخ السياقات
        """
        return [
            {
                "project_name": ctx.project_name,
                "created_at": ctx.created_at,
                "modifications": len(ctx.modifications_made),
                "steps": ctx.total_steps
            }
            for ctx in self.context_history
        ]
    
    def _save_context(self, context: ProjectContext, name: str = None):
        """حفظ السياق في الملف"""
        try:
            if name:
                file_path = self.storage_dir / f"{name}.json"
            else:
                file_path = self.storage_dir / f"{context.project_name or 'context'}.json"
            
            file_path.write_text(
                json.dumps(context.to_dict(), ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"فشل حفظ السياق: {e}")
    
    def _load_saved_contexts(self):
        """تحميل السياقات المحفوظة من الملفات"""
        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    data = json.loads(file_path.read_text(encoding='utf-8'))
                    context = ProjectContext.from_dict(data)
                    
                    # استخدام اسم الملف كاسم للسياق
                    name = file_path.stem
                    self.saved_contexts[name] = context
                    
                except Exception as e:
                    logger.warning(f"فشل تحميل السياق من {file_path}: {e}")
            
            logger.info(f"تحميل {len(self.saved_contexts)} سياق محفوظ")
            
        except Exception as e:
            logger.error(f"فشل تحميل السياقات المحفوظة: {e}")
    
    def clear_history(self):
        """مسح تاريخ السياقات"""
        self.context_history.clear()
        logger.info("تم مسح تاريخ السياقات")
    
    def delete_context(self, name: str) -> bool:
        """
        حذف سياق محفوظ
        
        Args:
            name: اسم السياق
        
        Returns:
            bool: نجاح الحذف
        """
        if name not in self.saved_contexts:
            return False
        
        # حذف من الذاكرة
        del self.saved_contexts[name]
        
        # حذف الملف
        file_path = self.storage_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"حذف السياق: {name}")
        return True
    
    def export_contexts(self, export_path: str) -> str:
        """
        تصدير جميع السياقات إلى ملف
        
        Args:
            export_path: مسار ملف التصدير
        
        Returns:
            str: مسار الملف المصدر
        """
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "exported_at": datetime.now().isoformat(),
                "contexts": {
                    name: ctx.to_dict()
                    for name, ctx in self.saved_contexts.items()
                },
                "current_context": self.current_context.to_dict() if self.current_context else None,
                "stats": self.stats
            }
            
            export_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            logger.info(f"تصدير السياقات إلى: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"فشل تصدير السياقات: {e}")
            raise ContextError(
                message="فشل تصدير السياقات",
                details={"error": str(e)}
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المدير"""
        return {
            **self.stats,
            "has_current_context": self.current_context is not None,
            "saved_contexts": len(self.saved_contexts),
            "history_size": len(self.context_history),
            "history_limit": self.history_limit,
            "current_project": self.current_context.project_name if self.current_context else None
        }


__all__ = ["ContextManager", "ProjectContext"]