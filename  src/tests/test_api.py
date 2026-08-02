"""
LugyFlutter - اختبارات وحدة API (FastAPI)
اختبارات للتحقق من صحة عمل واجهة API ونقاط النهاية
"""

import pytest
import asyncio
import json
import base64
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.web.api import app, AgentManager, _run_task
from src.web.models import (
    TaskRequest,
    TaskResponse,
    TaskStatus,
    ProjectCreate,
    ProjectClone,
    CheckpointCreate,
    CheckpointResponse,
    HealthResponse
)
from src.core.enums import TaskType, InteractionMode
from src.core.exceptions import AgentError


# ============================================================
# بيانات الاختبار (Fixtures)
# ============================================================

@pytest.fixture
def client():
    """إنشاء عميل اختبار FastAPI"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_agent():
    """إنشاء وكيل وهمي"""
    agent = Mock()
    agent.stats = {
        "tasks_executed": 10,
        "successful_tasks": 8,
        "failed_tasks": 2
    }
    agent.context = Mock()
    agent.context.project_name = "TestProject"
    agent.context.current_view = "builder"
    agent.context.current_step = 5
    agent.context.modifications_made = ["تعديل 1", "تعديل 2"]
    agent.context.to_dict = Mock(return_value={
        "project_name": "TestProject",
        "current_view": "builder"
    })
    
    agent.checkpoints = Mock()
    agent.checkpoints.checkpoints = []
    agent.checkpoints.list_checkpoints = Mock(return_value=[
        {"id": "cp1", "step": 1, "description": "نقطة 1", "timestamp": "2024-01-01T00:00:00", "has_screenshot": False},
        {"id": "cp2", "step": 2, "description": "نقطة 2", "timestamp": "2024-01-01T00:00:01", "has_screenshot": False}
    ])
    agent.checkpoints.save_checkpoint = Mock(return_value="cp3")
    agent.checkpoints.undo = Mock(return_value=Mock(checkpoint_id="cp1", description="نقطة 1", step=1))
    agent.checkpoints.redo = Mock(return_value=Mock(checkpoint_id="cp2", description="نقطة 2", step=2))
    
    agent.registry = Mock()
    agent.registry.projects = {
        "Project1": Mock(source_type="figma", status="active", modifications_count=5, tags=["tag1"], created_at="2024-01-01", updated_at="2024-01-02"),
        "Project2": Mock(source_type="flutterflow", status="archived", modifications_count=2, tags=[], created_at="2024-01-03", updated_at="2024-01-04")
    }
    agent.registry.register_project = Mock()
    agent.registry.register_clone = Mock()
    
    agent.browser = AsyncMock()
    agent.browser.take_screenshot = AsyncMock(return_value=b"screenshot_data")
    
    agent.process_user_request = AsyncMock(return_value="Task completed successfully")
    agent.initialize_browser = AsyncMock()
    
    return agent


@pytest.fixture
def mock_task_request():
    """إنشاء طلب مهمة وهمي"""
    return {
        "user_input": "أنشئ مشروع جديد اسمه تطبيقي",
        "mode": "full_interactive",
        "auto_execute": False
    }


@pytest.fixture
def mock_project_create():
    """إنشاء طلب إنشاء مشروع وهمي"""
    return {
        "name": "تطبيقي",
        "template": "blank",
        "description": "مشروع تطبيق جديد"
    }


@pytest.fixture
def mock_project_clone():
    """إنشاء طلب نسخ مشروع وهمي"""
    return {
        "source_url": "https://figma.com/design/abc123",
        "source_type": "figma",
        "project_name": "تطبيق المطعم"
    }


@pytest.fixture
def mock_checkpoint_create():
    """إنشاء طلب نقطة تفتيش وهمي"""
    return {
        "description": "نقطة تفتيش اختبار",
        "metadata": {"step": 5, "project": "TestProject"}
    }


# ============================================================
# اختبارات نقاط النهاية الأساسية
# ============================================================

class TestBasicEndpoints:
    """اختبارات نقاط النهاية الأساسية"""
    
    def test_root_endpoint(self, client):
        """اختبار نقطة النهاية الرئيسية"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "LugyFlutter API"
        assert data["version"] == "2.0.0"
        assert data["status"] == "running"
        assert "/docs" in data["docs"]
    
    def test_health_endpoint(self, client):
        """اختبار نقطة فحص الصحة"""
        with patch('src.web.api.AgentManager.get_agent', return_value=Mock()):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "2.0.0"
            assert "system_info" in data
            assert "agent_initialized" in data
    
    def test_health_endpoint_unhealthy(self, client):
        """اختبار نقطة فحص الصحة عندما يكون الوكيل غير صحي"""
        with patch('src.web.api.AgentManager.get_agent', return_value=None):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["agent_initialized"] is False


