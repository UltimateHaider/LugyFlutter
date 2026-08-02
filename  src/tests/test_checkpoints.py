"""
LugyFlutter - اختبارات وحدة نقاط التفتيش (Checkpoints)
اختبارات للتحقق من صحة عمل نظام نقاط التفتيش وإدارة الحالة
"""

import pytest
import json
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.checkpoint.checkpoint_manager import (
    CheckpointManager,
    ExecutionCheckpoint,
    CheckpointError,
    CheckpointSaveError,
    CheckpointRestoreError,
    CheckpointCorruptedError,
    NoCheckpointError
)
from src.checkpoint.checkpoint_storage import CheckpointStorage, CheckpointFile
from src.checkpoint.state_sync import StateSynchronizer, StateSnapshot


# ============================================================
# بيانات الاختبار (Fixtures)
# ============================================================

@pytest.fixture
def checkpoint_manager():
    """إنشاء مدير نقاط تفتيش للاختبار"""
    return CheckpointManager(max_checkpoints=5)


@pytest.fixture
def checkpoint_storage(tmp_path):
    """إنشاء نظام تخزين نقاط تفتيش للاختبار"""
    return CheckpointStorage(base_dir=str(tmp_path / "checkpoints"))


@pytest.fixture
def sample_state():
    """حالة عينة للاختبار"""
    return {
        "context": {
            "project_name": "TestProject",
            "current_view": "builder",
            "current_step": 5,
            "modifications_made": ["تعديل 1", "تعديل 2"]
        },
        "browser_state": {
            "url": "https://app.flutterflow.io",
            "title": "FlutterFlow Builder",
            "scroll_position": {"x": 0, "y": 100}
        },
        "stats": {
            "tasks_executed": 10,
            "successful_tasks": 8
        }
    }


@pytest.fixture
def mock_browser():
    """إنشاء متصفح وهمي للاختبار"""
    browser = Mock()
    browser.take_screenshot = AsyncMock(return_value=b"screenshot_data")
    browser.get_current_url = AsyncMock(return_value="https://app.flutterflow.io")
    browser.get_page_title = AsyncMock(return_value="FlutterFlow Builder")
    browser.execute_js = AsyncMock(return_value={"scrollX": 0, "scrollY": 100})
    browser.navigate_to = AsyncMock(return_value=True)
    browser.scroll_to = AsyncMock(return_value=True)
    return browser


# ============================================================
# اختبارات ExecutionCheckpoint
# ============================================================

class TestExecutionCheckpoint:
    """اختبارات نموذج نقطة التفتيش"""
    
    def test_create_checkpoint(self):
        """اختبار إنشاء نقطة تفتيش"""
        checkpoint = ExecutionCheckpoint(
            step=1,
            state={"test": "data"},
            description="نقطة اختبار"
        )
        
        assert checkpoint.step == 1
        assert checkpoint.state == {"test": "data"}
        assert checkpoint.description == "نقطة اختبار"
        assert checkpoint.checkpoint_id is not None
        assert checkpoint.timestamp is not None
        assert checkpoint.parent_id is None
    
    def test_checkpoint_with_screenshot(self):
        """اختبار نقطة تفتيش مع لقطة شاشة"""
        screenshot_data = b"test_screenshot"
        screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
        
        checkpoint = ExecutionCheckpoint(
            step=1,
            state={},
            screenshot=screenshot_b64,
            description="مع لقطة"
        )
        
        assert checkpoint.has_screenshot() is True
        assert checkpoint.get_screenshot_bytes() == screenshot_data
    
    def test_checkpoint_without_screenshot(self):
        """اختبار نقطة تفتيش بدون لقطة شاشة"""
        checkpoint = ExecutionCheckpoint(
            step=1,
            state={},
            description="بدون لقطة"
        )
        
        assert checkpoint.has_screenshot() is False
        assert checkpoint.get_screenshot_bytes() is None
    
    def test_checkpoint_with_parent(self):
        """اختبار نقطة تفتيش مع أب"""
        checkpoint = ExecutionCheckpoint(
            step=2,
            state={},
            parent_id="parent_123",
            description="نقطة فرعية"
        )
        
        assert checkpoint.parent_id == "parent_123"
    
    def test_checkpoint_to_dict(self):
        """اختبار تحويل نقطة التفتيش إلى قاموس"""
        checkpoint = ExecutionCheckpoint(
            step=1,
            state={"test": "data"},
            description="نقطة اختبار"
        )
        
        data = checkpoint.to_dict()
        assert data["step"] == 1
        assert data["state"] == {"test": "data"}
        assert data["description"] == "نقطة اختبار"
        assert "checkpoint_id" in data
        assert "timestamp" in data
    
    def test_checkpoint_from_dict(self):
        """اختبار إنشاء نقطة تفتيش من قاموس"""
        data = {
            "step": 1,
            "state": {"test": "data"},
            "description": "نقطة اختبار",
            "checkpoint_id": "test_id",
            "timestamp": "2024-01-01T00:00:00",
            "parent_id": None,
            "screenshot": None,
            "metadata": {}
        }
        
        checkpoint = ExecutionCheckpoint.from_dict(data)
        assert checkpoint.step == 1
        assert checkpoint.state == {"test": "data"}
        assert checkpoint.description == "نقطة اختبار"
        assert checkpoint.checkpoint_id == "test_id"


