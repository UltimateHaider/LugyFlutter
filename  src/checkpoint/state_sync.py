"""
LugyFlutter - مزامنة الحالة (State Synchronization)
مزامنة حالة الوكيل مع المتصفح ونقاط التفتيش
"""

import asyncio
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from ..core.exceptions import BrowserError, CheckpointRestoreError
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


@dataclass
class StateSnapshot:
    """
    لقطة لحالة النظام
    """
    context: Dict[str, Any]
    browser_state: Dict[str, Any]
    checkpoint_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """حساب هاش للحالة"""
        data = f"{self.context}{self.browser_state}{self.timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    def is_identical(self, other: 'StateSnapshot') -> bool:
        """التحقق من تطابق حالتين"""
        return self.hash == other.hash


class StateSynchronizer:
    """
    مزامنة الحالة بين الوكيل والمتصفح ونقاط التفتيش
    الميزات:
    - التقاط حالة كاملة للنظام
    - مقارنة الحالات لاكتشاف التغييرات
    - استعادة الحالة من نقطة تفتيش
    - التحقق من صحة الحالة
    - تتبع التغييرات
    """
    
    def __init__(self, browser_manager, checkpoint_manager):
        """
        تهيئة مزامن الحالة
        
        Args:
            browser_manager: مدير المتصفح
            checkpoint_manager: مدير نقاط التفتيش
        """
        self.browser = browser_manager
        self.checkpoints = checkpoint_manager
        
        self.current_snapshot: Optional[StateSnapshot] = None
        self.previous_snapshots: List[StateSnapshot] = []
        self.max_history = 20
        
        # إحصائيات
        self.stats = {
            "snapshots_taken": 0,
            "snapshots_restored": 0,
            "comparisons": 0,
            "changes_detected": 0,
            "syncs": 0,
            "failures": 0
        }
        
        logger.info("تم تهيئة StateSynchronizer")
    
    async def capture_state(self, context: Dict[str, Any]) -> StateSnapshot:
        """
        التقاط حالة كاملة للنظام
        
        Args:
            context: سياق الوكيل
        
        Returns:
            StateSnapshot: لقطة الحالة
        """
        try:
            # التقاط حالة المتصفح
            browser_state = await self._capture_browser_state()
            
            # إنشاء لقطة الحالة
            snapshot = StateSnapshot(
                context=context,
                browser_state=browser_state,
                checkpoint_id=self._get_current_checkpoint_id()
            )
            
            # تحديث السجل
            self.previous_snapshots.append(snapshot)
            if len(self.previous_snapshots) > self.max_history:
                self.previous_snapshots.pop(0)
            
            self.current_snapshot = snapshot
            self.stats["snapshots_taken"] += 1
            
            logger.debug(f"التقاط حالة جديدة: {snapshot.hash}")
            return snapshot
            
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"فشل التقاط الحالة: {e}")
            raise BrowserError(
                message="فشل التقاط حالة النظام",
                details={"error": str(e)}
            )
    
    async def _capture_browser_state(self) -> Dict[str, Any]:
        """التقاط حالة المتصفح"""
        try:
            state = {
                "url": await self.browser.get_current_url(),
                "title": await self.browser.get_page_title(),
                "ready_state": await self.browser.execute_js("document.readyState"),
                "scroll_position": await self.browser.execute_js("""
                    ({ scrollX: window.scrollX, scrollY: window.scrollY })
                """),
                "viewport": await self.browser.execute_js("""
                    ({
                        width: window.innerWidth,
                        height: window.innerHeight
                    })
                """),
                "page_size": await self.browser.execute_js("""
                    ({
                        width: document.documentElement.scrollWidth,
                        height: document.documentElement.scrollHeight
                    })
                """)
            }
            
            return state
            
        except Exception as e:
            logger.warning(f"فشل التقاط حالة المتصفح: {e}")
            return {"error": str(e)}
    
    def _get_current_checkpoint_id(self) -> Optional[str]:
        """الحصول على معرف نقطة التفتيش الحالية"""
        current = self.checkpoints.get_current()
        return current.checkpoint_id if current else None
    
    async def restore_state(self, checkpoint_id: str) -> bool:
        """
        استعادة حالة من نقطة تفتيش
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
        
        Returns:
            bool: نجاح الاستعادة
        """
        try:
            # استعادة نقطة التفتيش
            checkpoint = self.checkpoints.restore_to(checkpoint_id)
            
            if not checkpoint:
                raise CheckpointRestoreError(
                    checkpoint_id=checkpoint_id,
                    message="فشل استعادة نقطة التفتيش"
                )
            
            # استعادة السياق
            context = checkpoint.state.get("context", {})
            
            # استعادة حالة المتصفح
            browser_state = checkpoint.state.get("browser_state", {})
            if browser_state:
                await self._restore_browser_state(browser_state)
            
            # تحديث اللقطة الحالية
            self.current_snapshot = StateSnapshot(
                context=context,
                browser_state=browser_state,
                checkpoint_id=checkpoint_id
            )
            
            self.stats["snapshots_restored"] += 1
            self.stats["syncs"] += 1
            
            logger.info(f"استعادة الحالة من نقطة التفتيش: {checkpoint_id}")
            return True
            
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"فشل استعادة الحالة: {e}")
            raise CheckpointRestoreError(
                checkpoint_id=checkpoint_id,
                message="فشل استعادة الحالة",
                details={"error": str(e)}
            )
    
    async def _restore_browser_state(self, browser_state: Dict[str, Any]):
        """استعادة حالة المتصفح"""
        try:
            # التنقل إلى URL
            if browser_state.get("url"):
                await self.browser.navigate_to(browser_state["url"])
            
            # التمرير إلى الموضع المحفوظ
            if browser_state.get("scroll_position"):
                scroll = browser_state["scroll_position"]
                await self.browser.scroll_to(scroll.get("scrollX", 0), scroll.get("scrollY", 0))
            
            logger.debug("تم استعادة حالة المتصفح")
            
        except Exception as e:
            logger.warning(f"فشل استعادة حالة المتصفح: {e}")
    
    def compare_with_current(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        مقارنة حالة مع الحالة الحالية
        
        Args:
            state: الحالة للمقارنة
        
        Returns:
            Dict: نتائج المقارنة
        """
        self.stats["comparisons"] += 1
        
        if not self.current_snapshot:
            return {
                "has_changes": True,
                "message": "لا توجد حالة حالية للمقارنة"
            }
        
        # مقارنة السياق
        context_changes = self._compare_dicts(
            self.current_snapshot.context,
            state.get("context", {})
        )
        
        # مقارنة حالة المتصفح
        browser_changes = self._compare_dicts(
            self.current_snapshot.browser_state,
            state.get("browser_state", {})
        )
        
        has_changes = context_changes or browser_changes
        
        if has_changes:
            self.stats["changes_detected"] += 1
        
        return {
            "has_changes": has_changes,
            "context_changes": context_changes,
            "browser_changes": browser_changes,
            "change_count": len(context_changes) + len(browser_changes)
        }
    
    def _compare_dicts(self, dict1: Dict, dict2: Dict) -> List[str]:
        """مقارنة قاموسين وإرجاع التغييرات"""
        changes = []
        
        if not dict1:
            return ["الحالة الأولى فارغة"]
        
        if not dict2:
            return ["الحالة الثانية فارغة"]
        
        for key in set(dict1.keys()) | set(dict2.keys()):
            if key not in dict1:
                changes.append(f"المفتاح '{key}' تم إضافته")
            elif key not in dict2:
                changes.append(f"المفتاح '{key}' تم حذفه")
            elif dict1[key] != dict2[key]:
                changes.append(
                    f"المفتاح '{key}' تغير من '{dict1[key]}' إلى '{dict2[key]}'"
                )
        
        return changes
    
    async def sync_with_browser(self, context: Dict[str, Any]) -> bool:
        """
        مزامنة الحالة مع المتصفح
        
        Args:
            context: سياق الوكيل
        
        Returns:
            bool: نجاح المزامنة
        """
        try:
            # التقاط حالة جديدة
            snapshot = await self.capture_state(context)
            
            # مقارنة مع الحالة السابقة
            if self.previous_snapshots and len(self.previous_snapshots) > 1:
                previous = self.previous_snapshots[-2]
                comparison = self.compare_with_current({
                    "context": previous.context,
                    "browser_state": previous.browser_state
                })
                
                if comparison["has_changes"]:
                    logger.debug(f"تغييرات مكتشفة: {comparison['change_count']}")
            
            self.stats["syncs"] += 1
            return True
            
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"فشل المزامنة: {e}")
            return False
    
    def get_snapshot_history(self) -> List[Dict[str, Any]]:
        """الحصول على تاريخ اللقطات"""
        return [
            {
                "hash": s.hash,
                "timestamp": s.timestamp,
                "checkpoint_id": s.checkpoint_id,
                "context_keys": list(s.context.keys()) if s.context else [],
                "has_browser_state": bool(s.browser_state)
            }
            for s in self.previous_snapshots
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المزامن"""
        return {
            **self.stats,
            "has_current_snapshot": self.current_snapshot is not None,
            "history_size": len(self.previous_snapshots),
            "max_history": self.max_history,
            "current_hash": self.current_snapshot.hash if self.current_snapshot else None
        }
    
    def clear_history(self):
        """مسح تاريخ اللقطات"""
        self.previous_snapshots.clear()
        self.current_snapshot = None
        logger.info("تم مسح تاريخ اللقطات")


__all__ = ["StateSynchronizer", "StateSnapshot"]