"""
LugyFlutter - سجل المشاريع (Project Registry)
تسجيل وإدارة المشاريع المنسوخة والمشاريع المعروفة
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

from ..core.exceptions import RegistryError
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


@dataclass
class ProjectRecord:
    """
    سجل مشروع في قاعدة البيانات
    """
    project_name: str
    project_id: Optional[str] = None
    project_url: Optional[str] = None
    source_type: str = "flutterflow"  # flutterflow, figma, lovable, custom
    source_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    status: str = "active"  # active, archived, deleted
    modifications_count: int = 0
    clone_source: Optional[str] = None  # من أي مشروع تم النسخ
    
    def update_access(self):
        """تحديث وقت آخر وصول"""
        self.last_accessed = datetime.now().isoformat()
    
    def increment_modifications(self):
        """زيادة عدد التعديلات"""
        self.modifications_count += 1
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل السجل إلى قاموس"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectRecord':
        """إنشاء سجل من قاموس"""
        return cls(**data)


class ProjectRegistry:
    """
    سجل المشاريع - إدارة وتتبع المشاريع
    الميزات:
    - تسجيل المشاريع الجديدة
    - تتبع المشاريع المنسوخة من مصادر خارجية
    - البحث عن المشاريع
    - تصنيف المشاريع بالعلامات
    - أرشفة المشاريع القديمة
    - تصدير واستيراد السجل
    """
    
    def __init__(self, storage_file: str = "logs/projects_registry.json"):
        """
        تهيئة سجل المشاريع
        
        Args:
            storage_file: مسار ملف التخزين
        """
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.projects: Dict[str, ProjectRecord] = {}
        self.source_index: Dict[str, List[str]] = {}  # مصدر -> قائمة المشاريع
        
        # إحصائيات
        self.stats = {
            "total_projects": 0,
            "active_projects": 0,
            "archived_projects": 0,
            "cloned_projects": 0,
            "created_today": 0,
            "last_export": None
        }
        
        # تحميل السجل
        self._load_registry()
        
        logger.info(f"تم تهيئة ProjectRegistry مع {len(self.projects)} مشروع")
    
    def register_project(
        self,
        project_name: str,
        project_id: str = None,
        project_url: str = None,
        source_type: str = "flutterflow",
        source_url: str = None,
        clone_source: str = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> ProjectRecord:
        """
        تسجيل مشروع جديد في السجل
        
        Args:
            project_name: اسم المشروع
            project_id: معرف المشروع
            project_url: رابط المشروع
            source_type: نوع المصدر
            source_url: رابط المصدر
            clone_source: مصدر النسخ
            metadata: بيانات إضافية
            tags: علامات المشروع
        
        Returns:
            ProjectRecord: سجل المشروع
        """
        # التحقق من وجود المشروع
        if project_name in self.projects:
            logger.warning(f"المشروع موجود بالفعل: {project_name}")
            return self.projects[project_name]
        
        # إنشاء السجل
        record = ProjectRecord(
            project_name=project_name,
            project_id=project_id,
            project_url=project_url,
            source_type=source_type,
            source_url=source_url,
            clone_source=clone_source,
            metadata=metadata or {},
            tags=tags or []
        )
        
        # تحديث الإحصائيات
        if source_type in ["figma", "lovable"]:
            self.stats["cloned_projects"] += 1
        
        # حفظ السجل
        self.projects[project_name] = record
        
        # تحديث فهرس المصادر
        if source_url:
            if source_url not in self.source_index:
                self.source_index[source_url] = []
            self.source_index[source_url].append(project_name)
        
        # تحديث الإحصائيات
        self.stats["total_projects"] = len(self.projects)
        self.stats["active_projects"] = sum(1 for p in self.projects.values() if p.status == "active")
        self.stats["archived_projects"] = sum(1 for p in self.projects.values() if p.status == "archived")
        
        # حساب المشاريع التي تم إنشاؤها اليوم
        today = datetime.now().date().isoformat()
        self.stats["created_today"] = sum(
            1 for p in self.projects.values()
            if p.created_at.startswith(today)
        )
        
        # حفظ السجل
        self._save_registry()
        
        logger.info(f"تسجيل مشروع جديد: {project_name} (المصدر: {source_type})")
        return record
    
    def get_project(self, project_name: str) -> Optional[ProjectRecord]:
        """
        الحصول على سجل مشروع
        
        Args:
            project_name: اسم المشروع
        
        Returns:
            Optional[ProjectRecord]: سجل المشروع
        """
        if project_name in self.projects:
            record = self.projects[project_name]
            record.update_access()
            self._save_registry()
            return record
        
        logger.debug(f"المشروع غير موجود: {project_name}")
        return None
    
    def update_project(self, project_name: str, **kwargs) -> Optional[ProjectRecord]:
        """
        تحديث سجل مشروع
        
        Args:
            project_name: اسم المشروع
            **kwargs: القيم المراد تحديثها
        
        Returns:
            Optional[ProjectRecord]: السجل المحدث
        """
        if project_name not in self.projects:
            logger.warning(f"المشروع غير موجود: {project_name}")
            return None
        
        record = self.projects[project_name]
        
        # تحديث الحقول
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        record.updated_at = datetime.now().isoformat()
        self._save_registry()
        
        logger.debug(f"تحديث المشروع: {project_name}")
        return record
    
    def register_clone(
        self,
        source_url: str,
        flutterflow_project: str,
        source_type: str = "figma",
        metadata: Dict[str, Any] = None
    ) -> ProjectRecord:
        """
        تسجيل مشروع منسوخ من مصدر خارجي
        
        Args:
            source_url: رابط المصدر
            flutterflow_project: اسم المشروع في FlutterFlow
            source_type: نوع المصدر (figma, lovable)
            metadata: بيانات إضافية
        
        Returns:
            ProjectRecord: سجل المشروع
        """
        # التحقق من وجود المشروع
        if flutterflow_project in self.projects:
            # تحديث السجل الحالي
            record = self.projects[flutterflow_project]
            record.source_url = source_url
            record.source_type = source_type
            record.clone_source = source_url
            record.metadata.update(metadata or {})
            record.updated_at = datetime.now().isoformat()
            self._save_registry()
            return record
        
        # إنشاء سجل جديد
        return self.register_project(
            project_name=flutterflow_project,
            source_type=source_type,
            source_url=source_url,
            clone_source=source_url,
            metadata=metadata,
            tags=["cloned"]
        )
    
    def get_clones_from_source(self, source_url: str) -> List[ProjectRecord]:
        """
        الحصول على جميع المشاريع المنسوخة من مصدر معين
        
        Args:
            source_url: رابط المصدر
        
        Returns:
            List[ProjectRecord]: قائمة المشاريع
        """
        if source_url not in self.source_index:
            return []
        
        return [
            self.projects[name]
            for name in self.source_index[source_url]
            if name in self.projects
        ]
    
    def search_projects(
        self,
        query: str = None,
        tags: List[str] = None,
        source_type: str = None,
        status: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        البحث عن المشاريع
        
        Args:
            query: نص البحث
            tags: قائمة العلامات
            source_type: نوع المصدر
            status: حالة المشروع
            limit: الحد الأقصى للنتائج
        
        Returns:
            List[Dict]: نتائج البحث
        """
        results = []
        
        for name, record in self.projects.items():
            # تصفية حسب الحالة
            if status and record.status != status:
                continue
            
            # تصفية حسب نوع المصدر
            if source_type and record.source_type != source_type:
                continue
            
            # تصفية حسب العلامات
            if tags and not any(tag in record.tags for tag in tags):
                continue
            
            # تصفية حسب النص
            if query:
                query_lower = query.lower()
                if (query_lower not in name.lower() and
                    query_lower not in (record.project_id or "").lower() and
                    query_lower not in (record.source_url or "").lower() and
                    query_lower not in " ".join(record.tags).lower()):
                    continue
            
            results.append({
                "name": name,
                "project_id": record.project_id,
                "source_type": record.source_type,
                "source_url": record.source_url,
                "status": record.status,
                "tags": record.tags,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "last_accessed": record.last_accessed,
                "modifications_count": record.modifications_count
            })
        
        # ترتيب حسب آخر وصول
        results.sort(key=lambda x: x["last_accessed"], reverse=True)
        
        return results[:limit]
    
    def archive_project(self, project_name: str) -> bool:
        """
        أرشفة مشروع
        
        Args:
            project_name: اسم المشروع
        
        Returns:
            bool: نجاح الأرشفة
        """
        if project_name not in self.projects:
            return False
        
        record = self.projects[project_name]
        record.status = "archived"
        record.updated_at = datetime.now().isoformat()
        
        self.stats["active_projects"] -= 1
        self.stats["archived_projects"] += 1
        
        self._save_registry()
        logger.info(f"أرشفة المشروع: {project_name}")
        return True
    
    def restore_project(self, project_name: str) -> bool:
        """
        استعادة مشروع من الأرشيف
        
        Args:
            project_name: اسم المشروع
        
        Returns:
            bool: نجاح الاستعادة
        """
        if project_name not in self.projects:
            return False
        
        record = self.projects[project_name]
        if record.status != "archived":
            return False
        
        record.status = "active"
        record.updated_at = datetime.now().isoformat()
        
        self.stats["active_projects"] += 1
        self.stats["archived_projects"] -= 1
        
        self._save_registry()
        logger.info(f"استعادة المشروع: {project_name}")
        return True
    
    def add_tags(self, project_name: str, tags: List[str]) -> bool:
        """
        إضافة علامات لمشروع
        
        Args:
            project_name: اسم المشروع
            tags: قائمة العلامات
        
        Returns:
            bool: نجاح الإضافة
        """
        if project_name not in self.projects:
            return False
        
        record = self.projects[project_name]
        for tag in tags:
            if tag not in record.tags:
                record.tags.append(tag)
        
        record.updated_at = datetime.now().isoformat()
        self._save_registry()
        
        logger.debug(f"إضافة علامات للمشروع {project_name}: {tags}")
        return True
    
    def remove_tags(self, project_name: str, tags: List[str]) -> bool:
        """
        إزالة علامات من مشروع
        
        Args:
            project_name: اسم المشروع
            tags: قائمة العلامات
        
        Returns:
            bool: نجاح الإزالة
        """
        if project_name not in self.projects:
            return False
        
        record = self.projects[project_name]
        record.tags = [t for t in record.tags if t not in tags]
        record.updated_at = datetime.now().isoformat()
        
        self._save_registry()
        logger.debug(f"إزالة علامات من المشروع {project_name}: {tags}")
        return True
    
    def get_all_tags(self) -> List[str]:
        """
        الحصول على جميع العلامات المستخدمة
        
        Returns:
            List[str]: قائمة العلامات
        """
        tags = set()
        for record in self.projects.values():
            tags.update(record.tags)
        return sorted(list(tags))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات السجل
        
        Returns:
            Dict: الإحصائيات
        """
        return {
            **self.stats,
            "total_projects": len(self.projects),
            "source_types": {
                source_type: sum(1 for p in self.projects.values() if p.source_type == source_type)
                for source_type in set(p.source_type for p in self.projects.values())
            },
            "tags_used": len(self.get_all_tags()),
            "storage_file": str(self.storage_file)
        }
    
    def _save_registry(self):
        """حفظ السجل في الملف"""
        try:
            data = {
                "projects": {
                    name: record.to_dict()
                    for name, record in self.projects.items()
                },
                "source_index": self.source_index,
                "stats": self.stats,
                "updated_at": datetime.now().isoformat()
            }
            
            self.storage_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"فشل حفظ السجل: {e}")
            raise RegistryError(
                message="فشل حفظ سجل المشاريع",
                details={"error": str(e)}
            )
    
    def _load_registry(self):
        """تحميل السجل من الملف"""
        if not self.storage_file.exists():
            return
        
        try:
            data = json.loads(self.storage_file.read_text(encoding='utf-8'))
            
            self.projects = {
                name: ProjectRecord.from_dict(record)
                for name, record in data.get("projects", {}).items()
            }
            
            self.source_index = data.get("source_index", {})
            self.stats = data.get("stats", self.stats)
            
            logger.info(f"تحميل {len(self.projects)} مشروع من السجل")
            
        except Exception as e:
            logger.error(f"فشل تحميل السجل: {e}")
            # إنشاء نسخة احتياطية من الملف التالف
            if self.storage_file.exists():
                backup_path = self.storage_file.with_suffix(".json.bak")
                self.storage_file.rename(backup_path)
                logger.warning(f"تم إنشاء نسخة احتياطية من السجل التالف: {backup_path}")
    
    def export_registry(self, export_path: str) -> str:
        """
        تصدير السجل إلى ملف
        
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
                "projects": {
                    name: record.to_dict()
                    for name, record in self.projects.items()
                },
                "source_index": self.source_index,
                "stats": self.stats,
                "tags": self.get_all_tags()
            }
            
            export_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            self.stats["last_export"] = datetime.now().isoformat()
            logger.info(f"تصدير السجل إلى: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"فشل تصدير السجل: {e}")
            raise RegistryError(
                message="فشل تصدير سجل المشاريع",
                details={"error": str(e)}
            )
    
    def clear_registry(self):
        """مسح جميع السجلات"""
        self.projects.clear()
        self.source_index.clear()
        self.stats = {k: 0 for k in self.stats.keys()}
        self._save_registry()
        logger.warning("تم مسح جميع السجلات")


__all__ = ["ProjectRegistry", "ProjectRecord"]