# ============================================================
# اختبارات CheckpointManager
# ============================================================

class TestCheckpointManager:
    """اختبارات مدير نقاط التفتيش"""
    
    def test_initialization(self, checkpoint_manager):
        """اختبار تهيئة المدير"""
        assert checkpoint_manager.max_checkpoints == 5
        assert checkpoint_manager.checkpoints == []
        assert checkpoint_manager.current_index == -1
        assert checkpoint_manager.branches == {}
    
    def test_save_checkpoint(self, checkpoint_manager, sample_state):
        """اختبار حفظ نقطة تفتيش"""
        checkpoint_id = checkpoint_manager.save_checkpoint(
            step=1,
            state=sample_state,
            description="نقطة اختبار"
        )
        
        assert checkpoint_id is not None
        assert len(checkpoint_manager.checkpoints) == 1
        assert checkpoint_manager.current_index == 0
        
        checkpoint = checkpoint_manager.get_current()
        assert checkpoint.step == 1
        assert checkpoint.description == "نقطة اختبار"
        assert checkpoint.state == sample_state
    
    def test_save_multiple_checkpoints(self, checkpoint_manager):
        """اختبار حفظ نقاط تفتيش متعددة"""
        for i in range(3):
            checkpoint_manager.save_checkpoint(
                step=i,
                state={"step": i},
                description=f"نقطة {i}"
            )
        
        assert len(checkpoint_manager.checkpoints) == 3
        assert checkpoint_manager.current_index == 2
        
        # التحقق من الترتيب
        for i, cp in enumerate(checkpoint_manager.checkpoints):
            assert cp.step == i
            assert cp.description == f"نقطة {i}"
    
    def test_undo(self, checkpoint_manager):
        """اختبار التراجع"""
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        assert checkpoint_manager.current_index == 1
        
        checkpoint = checkpoint_manager.undo()
        assert checkpoint.step == 1
        assert checkpoint_manager.current_index == 0
        
        checkpoint = checkpoint_manager.undo()
        assert checkpoint is None  # لا توجد نقاط سابقة
    
    def test_redo(self, checkpoint_manager):
        """اختبار إعادة التقدم"""
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        checkpoint_manager.undo()  # العودة إلى النقطة 1
        assert checkpoint_manager.current_index == 0
        
        checkpoint = checkpoint_manager.redo()
        assert checkpoint.step == 2
        assert checkpoint_manager.current_index == 1
        
        checkpoint = checkpoint_manager.redo()
        assert checkpoint is None  # لا توجد نقاط تالية
    
    def test_max_checkpoints_limit(self):
        """اختبار الحد الأقصى لنقاط التفتيش"""
        manager = CheckpointManager(max_checkpoints=3)
        
        for i in range(5):
            manager.save_checkpoint(i, {"step": i}, f"نقطة {i}")
        
        assert len(manager.checkpoints) == 3
        assert manager.checkpoints[0].step == 2  # أقدم نقطة محذوفة
        assert manager.checkpoints[-1].step == 4
    
    def test_get_current(self, checkpoint_manager):
        """اختبار الحصول على النقطة الحالية"""
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        current = checkpoint_manager.get_current()
        assert current.step == 2
        
        checkpoint_manager.undo()
        current = checkpoint_manager.get_current()
        assert current.step == 1
    
    def test_get_by_id(self, checkpoint_manager):
        """اختبار الحصول على نقطة تفتيش بالمعرف"""
        cp1 = checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        cp2 = checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        found = checkpoint_manager.get_by_id(cp2)
        assert found is not None
        assert found.step == 2
        
        not_found = checkpoint_manager.get_by_id("non_existent")
        assert not_found is None
    
    def test_get_by_step(self, checkpoint_manager):
        """اختبار الحصول على نقاط التفتيش برقم خطوة"""
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1 مكررة")
        
        results = checkpoint_manager.get_by_step(1)
        assert len(results) == 2
        assert all(cp.step == 1 for cp in results)
    
    def test_list_checkpoints(self, checkpoint_manager):
        """اختبار قائمة نقاط التفتيش"""
        for i in range(3):
            checkpoint_manager.save_checkpoint(i, {}, f"نقطة {i}")
        
        checkpoints = checkpoint_manager.list_checkpoints()
        assert len(checkpoints) == 3
        assert checkpoints[0]["step"] == 0
        assert checkpoints[0]["is_current"] is False
        assert checkpoints[-1]["is_current"] is True
    
    def test_restore_to(self, checkpoint_manager):
        """اختبار استعادة نقطة تفتيش محددة"""
        cp1 = checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        cp2 = checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        cp3 = checkpoint_manager.save_checkpoint(3, {}, "نقطة 3")
        
        restored = checkpoint_manager.restore_to(cp1)
        assert restored.checkpoint_id == cp1
        assert checkpoint_manager.current_index == 0
        
        restored = checkpoint_manager.restore_to(cp3)
        assert restored.checkpoint_id == cp3
        assert checkpoint_manager.current_index == 2
    
    def test_restore_to_not_found(self, checkpoint_manager):
        """اختبار استعادة نقطة تفتيش غير موجودة"""
        with pytest.raises(CheckpointRestoreError):
            checkpoint_manager.restore_to("non_existent")
    
    def test_delete_checkpoint(self, checkpoint_manager):
        """اختبار حذف نقطة تفتيش"""
        cp1 = checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        cp2 = checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        assert len(checkpoint_manager.checkpoints) == 2
        
        result = checkpoint_manager.delete_checkpoint(cp1)
        assert result is True
        assert len(checkpoint_manager.checkpoints) == 1
        assert checkpoint_manager.checkpoints[0].checkpoint_id == cp2
    
    def test_delete_not_found(self, checkpoint_manager):
        """اختبار حذف نقطة تفتيش غير موجودة"""
        result = checkpoint_manager.delete_checkpoint("non_existent")
        assert result is False
    
    def test_clear_all(self, checkpoint_manager):
        """اختبار مسح جميع نقاط التفتيش"""
        for i in range(3):
            checkpoint_manager.save_checkpoint(i, {}, f"نقطة {i}")
        
        assert len(checkpoint_manager.checkpoints) == 3
        
        checkpoint_manager.clear_all()
        assert len(checkpoint_manager.checkpoints) == 0
        assert checkpoint_manager.current_index == -1
    
    def test_export_checkpoints(self, checkpoint_manager, tmp_path):
        """اختبار تصدير نقاط التفتيش"""
        for i in range(3):
            checkpoint_manager.save_checkpoint(i, {"step": i}, f"نقطة {i}")
        
        file_path = tmp_path / "export.json"
        data = checkpoint_manager.export_checkpoints(str(file_path))
        
        assert file_path.exists()
        assert "checkpoints" in data
        assert len(data["checkpoints"]) == 3
        assert data["current_index"] == 2
    
    def test_import_checkpoints(self, checkpoint_manager, tmp_path):
        """اختبار استيراد نقاط التفتيش"""
        # تصدير نقاط التفتيش أولاً
        for i in range(3):
            checkpoint_manager.save_checkpoint(i, {"step": i}, f"نقطة {i}")
        
        file_path = tmp_path / "export.json"
        checkpoint_manager.export_checkpoints(str(file_path))
        
        # إنشاء مدير جديد واستيراد
        new_manager = CheckpointManager()
        result = new_manager.import_checkpoints(str(file_path))
        
        assert result is True
        assert len(new_manager.checkpoints) == 3
        assert new_manager.current_index == 2
    
    def test_branching(self, checkpoint_manager):
        """اختبار التفرع في نقاط التفتيش"""
        # إنشاء نقاط أساسية
        cp1 = checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        cp2 = checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        # التراجع وإنشاء فرع جديد
        checkpoint_manager.undo()
        cp3 = checkpoint_manager.save_checkpoint(3, {}, "نقطة 3 (فرع)")
        
        assert len(checkpoint_manager.checkpoints) == 2
        assert checkpoint_manager.checkpoints[0].checkpoint_id == cp1
        assert checkpoint_manager.checkpoints[1].checkpoint_id == cp3
        
        # التحقق من التفرع
        branch_info = checkpoint_manager.get_branch_info()
        assert branch_info["branches"] == 1
    
    def test_get_history(self, checkpoint_manager):
        """اختبار الحصول على تاريخ نقاط التفتيش"""
        for i in range(5):
            checkpoint_manager.save_checkpoint(i, {}, f"نقطة {i}")
        
        history = checkpoint_manager.get_history(limit=3)
        assert len(history) == 3
        assert history[0].step == 2
        assert history[-1].step == 4
    
    def test_get_stats(self, checkpoint_manager):
        """اختبار الحصول على الإحصائيات"""
        for i in range(3):
            checkpoint_manager.save_checkpoint(i, {}, f"نقطة {i}")
        
        stats = checkpoint_manager.get_stats()
        assert stats["current_size"] == 3
        assert stats["max_size"] == 5
        assert stats["current_index"] == 2
        assert stats["can_undo"] is True
        assert stats["can_redo"] is False
    
    def test_get_summary(self, checkpoint_manager):
        """اختبار الحصول على الملخص"""
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        checkpoint_manager.save_checkpoint(2, {}, "نقطة 2")
        
        summary = checkpoint_manager.get_summary()
        assert "نقاط التفتيش" in summary
        assert "2/5" in summary
        assert "نقطة 1" in summary
        assert "نقطة 2" in summary


