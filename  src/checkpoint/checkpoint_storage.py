"""
LugyFlutter - تخزين نقاط التفتيش (Checkpoint Storage)
نظام متقدم لتخزين واسترجاع نقاط التفتيش مع ضغط وترميز
"""

import json
import gzip
import base64
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, BinaryIO
from dataclasses import dataclass, field

from ..core.exceptions import StorageError, FileReadError, FileWriteError
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


@dataclass
class CheckpointFile:
    """
    تمثيل ملف نقطة تفتيش
    """
    checkpoint_id: str
    file_path: Path
    size: int
    compressed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_size_mb(self) -> float:
        """الحصول على حجم الملف بالميغابايت"""
        return self.size / (1024 * 1024)
    
    def get_size_kb(self) -> float:
        """الحصول على حجم الملف بالكيلوبايت"""
        return self.size / 1024


class CheckpointStorage:
    """
    نظام تخزين نقاط التفتيش المتقدم
    الميزات:
    - تخزين نقاط التفتيش بضغط gzip
    - ترميز Base64 للبيانات
    - إدارة مساحة التخزين
    - دعم التصدير والاستيراد
    - أرشفة نقاط التفتيش القديمة
    """
    
    def __init__(self, base_dir: str = "logs/checkpoints", max_storage_mb: int = 100):
        """
        تهيئة نظام التخزين
        
        Args:
            base_dir: المجلد الأساسي للتخزين
            max_storage_mb: الحد الأقصى لحجم التخزين بالميغابايت
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.max_storage_bytes = max_storage_mb * 1024 * 1024
        
        self.checkpoint_files: Dict[str, CheckpointFile] = {}
        self.index_file = self.base_dir / "index.json"
        
        # إحصائيات
        self.stats = {
            "total_checkpoints": 0,
            "total_size": 0,
            "compressed": 0,
            "uncompressed": 0,
            "saves": 0,
            "loads": 0,
            "deletions": 0
        }
        
        # تحميل الفهرس
        self._load_index()
        
        logger.info(f"تم تهيئة CheckpointStorage في: {self.base_dir}")
    
    def save(self, checkpoint_id: str, data: Dict[str, Any], compress: bool = True) -> str:
        """
        حفظ نقطة تفتيش
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
            data: بيانات نقطة التفتيش
            compress: ضغط البيانات
        
        Returns:
            str: مسار الملف المحفوظ
        """
        try:
            # تحويل البيانات إلى JSON
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            bytes_data = json_data.encode('utf-8')
            
            # ضغط إذا كان مطلوباً
            if compress and len(bytes_data) > 1024:  # ضغط إذا كان الحجم أكبر من 1KB
                compressed_data = gzip.compress(bytes_data)
                file_path = self.base_dir / f"{checkpoint_id}.json.gz"
            else:
                compressed_data = bytes_data
                file_path = self.base_dir / f"{checkpoint_id}.json"
            
            # حفظ الملف
            file_path.write_bytes(compressed_data)
            
            # تحديث الفهرس
            checkpoint_file = CheckpointFile(
                checkpoint_id=checkpoint_id,
                file_path=file_path,
                size=len(compressed_data),
                compressed=compress and len(bytes_data) > 1024,
                metadata={"original_size": len(bytes_data)}
            )
            
            self.checkpoint_files[checkpoint_id] = checkpoint_file
            self.stats["saves"] += 1
            self.stats["total_checkpoints"] = len(self.checkpoint_files)
            self.stats["total_size"] = sum(cf.size for cf in self.checkpoint_files.values())
            
            if checkpoint_file.compressed:
                self.stats["compressed"] += 1
            else:
                self.stats["uncompressed"] += 1
            
            # حفظ الفهرس
            self._save_index()
            
            # التحقق من مساحة التخزين
            self._check_storage_limit()
            
            logger.debug(f"حفظ نقطة التفتيش: {checkpoint_id}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"فشل حفظ نقطة التفتيش {checkpoint_id}: {e}")
            raise FileWriteError(
                file_path=str(self.base_dir / checkpoint_id),
                message="فشل حفظ نقطة التفتيش",
                details={"checkpoint_id": checkpoint_id, "error": str(e)}
            )
    
    def load(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        تحميل نقطة تفتيش
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
        
        Returns:
            Dict[str, Any]: بيانات نقطة التفتيش
        """
        try:
            if checkpoint_id not in self.checkpoint_files:
                logger.error(f"نقطة التفتيش غير موجودة: {checkpoint_id}")
                return None
            
            checkpoint_file = self.checkpoint_files[checkpoint_id]
            file_path = checkpoint_file.file_path
            
            if not file_path.exists():
                logger.error(f"ملف نقطة التفتيش غير موجود: {file_path}")
                return None
            
            # قراءة الملف
            data = file_path.read_bytes()
            
            # فك الضغط إذا كان مضغوطاً
            if checkpoint_file.compressed:
                data = gzip.decompress(data)
            
            # تحويل JSON
            json_data = data.decode('utf-8')
            result = json.loads(json_data)
            
            self.stats["loads"] += 1
            logger.debug(f"تحميل نقطة التفتيش: {checkpoint_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"فشل تحميل نقطة التفتيش {checkpoint_id}: {e}")
            raise FileReadError(
                file_path=str(self.base_dir / checkpoint_id),
                message="فشل تحميل نقطة التفتيش",
                details={"checkpoint_id": checkpoint_id, "error": str(e)}
            )
    
    def delete(self, checkpoint_id: str) -> bool:
        """
        حذف نقطة تفتيش
        
        Args:
            checkpoint_id: معرف نقطة التفتيش
        
        Returns:
            bool: نجاح الحذف
        """
        try:
            if checkpoint_id not in self.checkpoint_files:
                return False
            
            checkpoint_file = self.checkpoint_files[checkpoint_id]
            
            # حذف الملف
            if checkpoint_file.file_path.exists():
                checkpoint_file.file_path.unlink()
            
            # حذف من الفهرس
            del self.checkpoint_files[checkpoint_id]
            
            self.stats["deletions"] += 1
            self.stats["total_checkpoints"] = len(self.checkpoint_files)
            self.stats["total_size"] = sum(cf.size for cf in self.checkpoint_files.values())
            
            # حفظ الفهرس
            self._save_index()
            
            logger.debug(f"حذف نقطة التفتيش: {checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"فشل حذف نقطة التفتيش {checkpoint_id}: {e}")
            return False
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        قائمة نقاط التفتيش المحفوظة
        
        Returns:
            List[Dict]: قائمة نقاط التفتيش
        """
        return [
            {
                "id": cf.checkpoint_id,
                "size": cf.size,
                "size_kb": cf.get_size_kb(),
                "size_mb": cf.get_size_mb(),
                "compressed": cf.compressed,
                "created_at": cf.created_at,
                "path": str(cf.file_path),
                "metadata": cf.metadata
            }
            for cf in self.checkpoint_files.values()
        ]
    
    def get_size(self) -> Dict[str, Any]:
        """
        الحصول على معلومات حجم التخزين
        
        Returns:
            Dict: معلومات الحجم
        """
        total_size = self.stats["total_size"]
        return {
            "total_size_bytes": total_size,
            "total_size_kb": total_size / 1024,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_storage_bytes / (1024 * 1024),
            "usage_percent": (total_size / self.max_storage_bytes) * 100,
            "checkpoint_count": len(self.checkpoint_files)
        }
    
    def _check_storage_limit(self):
        """التحقق من حد التخزين وإزالة أقدم النقاط إذا لزم الأمر"""
        total_size = self.stats["total_size"]
        
        while total_size > self.max_storage_bytes and len(self.checkpoint_files) > 1:
            # العثور على أقدم نقطة تفتيش
            oldest = min(
                self.checkpoint_files.values(),
                key=lambda cf: cf.created_at
            )
            
            # حذفها
            self.delete(oldest.checkpoint_id)
            logger.warning(f"حذف نقطة تفتيش قديمة لتوفير مساحة: {oldest.checkpoint_id}")
            
            total_size = self.stats["total_size"]
    
    def _save_index(self):
        """حفظ الفهرس"""
        try:
            index_data = {
                "checkpoints": {
                    cf.checkpoint_id: {
                        "file_path": str(cf.file_path),
                        "size": cf.size,
                        "compressed": cf.compressed,
                        "created_at": cf.created_at,
                        "metadata": cf.metadata
                    }
                    for cf in self.checkpoint_files.values()
                },
                "stats": self.stats,
                "updated_at": datetime.now().isoformat()
            }
            
            self.index_file.write_text(
                json.dumps(index_data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"فشل حفظ الفهرس: {e}")
    
    def _load_index(self):
        """تحميل الفهرس"""
        if not self.index_file.exists():
            return
        
        try:
            index_data = json.loads(self.index_file.read_text(encoding='utf-8'))
            
            for cp_id, data in index_data.get("checkpoints", {}).items():
                file_path = Path(data["file_path"])
                
                # التحقق من وجود الملف
                if not file_path.exists():
                    continue
                
                self.checkpoint_files[cp_id] = CheckpointFile(
                    checkpoint_id=cp_id,
                    file_path=file_path,
                    size=data["size"],
                    compressed=data["compressed"],
                    created_at=data["created_at"],
                    metadata=data.get("metadata", {})
                )
            
            # تحديث الإحصائيات
            self.stats = index_data.get("stats", self.stats)
            self.stats["total_checkpoints"] = len(self.checkpoint_files)
            self.stats["total_size"] = sum(cf.size for cf in self.checkpoint_files.values())
            
            logger.info(f"تحميل {len(self.checkpoint_files)} نقطة تفتيش من الفهرس")
            
        except Exception as e:
            logger.error(f"فشل تحميل الفهرس: {e}")
    
    def export_all(self, export_path: str) -> str:
        """
        تصدير جميع نقاط التفتيش إلى ملف ZIP
        
        Args:
            export_path: مسار ملف التصدير
        
        Returns:
            str: مسار الملف المصدر
        """
        import zipfile
        
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # إضافة الفهرس
                zipf.write(self.index_file, self.index_file.name)
                
                # إضافة جميع نقاط التفتيش
                for cp_id, cp_file in self.checkpoint_files.items():
                    if cp_file.file_path.exists():
                        zipf.write(
                            cp_file.file_path,
                            f"checkpoints/{cp_file.file_path.name}"
                        )
            
            logger.info(f"تصدير {len(self.checkpoint_files)} نقطة تفتيش إلى: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"فشل تصدير نقاط التفتيش: {e}")
            raise StorageError(
                message="فشل تصدير نقاط التفتيش",
                details={"export_path": str(export_path), "error": str(e)}
            )
    
    def import_from_zip(self, import_path: str) -> int:
        """
        استيراد نقاط التفتيش من ملف ZIP
        
        Args:
            import_path: مسار ملف ZIP
        
        Returns:
            int: عدد نقاط التفتيش المستوردة
        """
        import zipfile
        import tempfile
        
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                raise FileNotFoundError(f"الملف غير موجود: {import_path}")
            
            count = 0
            temp_dir = Path(tempfile.mkdtemp())
            
            with zipfile.ZipFile(import_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # استيراد الفهرس
            index_file = temp_dir / self.index_file.name
            if index_file.exists():
                # نسخ الفهرس المؤقت
                shutil.copy2(index_file, self.index_file)
                self._load_index()
                count = len(self.checkpoint_files)
            
            # استيراد نقاط التفتيش
            checkpoint_dir = temp_dir / "checkpoints"
            if checkpoint_dir.exists():
                for file_path in checkpoint_dir.glob("*"):
                    # استخراج المعرف من اسم الملف
                    cp_id = file_path.stem.split('.')[0]
                    if cp_id not in self.checkpoint_files:
                        # نسخ الملف
                        dest_path = self.base_dir / file_path.name
                        shutil.copy2(file_path, dest_path)
                        
                        # تحديث الفهرس
                        self.checkpoint_files[cp_id] = CheckpointFile(
                            checkpoint_id=cp_id,
                            file_path=dest_path,
                            size=dest_path.stat().st_size,
                            compressed=file_path.suffix == '.gz',
                            created_at=datetime.now().isoformat()
                        )
                        count += 1
            
            # تحديث الإحصائيات
            self.stats["total_checkpoints"] = len(self.checkpoint_files)
            self.stats["total_size"] = sum(cf.size for cf in self.checkpoint_files.values())
            self._save_index()
            
            # تنظيف
            shutil.rmtree(temp_dir)
            
            logger.info(f"استيراد {count} نقطة تفتيش من: {import_path}")
            return count
            
        except Exception as e:
            logger.error(f"فشل استيراد نقاط التفتيش: {e}")
            raise StorageError(
                message="فشل استيراد نقاط التفتيش",
                details={"import_path": str(import_path), "error": str(e)}
            )
    
    def clear_all(self):
        """حذف جميع نقاط التفتيش"""
        try:
            # حذف الملفات
            for cp_id in list(self.checkpoint_files.keys()):
                self.delete(cp_id)
            
            # حذف الفهرس
            if self.index_file.exists():
                self.index_file.unlink()
            
            # إعادة تعيين الإحصائيات
            self.stats = {
                "total_checkpoints": 0,
                "total_size": 0,
                "compressed": 0,
                "uncompressed": 0,
                "saves": 0,
                "loads": 0,
                "deletions": 0
            }
            
            logger.info("تم حذف جميع نقاط التفتيش")
            
        except Exception as e:
            logger.error(f"فشل حذف نقاط التفتيش: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التخزين"""
        size_info = self.get_size()
        
        return {
            **self.stats,
            **size_info,
            "storage_dir": str(self.base_dir),
            "max_storage_mb": self.max_storage_bytes / (1024 * 1024),
            "index_exists": self.index_file.exists()
        }


__all__ = ["CheckpointStorage", "CheckpointFile"]