"""
LugyFlutter - مدير نقاط التفتيش (Checkpoint Manager)
نظام متقدم لحفظ واستعادة حالة التنفيذ مع دعم Undo/Redo
"""

import json
import base64
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path

from ..core.config import config
from ..core.exceptions import (
    CheckpointError,
    CheckpointSaveError,
    CheckpointRestoreError,
    CheckpointCorruptedError,
    NoCheckpointError
)
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


@dataclass
class ExecutionCheckpoint:
    """
    نقطة تفتيش في التنفيذ
    تحتوي على حالة الوكيل والمتصفح والسياق
    """
    step: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    state: Dict[str, Any] = field(default_factory=dict)
    screenshot: Optional[str] = None  # Base64 encoded
    description: str = ""
    checkpoint_id: str = field(default_factory=lambda: hashlib.md5(
        f"{datetime.now().isoformat()}".encode()
    ).hexdigest()[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل نقطة التفتيش إلى قاموس"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionCheckpoint':
        """إنشاء نقطة تفتيش من قاموس"""
        return cls(**data)
    
    def has_screenshot(self) -> bool:
        """التحقق من وجود لقطة شاشة"""
        return bool(self.screenshot)
    
    def get_screenshot_bytes(self) -> Optional[bytes]:
        """الحصول على لقطة الشاشة كـ bytes"""
        if self.screenshot:
            return base64.b64decode(self.screenshot)
        return None


class CheckpointManager:
    """
    مدير نقاط التفتيش المتقدم
    الميزات:
    - حفظ واستعادة نقاط التفتيش
    - Undo/Redo مع دعم التاريخ الكامل
    - تخزين لقطات الشاشة
    - إدارة الذاكرة والحد الأقصى
    - تصدير واستيراد نقاط التفتيش
    - دمج نقاط التفتيش (Branching)
    """
    
    def __init__(self, max_checkpoints: int = None, storage_dir: str = None):
        """
        تهيئة مدير نقاط التفتيش
        
        Args:
            max_checkpoints: الحد الأقصى لعدد نقاط التفتيش
            storage_dir: مجلد تخزين نقاط التفتيش
        """
        self.max_checkpoints = max_checkpoints or config.MAX_CHECKPOINTS
        self.storage_dir = Path(storage_dir or "logs/checkpoints")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoints: List[ExecutionCheckpoint] = []
        self.current_index = -1
        self.branches: Dict[str, List[str]] = {}  # تتبع فروع نقاط التفتيش
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "total_checkpoints": 0,
            "branches": 0
        }
        
        # إحصائيات
        self.stats = {
            "saves": 0,
            "restores": 0,
            "undos": 0,
            "redos": 0,
            "failures": 0,
            "checkpoint_size": 0
        }
        
        # تحميل نقاط التفتيش السابقة
        self._load_checkpoints()
        
        logger.info(f"تم تهيئة CheckpointManager مع {len(self.checkpoints)} نقطة تفتيش")
    
    def save_checkpoint(
        self,
        step: int,
        state: Dict[str, Any],
        screenshot: Optional[bytes] = None,
        description: str = "",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        حفظ نقطة تفتيش جديدة
        
        Args:
            step: رقم الخطوة
            state: حالة الوكيل
            screenshot: لقطة شاشة (اختياري)
            description: وصف النقطة
            metadata: بيانات إضافية
        
        Returns:
            str: معرف نقطة التفتيش
        """
        try:
            # تحويل لقطة الشاشة إلى Base64
            screenshot_b64 = None
            if screenshot:
                screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # الحصول على معرف الأصل (للتفرع)
            parent_id = None
            if self.current_index >= 0 and self.current_index < len(self.checkpoints):
                parent_id = self.checkpoints[self.current_index].checkpoint_id
            
            # إنشاء نقطة التفتيش
            checkpoint = ExecutionCheckpoint(
                step=step,
                state=state,
                screenshot=screenshot_b64,
                description=description,
                metadata=metadata or {},
                parent_id=parent_id
            )
            
            # حذف نقاط التفتيش بعد المؤشر الحالي (إذا كنا في وضع التراجع)
            if self.current_index < len(self.checkpoints) - 1:
                # حفظ نقاط التفتيش المحذوفة للتفرع
                removed = self.checkpoints[self.current_index + 1:]
                for cp in removed:
                    self.branches[cp.checkpoint_id] = [c.checkpoint_id for c in self.checkpoints]
                
                self.checkpoints = self.checkpoints[:self.current_index + 1]
            
            # إضافة نقطة التفتيش الجديدة
            self.checkpoints.append(checkpoint)
            self.current_index = len(self.checkpoints) - 1
            
            # إزالة أقدم نقطة إذا تجاوزنا الحد
            if len(self.checkpoints) > self.max_checkpoints:
                removed = self.checkpoints.pop(0)
                self.current_index -= 1
                logger.debug(f"إزالة نقطة تفتيش قديمة: {removed.checkpoint_id}")
            
            # تحديث الإحصائيات
            self.stats["saves"] += 1
            self.stats["checkpoint_size"] = len(json.dumps(checkpoint.to_dict()))
            self.metadata["total_checkpoints"] = len(self.checkpoints)
            
            # حفظ نقاط التفتيش
            self._save_checkpoints()
            
            logger.info(f"حفظ نقطة تفتيش: {checkpoint.checkpoint_id} - {description}")
            return checkpoint.checkpoint_id
            
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"فشل حفظ نقطة التفتيش: {e}")
            raise CheckpointSaveError(
                message="فشل حفظ نقطة التفتيش",
                details={"error": str(e), "step": step}
            )
    
    def undo(self) -> Optional[ExecutionCheckpoint]:
        """
        التراجع عن آخر إجراء (الرجوع إلى نقطة التفتيش السابقة)
        
        Returns:
            Optional[ExecutionCheckpoint]: نقطة التفتيش المستعادة
        """
        if self.current_index > 0:
            self.current_index -= 1
            self.stats["undos"] += 1
            
            checkpoint = self.checkpoints[self.current_index]
            logger.info(f"التراجع إلى نقطة التفتيش: {checkpoint.checkpoint_id}")
            return checkpoint
        
        raise NoCheckpointError("لا توجد نقاط تفتيش للتراجع عنها")
    
    def redo(self) -> Optional[ExecutionCheckpoint]:
        """
        إعادة التقدم (الرجوع إلى نقطة التفتيش التالية)
        
        Returns:
            Optional[ExecutionCheckpoint]: نقطة التفتيش المستعادة
        """
        if self.current_index < len(self.checkpoints) - 1:
            self.current_index += 1
            self.stats["redos"] += 1
            
            checkpoint = self.checkpoints[self.current_index]
            logger.info(f"إعادة التقدم إلى نقطة التفتيش: {checkpoint.checkpoint_id}")
            return checkpoint
        
        raise NoCheckpointError("لا توجد نقاط تفتيش للتقدم إليها")
    
    def get_current(self) -> Optional[ExecutionCheckpoint]:
        """
        الحصول على نقطة التفتيش الحالية
        
        Returns:
            Optional[ExecutionCheckpoint]: نقطة التفتيش الحالية
        """
        if 0 <= self.current_index < len(self.checkpoints):
            return self.checkpoints[self.current_index]
        return None
    
    def get_by_id(self, checkpoint_id: str) -> Optional[ExecutionCheckpoint]:
        """
        الحصول على نقطة تفتيش بواسطة المعرف
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
        
        Returns:
            Optional[ExecutionCheckpoint]: نقطة التفتيش المطلوبة
        """
        for checkpoint in self.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                return checkpoint
        return None
    
    def get_by_step(self, step: int) -> List[ExecutionCheckpoint]:
        """
        الحصول على نقاط التفتيش برقم خطوة معين
        
        Args:
            step: رقم الخطوة
        
        Returns:
            List[ExecutionCheckpoint]: قائمة بنقاط التفتيش
        """
        return [cp for cp in self.checkpoints if cp.step == step]
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        الحصول على قائمة مبسطة بنقاط التفتيش
        
        Returns:
            List[Dict]: قائمة نقاط التفتيش
        """
        return [
            {
                "index": i,
                "id": cp.checkpoint_id,
                "step": cp.step,
                "timestamp": cp.timestamp,
                "description": cp.description,
                "has_screenshot": cp.has_screenshot(),
                "is_current": i == self.current_index,
                "parent_id": cp.parent_id,
                "metadata": cp.metadata
            }
            for i, cp in enumerate(self.checkpoints)
        ]
    
    def get_history(self, limit: int = None) -> List[ExecutionCheckpoint]:
        """
        الحصول على تاريخ نقاط التفتيش
        
        Args:
            limit: عدد النقاط المطلوبة (اختياري)
        
        Returns:
            List[ExecutionCheckpoint]: قائمة بنقاط التفتيش
        """
        history = self.checkpoints.copy()
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_branch_info(self) -> Dict[str, Any]:
        """
        الحصول على معلومات التفرع
        
        Returns:
            Dict: معلومات التفرع
        """
        return {
            "branches": len(self.branches),
            "current_branch": self._get_current_branch(),
            "total_checkpoints": len(self.checkpoints),
            "current_position": self.current_index
        }
    
    def _get_current_branch(self) -> List[str]:
        """الحصول على الفرع الحالي"""
        if self.current_index < 0:
            return []
        return [cp.checkpoint_id for cp in self.checkpoints[:self.current_index + 1]]
    
    def restore_to(self, checkpoint_id: str) -> ExecutionCheckpoint:
        """
        استعادة نقطة تفتيش محددة
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
        
        Returns:
            ExecutionCheckpoint: نقطة التفتيش المستعادة
        """
        checkpoint = self.get_by_id(checkpoint_id)
        if not checkpoint:
            raise CheckpointRestoreError(
                checkpoint_id=checkpoint_id,
                message="نقطة التفتيش غير موجودة"
            )
        
        # العثور على مؤشر النقطة
        for i, cp in enumerate(self.checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                self.current_index = i
                self.stats["restores"] += 1
                
                logger.info(f"استعادة نقطة التفتيش: {checkpoint_id}")
                return checkpoint
        
        raise CheckpointRestoreError(
            checkpoint_id=checkpoint_id,
            message="فشل استعادة نقطة التفتيش"
        )
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        حذف نقطة تفتيش
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
        
        Returns:
            bool: نجاح الحذف
        """
        for i, cp in enumerate(self.checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                del self.checkpoints[i]
                if self.current_index >= i:
                    self.current_index -= 1
                self._save_checkpoints()
                logger.info(f"حذف نقطة التفتيش: {checkpoint_id}")
                return True
        
        return False
    
    def clear_all(self):
        """مسح جميع نقاط التفتيش"""
        self.checkpoints.clear()
        self.current_index = -1
        self.branches.clear()
        self._save_checkpoints()
        logger.info("تم مسح جميع نقاط التفتيش")
    
    def export_checkpoints(self, file_path: str = None) -> Dict[str, Any]:
        """
        تصدير نقاط التفتيش إلى ملف
        
        Args:
            file_path: مسار ملف التصدير
        
        Returns:
            Dict: بيانات نقاط التفتيش
        """
        data = {
            "metadata": self.metadata,
            "stats": self.stats,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "current_index": self.current_index,
            "branches": self.branches,
            "exported_at": datetime.now().isoformat()
        }
        
        if file_path:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            logger.info(f"تصدير نقاط التفتيش إلى: {file_path}")
        
        return data
    
    def import_checkpoints(self, data: Union[str, Dict[str, Any]]) -> bool:
        """
        استيراد نقاط التفتيش من ملف أو قاموس
        
        Args:
            data: بيانات نقاط التفتيش (مسار ملف أو قاموس)
        
        Returns:
            bool: نجاح الاستيراد
        """
        try:
            if isinstance(data, str):
                # مسار ملف
                path = Path(data)
                if not path.exists():
                    logger.error(f"الملف غير موجود: {data}")
                    return False
                data = json.loads(path.read_text(encoding='utf-8'))
            
            # استيراد البيانات
            self.checkpoints = [
                ExecutionCheckpoint.from_dict(cp) for cp in data.get("checkpoints", [])
            ]
            self.current_index = data.get("current_index", -1)
            self.branches = data.get("branches", {})
            self.metadata = data.get("metadata", {})
            
            self._save_checkpoints()
            logger.info(f"استيراد {len(self.checkpoints)} نقطة تفتيش")
            return True
            
        except Exception as e:
            logger.error(f"فشل استيراد نقاط التفتيش: {e}")
            raise CheckpointCorruptedError(
                message="فشل استيراد نقاط التفتيش",
                details={"error": str(e)}
            )
    
    def _save_checkpoints(self):
        """حفظ نقاط التفتيش في الملف"""
        try:
            data = self.export_checkpoints()
            file_path = self.storage_dir / "checkpoints.json"
            file_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"فشل حفظ نقاط التفتيش: {e}")
    
    def _load_checkpoints(self):
        """تحميل نقاط التفتيش من الملف"""
        file_path = self.storage_dir / "checkpoints.json"
        if file_path.exists():
            try:
                self.import_checkpoints(str(file_path))
            except Exception as e:
                logger.warning(f"فشل تحميل نقاط التفتيش: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المدير"""
        return {
            **self.stats,
            "current_size": len(self.checkpoints),
            "max_size": self.max_checkpoints,
            "current_index": self.current_index,
            "has_current": self.get_current() is not None,
            "can_undo": self.current_index > 0,
            "can_redo": self.current_index < len(self.checkpoints) - 1,
            "branches": len(self.branches),
            "storage_dir": str(self.storage_dir)
        }
    
    def get_summary(self) -> str:
        """الحصول على ملخص نقاط التفتيش"""
        if not self.checkpoints:
            return "📭 لا توجد نقاط تفتيش"
        
        current = self.get_current()
        current_info = f" (الحالية)" if current else ""
        
        summary = f"💾 نقاط التفتيش: {len(self.checkpoints)}/{self.max_checkpoints}{current_info}\n"
        
        for i, cp in enumerate(self.checkpoints):
            marker = "👉 " if i == self.current_index else "   "
            summary += f"{marker}[{i+1}] {cp.description} ({cp.timestamp[:19]})\n"
        
        return summary


__all__ = [
    "CheckpointManager",
    "ExecutionCheckpoint",
    "CheckpointError",
    "CheckpointSaveError",
    "CheckpointRestoreError",
    "CheckpointCorruptedError",
    "NoCheckpointError"
]