# ============================================================
# اختبارات CheckpointStorage
# ============================================================

class TestCheckpointStorage:
    """اختبارات نظام تخزين نقاط التفتيش"""
    
    def test_initialization(self, checkpoint_storage):
        """اختبار تهيئة التخزين"""
        assert checkpoint_storage.base_dir.exists()
        assert checkpoint_storage.checkpoint_files == {}
        assert checkpoint_storage.stats["total_checkpoints"] == 0
    
    def test_save_and_load(self, checkpoint_storage):
        """اختبار حفظ وتحميل نقطة تفتيش"""
        data = {"test": "data", "step": 1}
        
        # حفظ
        checkpoint_id = "test_cp_1"
        file_path = checkpoint_storage.save(checkpoint_id, data)
        
        assert file_path is not None
        assert checkpoint_id in checkpoint_storage.checkpoint_files
        
        # تحميل
        loaded = checkpoint_storage.load(checkpoint_id)
        assert loaded == data
    
    def test_save_with_compression(self, checkpoint_storage):
        """اختبار حفظ مع ضغط"""
        data = {"large": "x" * 10000}  # بيانات كبيرة للضغط
        
        checkpoint_id = "compressed_cp"
        file_path = checkpoint_storage.save(checkpoint_id, data, compress=True)
        
        checkpoint_file = checkpoint_storage.checkpoint_files[checkpoint_id]
        assert checkpoint_file.compressed is True
        assert checkpoint_file.size > 0
    
    def test_save_without_compression(self, checkpoint_storage):
        """اختبار حفظ بدون ضغط"""
        data = {"small": "test"}
        
        checkpoint_id = "uncompressed_cp"
        file_path = checkpoint_storage.save(checkpoint_id, data, compress=False)
        
        checkpoint_file = checkpoint_storage.checkpoint_files[checkpoint_id]
        assert checkpoint_file.compressed is False
    
    def test_load_not_found(self, checkpoint_storage):
        """اختبار تحميل نقطة تفتيش غير موجودة"""
        result = checkpoint_storage.load("non_existent")
        assert result is None
    
    def test_delete(self, checkpoint_storage):
        """اختبار حذف نقطة تفتيش"""
        data = {"test": "data"}
        checkpoint_id = "test_cp"
        checkpoint_storage.save(checkpoint_id, data)
        
        assert checkpoint_id in checkpoint_storage.checkpoint_files
        
        result = checkpoint_storage.delete(checkpoint_id)
        assert result is True
        assert checkpoint_id not in checkpoint_storage.checkpoint_files
    
    def test_list_checkpoints(self, checkpoint_storage):
        """اختبار قائمة نقاط التفتيش"""
        for i in range(3):
            checkpoint_storage.save(f"cp_{i}", {"step": i})
        
        checkpoints = checkpoint_storage.list_checkpoints()
        assert len(checkpoints) == 3
        assert all("id" in cp for cp in checkpoints)
        assert all("size" in cp for cp in checkpoints)
    
    def test_get_size(self, checkpoint_storage):
        """اختبار الحصول على حجم التخزين"""
        for i in range(3):
            checkpoint_storage.save(f"cp_{i}", {"step": i})
        
        size_info = checkpoint_storage.get_size()
        assert size_info["checkpoint_count"] == 3
        assert size_info["total_size_bytes"] > 0
    
    def test_storage_limit(self, tmp_path):
        """اختبار حد التخزين"""
        storage = CheckpointStorage(
            base_dir=str(tmp_path / "checkpoints"),
            max_storage_mb=1  # حد صغير للتجربة
        )
        
        # حفظ نقاط تفتيش حتى يتجاوز الحد
        for i in range(20):
            storage.save(f"cp_{i}", {"data": "x" * 10000})
        
        # يجب أن يكون العدد أقل من 20 بسبب حذف القديم
        assert len(storage.checkpoint_files) < 20
        assert storage.stats["deletions"] > 0
    
    def test_export_all(self, checkpoint_storage, tmp_path):
        """اختبار تصدير جميع نقاط التفتيش"""
        for i in range(3):
            checkpoint_storage.save(f"cp_{i}", {"step": i})
        
        export_path = tmp_path / "export.zip"
        result = checkpoint_storage.export_all(str(export_path))
        
        assert result is not None
        assert export_path.exists()
    
    def test_import_from_zip(self, checkpoint_storage, tmp_path):
        """اختبار استيراد نقاط التفتيش من ZIP"""
        # تصدير أولاً
        for i in range(3):
            checkpoint_storage.save(f"cp_{i}", {"step": i})
        
        export_path = tmp_path / "export.zip"
        checkpoint_storage.export_all(str(export_path))
        
        # إنشاء تخزين جديد واستيراد
        new_storage = CheckpointStorage(base_dir=str(tmp_path / "new_checkpoints"))
        count = new_storage.import_from_zip(str(export_path))
        
        assert count > 0
        assert len(new_storage.checkpoint_files) > 0
    
    def test_clear_all(self, checkpoint_storage):
        """اختبار مسح جميع نقاط التفتيش"""
        for i in range(3):
            checkpoint_storage.save(f"cp_{i}", {"step": i})
        
        assert len(checkpoint_storage.checkpoint_files) == 3
        
        checkpoint_storage.clear_all()
        assert len(checkpoint_storage.checkpoint_files) == 0
        assert checkpoint_storage.stats["total_checkpoints"] == 0
    
    def test_get_stats(self, checkpoint_storage):
        """اختبار الحصول على إحصائيات التخزين"""
        for i in range(3):
            checkpoint_storage.save(f"cp_{i}", {"step": i})
        
        stats = checkpoint_storage.get_stats()
        assert stats["total_checkpoints"] == 3
        assert stats["total_size"] > 0
        assert "storage_dir" in stats