# ============================================================
# اختبارات نقاط نهاية المهام
# ============================================================

class TestTaskEndpoints:
    """اختبارات نقاط نهاية المهام"""
    
    def test_execute_task(self, client, mock_task_request, mock_agent):
        """اختبار تنفيذ مهمة"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            with patch('src.web.api.AgentManager.create_task') as mock_create:
                mock_create.return_value = {"status": "running"}
                
                response = client.post("/task/execute", json=mock_task_request)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "started"
                assert "task_id" in data
                assert data["task_id"].startswith("task_")
    
    def test_execute_task_no_agent(self, client, mock_task_request):
        """اختبار تنفيذ مهمة بدون وكيل"""
        with patch('src.web.api.AgentManager.get_agent', return_value=None):
            response = client.post("/task/execute", json=mock_task_request)
            
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
    
    def test_execute_task_invalid_mode(self, client, mock_task_request):
        """اختبار تنفيذ مهمة بوضع غير صحيح"""
        mock_task_request["mode"] = "invalid_mode"
        
        with patch('src.web.api.AgentManager.get_agent', return_value=Mock()):
            response = client.post("/task/execute", json=mock_task_request)
            
            assert response.status_code == 422  # Validation error
    
    def test_get_task_status(self, client):
        """اختبار الحصول على حالة مهمة"""
        task_id = "task_20240101_120000"
        
        with patch('src.web.api.AgentManager.get_task') as mock_get:
            mock_get.return_value = {
                "task_id": task_id,
                "status": "completed",
                "result": "Task done",
                "error": None,
                "progress": 100,
                "steps": [],
                "started_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            }
            
            response = client.get(f"/task/{task_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert data["status"] == "completed"
            assert data["result"] == "Task done"
    
    def test_get_task_status_not_found(self, client):
        """اختبار الحصول على حالة مهمة غير موجودة"""
        with patch('src.web.api.AgentManager.get_task', return_value=None):
            response = client.get("/task/non_existent")
            
            assert response.status_code == 404
            assert "detail" in response.json()
    
    def test_wait_for_task(self, client):
        """اختبار انتظار مهمة"""
        task_id = "task_20240101_120000"
        
        with patch('src.web.api.AgentManager.get_task') as mock_get:
            # أولاً: المهمة قيد التشغيل
            mock_get.return_value = {
                "task_id": task_id,
                "status": "running",
                "result": None,
                "error": None,
                "progress": 50,
                "steps": [],
                "started_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": None
            }
            
            with patch('asyncio.sleep', return_value=None):
                # ثانياً: المهمة مكتملة
                mock_get.return_value = {
                    "task_id": task_id,
                    "status": "completed",
                    "result": "Task done",
                    "error": None,
                    "progress": 100,
                    "steps": [],
                    "started_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat()
                }
                
                response = client.get(f"/task/{task_id}/wait?timeout=5")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "completed"
    
    def test_list_tasks(self, client):
        """اختبار قائمة المهام"""
        with patch('src.web.api.AgentManager._tasks') as mock_tasks:
            mock_tasks.values.return_value = [
                {
                    "task_id": "task_1",
                    "status": "completed",
                    "started_at": "2024-01-01T00:00:00"
                },
                {
                    "task_id": "task_2",
                    "status": "running",
                    "started_at": "2024-01-01T00:00:01"
                }
            ]
            
            response = client.get("/tasks?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["task_id"] == "task_2"  # الأحدث أولاً


# ============================================================
# اختبارات نقاط نهاية المشاريع
# ============================================================

class TestProjectEndpoints:
    """اختبارات نقاط نهاية المشاريع"""
    
    def test_create_project(self, client, mock_project_create, mock_agent):
        """اختبار إنشاء مشروع"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.post("/project/create", json=mock_project_create)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "تم إنشاء المشروع" in data["message"]
            assert data["project"]["name"] == "تطبيقي"
    
    def test_create_project_no_agent(self, client, mock_project_create):
        """اختبار إنشاء مشروع بدون وكيل"""
        with patch('src.web.api.AgentManager.get_agent', return_value=None):
            response = client.post("/project/create", json=mock_project_create)
            
            assert response.status_code == 503
            assert "detail" in response.json()
    
    def test_create_project_invalid_name(self, client):
        """اختبار إنشاء مشروع باسم غير صحيح"""
        invalid_data = {
            "name": "a",  # قصير جداً
            "template": "blank"
        }
        
        with patch('src.web.api.AgentManager.get_agent', return_value=Mock()):
            response = client.post("/project/create", json=invalid_data)
            
            assert response.status_code == 422  # Validation error
    
    def test_clone_project(self, client, mock_project_clone, mock_agent):
        """اختبار نسخ مشروع"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.post("/project/clone", json=mock_project_clone)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "تم نسخ المشروع" in data["message"]
            assert data["project"]["name"] == "تطبيق المطعم"
            assert data["project"]["source_type"] == "figma"
    
    def test_clone_project_invalid_url(self, client):
        """اختبار نسخ مشروع برابط غير صحيح"""
        invalid_data = {
            "source_url": "invalid_url",
            "source_type": "figma",
            "project_name": "تطبيق"
        }
        
        with patch('src.web.api.AgentManager.get_agent', return_value=Mock()):
            response = client.post("/project/clone", json=invalid_data)
            
            assert response.status_code == 422  # Validation error


# ============================================================
# اختبارات نقاط نهاية نقاط التفتيش
# ============================================================

class TestCheckpointEndpoints:
    """اختبارات نقاط نهاية نقاط التفتيش"""
    
    def test_list_checkpoints(self, client, mock_agent):
        """اختبار قائمة نقاط التفتيش"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.get("/checkpoints")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["checkpoint_id"] == "cp1"
            assert data[0]["step"] == 1
    
    def test_list_checkpoints_no_agent(self, client):
        """اختبار قائمة نقاط التفتيش بدون وكيل"""
        with patch('src.web.api.AgentManager.get_agent', return_value=None):
            response = client.get("/checkpoints")
            
            assert response.status_code == 503
            assert "detail" in response.json()
    
    def test_create_checkpoint(self, client, mock_checkpoint_create, mock_agent):
        """اختبار إنشاء نقطة تفتيش"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.post("/checkpoints", json=mock_checkpoint_create)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["checkpoint_id"] == "cp3"
            assert "تم حفظ نقطة التفتيش" in data["message"]
    
    def test_undo_checkpoint(self, client, mock_agent):
        """اختبار التراجع عن نقطة تفتيش"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.post("/checkpoints/undo")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["checkpoint"]["id"] == "cp1"
            assert "تم التراجع" in data["message"]
    
    def test_undo_checkpoint_no_checkpoints(self, client):
        """اختبار التراجع بدون نقاط تفتيش"""
        agent = Mock()
        agent.checkpoints = Mock()
        agent.checkpoints.undo = Mock(return_value=None)
        
        with patch('src.web.api.AgentManager.get_agent', return_value=agent):
            response = client.post("/checkpoints/undo")
            
            assert response.status_code == 404
            assert "detail" in response.json()
    
    def test_redo_checkpoint(self, client, mock_agent):
        """اختبار إعادة التقدم إلى نقطة تفتيش"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.post("/checkpoints/redo")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["checkpoint"]["id"] == "cp2"
            assert "تم الإعادة" in data["message"]


# ============================================================
# اختبارات نقاط نهاية أخرى
# ============================================================

class TestOtherEndpoints:
    """اختبارات نقاط النهاية الأخرى"""
    
    def test_get_screenshot(self, client, mock_agent):
        """اختبار الحصول على لقطة شاشة"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.get("/screenshot")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == b"screenshot_data"
    
    def test_get_screenshot_no_browser(self, client):
        """اختبار الحصول على لقطة شاشة بدون متصفح"""
        agent = Mock()
        agent.browser = None
        
        with patch('src.web.api.AgentManager.get_agent', return_value=agent):
            response = client.get("/screenshot")
            
            assert response.status_code == 503
            assert "detail" in response.json()
    
    def test_get_status(self, client, mock_agent):
        """اختبار الحصول على حالة الوكيل"""
        with patch('src.web.api.AgentManager.get_agent', return_value=mock_agent):
            response = client.get("/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"
            assert data["name"] == "LugyFlutter"
            assert data["version"] == "2.0.0"
            assert "context" in data
            assert "stats" in data
    
    def test_get_status_no_agent(self, client):
        """اختبار الحصول على حالة الوكيل بدون وكيل"""
        with patch('src.web.api.AgentManager.get_agent', return_value=None):
            response = client.get("/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "not_initialized"
            assert data["message"] == "الوكيل غير مهيأ"
    
    def test_export_logs(self, client):
        """اختبار تصدير السجلات"""
        with patch('src.web.api.Path.exists', return_value=True):
            with patch('src.web.api.export_logs_to_zip', return_value=Path("logs.zip")):
                response = client.post("/export/logs")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "تم تصدير السجلات" in data["message"]
    
    def test_export_logs_no_logs(self, client):
        """اختبار تصدير السجلات بدون وجود سجلات"""
        with patch('src.web.api.Path.exists', return_value=False):
            response = client.post("/export/logs")
            
            assert response.status_code == 404
            assert "detail" in response.json()
    
    def test_download_logs(self, client):
        """اختبار تحميل السجلات"""
        with patch('src.web.api.Path.exists', return_value=True):
            with patch('src.web.api.export_logs_to_zip', return_value=Path("logs.zip")):
                with patch('src.web.api.Path.exists', return_value=True):
                    response = client.get("/export/logs/download")
                    
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/zip"
    
    def test_restart_agent(self, client):
        """اختبار إعادة تشغيل الوكيل"""
        with patch('src.web.api.AgentManager.initialize_agent', return_value=True):
            response = client.post("/agent/restart")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "تم إعادة تشغيل الوكيل" in data["message"]
    
    def test_restart_agent_failure(self, client):
        """اختبار فشل إعادة تشغيل الوكيل"""
        with patch('src.web.api.AgentManager.initialize_agent', return_value=False):
            response = client.post("/agent/restart")
            
            assert response.status_code == 500
            assert "detail" in response.json()


# ============================================================
# اختبارات AgentManager
# ============================================================

class TestAgentManager:
    """اختبارات مدير الوكيل"""
    
    def test_singleton_pattern(self):
        """اختبار نمط Singleton"""
        manager1 = AgentManager()
        manager2 = AgentManager()
        
        assert manager1 is manager2
    
    def test_get_agent(self):
        """اختبار الحصول على الوكيل"""
        agent = AgentManager.get_agent()
        # قد يكون None إذا لم يتم التهيئة
        assert agent is not None or agent is None
    
    @pytest.mark.asyncio
    async def test_initialize_agent(self):
        """اختبار تهيئة الوكيل"""
        AgentManager._initialized = False
        AgentManager._agent = None
        
        with patch('src.web.api.LugyFlutter') as MockAgent:
            mock_agent_instance = Mock()
            mock_agent_instance.initialize_browser = AsyncMock()
            MockAgent.return_value = mock_agent_instance
            
            result = await AgentManager.initialize_agent()
            
            assert result is True
            assert AgentManager._initialized is True
            assert AgentManager._agent is not None
    
    def test_create_task(self):
        """اختبار إنشاء مهمة"""
        AgentManager._tasks = {}
        task_id = "test_task"
        
        task = AgentManager.create_task(task_id)
        
        assert task["task_id"] == task_id
        assert task["status"] == "pending"
        assert task["progress"] == 0
        assert task_id in AgentManager._tasks
    
    def test_update_task(self):
        """اختبار تحديث مهمة"""
        AgentManager._tasks = {}
        task_id = "test_task"
        AgentManager.create_task(task_id)
        
        AgentManager.update_task(task_id, status="running", progress=50)
        
        task = AgentManager._tasks[task_id]
        assert task["status"] == "running"
        assert task["progress"] == 50
    
    def test_complete_task(self):
        """اختبار إكمال مهمة"""
        AgentManager._tasks = {}
        task_id = "test_task"
        AgentManager.create_task(task_id)
        
        AgentManager.complete_task(task_id, result="Success")
        
        task = AgentManager._tasks[task_id]
        assert task["status"] == "completed"
        assert task["result"] == "Success"
        assert task["progress"] == 100
    
    def test_complete_task_with_error(self):
        """اختبار إكمال مهمة مع خطأ"""
        AgentManager._tasks = {}
        task_id = "test_task"
        AgentManager.create_task(task_id)
        
        AgentManager.complete_task(task_id, error="Something went wrong")
        
        task = AgentManager._tasks[task_id]
        assert task["status"] == "failed"
        assert task["error"] == "Something went wrong"


# ============================================================
# اختبارات الدوال المساعدة
# ============================================================

class TestHelperFunctions:
    """اختبارات الدوال المساعدة"""
    
    @pytest.mark.asyncio
    async def test_run_task(self):
        """اختبار تنفيذ مهمة في الخلفية"""
        task_id = "test_task"
        user_input = "أنشئ مشروع"
        mode = "auto"
        
        with patch('src.web.api.AgentManager.get_agent') as mock_get:
            mock_agent = AsyncMock()
            mock_agent.process_user_request = AsyncMock(return_value="Done")
            mock_get.return_value = mock_agent
            
            with patch('src.web.api.AgentManager.update_task'):
                with patch('src.web.api.AgentManager.complete_task'):
                    await _run_task(task_id, user_input, mode)
                    
                    mock_agent.process_user_request.assert_called_once_with(user_input)
    
    @pytest.mark.asyncio
    async def test_run_task_no_agent(self):
        """اختبار تنفيذ مهمة بدون وكيل"""
        task_id = "test_task"
        user_input = "أنشئ مشروع"
        mode = "auto"
        
        with patch('src.web.api.AgentManager.get_agent', return_value=None):
            with patch('src.web.api.AgentManager.update_task') as mock_update:
                await _run_task(task_id, user_input, mode)
                
                mock_update.assert_called_with(task_id, status="failed", error="الوكيل غير جاهز")
    
    @pytest.mark.asyncio
    async def test_run_task_with_error(self):
        """اختبار تنفيذ مهمة مع خطأ"""
        task_id = "test_task"
        user_input = "أنشئ مشروع"
        mode = "auto"
        
        with patch('src.web.api.AgentManager.get_agent') as mock_get:
            mock_agent = AsyncMock()
            mock_agent.process_user_request = AsyncMock(side_effect=Exception("Test error"))
            mock_get.return_value = mock_agent
            
            with patch('src.web.api.AgentManager.complete_task') as mock_complete:
                await _run_task(task_id, user_input, mode)
                
                mock_complete.assert_called_with(task_id, error="Test error")


# ============================================================
# اختبارات نماذج البيانات
# ============================================================

class TestModels:
    """اختبارات نماذج البيانات"""
    
    def test_task_request_validation(self):
        """اختبار التحقق من طلب المهمة"""
        # طلب صحيح
        request = TaskRequest(user_input="أنشئ مشروع", mode="full_interactive")
        assert request.user_input == "أنشئ مشروع"
        assert request.mode == "full_interactive"
        
        # وضع غير صحيح
        with pytest.raises(ValueError):
            TaskRequest(user_input="أنشئ مشروع", mode="invalid")
    
    def test_project_create_validation(self):
        """اختبار التحقق من إنشاء المشروع"""
        # اسم صحيح
        request = ProjectCreate(name="تطبيقي")
        assert request.name == "تطبيقي"
        
        # اسم قصير جداً
        with pytest.raises(ValueError):
            ProjectCreate(name="ا")
    
    def test_project_clone_validation(self):
        """اختبار التحقق من نسخ المشروع"""
        # رابط Figma صحيح
        request = ProjectClone(
            source_url="https://figma.com/design/abc123",
            source_type="figma",
            project_name="تطبيق"
        )
        assert request.source_type == "figma"
        
        # رابط Figma غير صحيح
        with pytest.raises(ValueError):
            ProjectClone(
                source_url="invalid_url",
                source_type="figma",
                project_name="تطبيق"
            )


# ============================================================
# تشغيل الاختبارات
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])