# ============================================================
# اختبارات StateSynchronizer
# ============================================================

class TestStateSynchronizer:
    """اختبارات مزامنة الحالة"""
    
    @pytest.fixture
    def synchronizer(self, mock_browser, checkpoint_manager):
        """إنشاء مزامن حالة للاختبار"""
        return StateSynchronizer(mock_browser, checkpoint_manager)
    
    @pytest.mark.asyncio
    async def test_capture_state(self, synchronizer, sample_state):
        """اختبار التقاط الحالة"""
        snapshot = await synchronizer.capture_state(sample_state["context"])
        
        assert snapshot is not None
        assert snapshot.context == sample_state["context"]
        assert snapshot.hash is not None
        assert synchronizer.current_snapshot is not None
    
    @pytest.mark.asyncio
    async def test_capture_state_with_checkpoint(self, synchronizer, sample_state, checkpoint_manager):
        """اختبار التقاط الحالة مع معرف نقطة تفتيش"""
        checkpoint_manager.save_checkpoint(1, {}, "نقطة 1")
        
        snapshot = await synchronizer.capture_state(sample_state["context"])
        
        assert snapshot.checkpoint_id is not None
        assert snapshot.checkpoint_id == checkpoint_manager.get_current().checkpoint_id
    
    def test_compare_with_current(self, synchronizer, sample_state):
        """اختبار مقارنة الحالة مع الحالية"""
        # التقاط الحالة أولاً
        snapshot = StateSnapshot(
            context=sample_state["context"],
            browser_state=sample_state["browser_state"]
        )
        synchronizer.current_snapshot = snapshot
        
        # مقارنة مع نفس الحالة
        result = synchronizer.compare_with_current({
            "context": sample_state["context"],
            "browser_state": sample_state["browser_state"]
        })
        
        assert result["has_changes"] is False
    
    def test_compare_with_different_state(self, synchronizer, sample_state):
        """اختبار مقارنة الحالة مع حالة مختلفة"""
        # التقاط الحالة أولاً
        snapshot = StateSnapshot(
            context=sample_state["context"],
            browser_state=sample_state["browser_state"]
        )
        synchronizer.current_snapshot = snapshot
        
        # مقارنة مع حالة مختلفة
        different_state = {
            "context": {"project_name": "DifferentProject"},
            "browser_state": {"url": "https://different.com"}
        }
        
        result = synchronizer.compare_with_current(different_state)
        assert result["has_changes"] is True
        assert len(result["context_changes"]) > 0
        assert len(result["browser_changes"]) > 0
    
    @pytest.mark.asyncio
    async def test_sync_with_browser(self, synchronizer, sample_state):
        """اختبار المزامنة مع المتصفح"""
        result = await synchronizer.sync_with_browser(sample_state["context"])
        assert result is True
        assert synchronizer.stats["syncs"] == 1
    
    def test_get_snapshot_history(self, synchronizer, sample_state):
        """اختبار الحصول على تاريخ اللقطات"""
        # إضافة بعض اللقطات
        for i in range(3):
            snapshot = StateSnapshot(
                context={"step": i},
                browser_state={}
            )
            synchronizer.previous_snapshots.append(snapshot)
        
        history = synchronizer.get_snapshot_history()
        assert len(history) == 3
        assert all("hash" in h for h in history)
    
    def test_clear_history(self, synchronizer, sample_state):
        """اختبار مسح تاريخ اللقطات"""
        for i in range(3):
            snapshot = StateSnapshot(
                context={"step": i},
                browser_state={}
            )
            synchronizer.previous_snapshots.append(snapshot)
        
        assert len(synchronizer.previous_snapshots) == 3
        
        synchronizer.clear_history()
        assert len(synchronizer.previous_snapshots) == 0
        assert synchronizer.current_snapshot is None


# ============================================================
# اختبارات الأخطاء (Error Tests)
# ============================================================

class TestCheckpointErrors:
    """اختبارات معالجة الأخطاء"""
    
    def test_no_checkpoint_error(self, checkpoint_manager):
        """اختبار خطأ عدم وجود نقاط تفتيش"""
        with pytest.raises(NoCheckpointError):
            checkpoint_manager.undo()
        
        with pytest.raises(NoCheckpointError):
            checkpoint_manager.redo()
    
    def test_checkpoint_corrupted_error(self, checkpoint_manager, tmp_path):
        """اختبار خطأ نقطة تفتيش تالفة"""
        # إنشاء ملف تالف
        file_path = tmp_path / "corrupted.json"
        file_path.write_text("{corrupted json")
        
        with pytest.raises(CheckpointCorruptedError):
            checkpoint_manager.import_checkpoints(str(file_path))
    
    def test_checkpoint_save_error(self, checkpoint_manager):
        """اختبار خطأ حفظ نقطة تفتيش"""
        # محاكاة خطأ في الحفظ
        with patch.object(checkpoint_manager, '_save_checkpoints', side_effect=Exception("Save error")):
            with pytest.raises(CheckpointSaveError):
                checkpoint_manager.save_checkpoint(1, {}, "نقطة اختبار")


# ============================================================
# تشغيل الاختبارات
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])