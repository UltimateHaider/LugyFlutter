"""
LugyFlutter - إعدادات الاختبارات (conftest.py)
ملف يحتوي على الإعدادات المشتركة و Fixtures لجميع اختبارات LugyFlutter
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import config
from src.core.enums import TaskType, InteractionMode
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# إعدادات pytest
# ============================================================

def pytest_configure(config):
    """تكوين pytest قبل تشغيل الاختبارات"""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as asynchronous"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as unit test"
    )


@pytest.fixture(scope="session")
def event_loop():
    """إنشاء حلقة أحداث للاختبارات غير المتزامنة"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# Fixtures للمجلدات والملفات المؤقتة
# ============================================================

@pytest.fixture(scope="function")
def temp_dir():
    """إنشاء مجلد مؤقت للاختبارات"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_log_dir(temp_dir):
    """إنشاء مجلد سجلات مؤقت"""
    log_dir = temp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


@pytest.fixture(scope="function")
def temp_checkpoint_dir(temp_dir):
    """إنشاء مجلد نقاط تفتيش مؤقت"""
    checkpoint_dir = temp_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    return checkpoint_dir


@pytest.fixture(scope="function")
def sample_json_file(temp_dir):
    """إنشاء ملف JSON عينة"""
    file_path = temp_dir / "test.json"
    data = {
        "name": "TestProject",
        "version": "1.0.0",
        "settings": {
            "debug": True,
            "timeout": 30
        },
        "items": ["item1", "item2", "item3"]
    }
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return file_path


# ============================================================
# Fixtures للبيانات
# ============================================================

@pytest.fixture
def sample_project_data():
    """بيانات مشروع عينة"""
    return {
        "name": "MyApp",
        "description": "تطبيق عينة للاختبار",
        "template": "blank",
        "status": "active",
        "tags": ["test", "sample"]
    }


@pytest.fixture
def sample_checkpoint_data():
    """بيانات نقطة تفتيش عينة"""
    return {
        "step": 1,
        "state": {
            "context": {
                "project_name": "MyApp",
                "current_view": "builder"
            },
            "browser_state": {
                "url": "https://app.flutterflow.io",
                "title": "FlutterFlow Builder"
            }
        },
        "description": "نقطة تفتيش اختبارية",
        "metadata": {"test": True}
    }


@pytest.fixture
def sample_user_inputs():
    """نصوص إدخال مستخدم عينة"""
    return {
        "create_project": "أنشئ مشروع جديد اسمه تطبيقي",
        "edit_project": "عدل مشروع التسوق وأضف زر في الصفحة الرئيسية",
        "clone_figma": "انسخ هذا التصميم من Figma https://figma.com/design/abc123",
        "clone_lovable": "نسخ من Lovable https://lovable.com/project/xyz",
        "analyze": "حلل تصميم المشروع الحالي",
        "unknown": "مرحباً كيف حالك"
    }


@pytest.fixture
def sample_widgets():
    """قائمة Widgets عينة"""
    return ["Column", "Row", "Container", "Text", "Button", "Image"]


@pytest.fixture
def sample_colors():
    """قائمة ألوان عينة"""
    return ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]


# ============================================================
# Fixtures للـ Mock Objects
# ============================================================

@pytest.fixture
def mock_browser():
    """إنشاء متصفح وهمي"""
    browser = AsyncMock()
    
    # دوال التنقل
    browser.navigate_to = AsyncMock(return_value=True)
    browser.get_current_url = AsyncMock(return_value="https://app.flutterflow.io")
    browser.get_page_title = AsyncMock(return_value="FlutterFlow Builder")
    
    # دوال التفاعل
    browser.execute_js = AsyncMock(return_value={"result": "success"})
    browser.take_screenshot = AsyncMock(return_value=b"screenshot_data")
    browser.find_element = AsyncMock(return_value={
        "x": 100,
        "y": 200,
        "width": 50,
        "height": 30,
        "text": "Test Element",
        "selector": "#test-element"
    })
    browser.click_element = AsyncMock(return_value=True)
    browser.type_text = AsyncMock(return_value=True)
    browser.wait_for_element = AsyncMock(return_value=True)
    
    # دوال إضافية
    browser.scroll_to = AsyncMock(return_value=True)
    browser.scroll_to_element = AsyncMock(return_value=True)
    browser.refresh = AsyncMock(return_value=True)
    browser.go_back = AsyncMock(return_value=True)
    browser.close = AsyncMock()
    
    return browser


@pytest.fixture
def mock_llm():
    """إنشاء نموذج LLM وهمي"""
    llm = Mock()
    
    # محاكاة الاستدعاء
    mock_response = Mock()
    mock_response.content = "ناتج من النموذج اللغوي"
    llm.invoke = Mock(return_value=mock_response)
    
    # محاكاة القنوات
    llm.generate = Mock(return_value=[mock_response])
    llm.agenerate = AsyncMock(return_value=[mock_response])
    
    return llm


@pytest.fixture
def mock_controller():
    """إنشاء Controller وهمي"""
    controller = Mock()
    
    # تسجيل الإجراءات
    controller.action = Mock(return_value=lambda x: x)
    controller.actions = {}
    controller.register = Mock()
    
    return controller


@pytest.fixture
def mock_checkpoint_manager():
    """إنشاء مدير نقاط تفتيش وهمي"""
    manager = Mock()
    
    # دوال الحفظ والاستعادة
    manager.save_checkpoint = Mock(return_value="cp_123456")
    manager.undo = Mock(return_value=Mock(
        checkpoint_id="cp_previous",
        step=1,
        description="نقطة سابقة",
        state={"context": {"project_name": "PreviousProject"}}
    ))
    manager.redo = Mock(return_value=Mock(
        checkpoint_id="cp_next",
        step=2,
        description="نقطة تالية",
        state={"context": {"project_name": "NextProject"}}
    ))
    manager.get_current = Mock(return_value=Mock(
        checkpoint_id="cp_current",
        step=1,
        description="نقطة حالية"
    ))
    manager.list_checkpoints = Mock(return_value=[
        {"id": "cp1", "step": 1, "description": "نقطة 1", "timestamp": "2024-01-01T00:00:00", "has_screenshot": False},
        {"id": "cp2", "step": 2, "description": "نقطة 2", "timestamp": "2024-01-01T00:00:01", "has_screenshot": False}
    ])
    manager.clear_all = Mock()
    
    manager.checkpoints = []
    
    return manager


@pytest.fixture
def mock_context():
    """إنشاء سياق مشروع وهمي"""
    context = Mock()
    context.project_name = "MyApp"
    context.project_id = "ff_123456"
    context.current_view = "builder"
    context.current_page = "HomePage"
    context.current_step = 5
    context.modifications_made = ["إضافة Column", "تعديل Text"]
    context.selected_widgets = ["Column", "Text"]
    context.source_url = "https://figma.com/design/abc123"
    context.to_dict = Mock(return_value={
        "project_name": "MyApp",
        "project_id": "ff_123456",
        "current_view": "builder",
        "current_page": "HomePage",
        "current_step": 5,
        "modifications_made": ["إضافة Column", "تعديل Text"]
    })
    context.update = Mock(return_value=context)
    context.add_modification = Mock()
    context.add_action = Mock()
    context.increment_step = Mock()
    
    return context


@pytest.fixture
def mock_registry():
    """إنشاء سجل مشاريع وهمي"""
    registry = Mock()
    
    # دوال التسجيل
    registry.register_project = Mock(return_value=Mock(
        project_name="NewProject",
        source_type="figma",
        status="active"
    ))
    registry.register_clone = Mock(return_value=Mock(
        project_name="ClonedProject",
        source_type="figma",
        status="active"
    ))
    registry.get_project = Mock(return_value=Mock(
        project_name="ExistingProject",
        source_type="flutterflow",
        status="active"
    ))
    registry.search_projects = Mock(return_value=[
        {"name": "Project1", "source_type": "figma"},
        {"name": "Project2", "source_type": "flutterflow"}
    ])
    registry.get_stats = Mock(return_value={
        "total_projects": 5,
        "active_projects": 3,
        "archived_projects": 2
    })
    
    registry.projects = {
        "Project1": Mock(source_type="figma", status="active", modifications_count=5, tags=["tag1"]),
        "Project2": Mock(source_type="flutterflow", status="archived", modifications_count=2, tags=[])
    }
    
    return registry


@pytest.fixture
def mock_conversation_logger():
    """إنشاء سجل محادثات وهمي"""
    logger = Mock()
    
    logger.add = Mock()
    logger.add_user_message = Mock()
    logger.add_agent_message = Mock()
    logger.add_system_message = Mock()
    logger.get_last = Mock(return_value=[
        Mock(role="user", content="Hello", timestamp="2024-01-01T00:00:00"),
        Mock(role="agent", content="Hi there", timestamp="2024-01-01T00:00:01")
    ])
    logger.search = Mock(return_value=[
        Mock(role="user", content="test message", timestamp="2024-01-01T00:00:00")
    ])
    logger.get_stats = Mock(return_value={
        "total_entries": 10,
        "user_messages": 5,
        "agent_messages": 4,
        "system_messages": 1
    })
    logger.clear = Mock()
    logger.save = Mock()
    
    logger.entries = []
    
    return logger


# ============================================================
# Fixtures للوكيل الرئيسي
# ============================================================

@pytest.fixture
def mock_agent():
    """إنشاء وكيل وهمي كامل"""
    agent = Mock()
    
    # دوال أساسية
    agent.initialize_browser = AsyncMock(return_value=True)
    agent.process_user_request = AsyncMock(return_value="تم التنفيذ بنجاح")
    agent.start_conversation = AsyncMock()
    
    # مكونات الوكيل
    agent.context = Mock()
    agent.context.project_name = "MyApp"
    agent.context.current_view = "builder"
    agent.context.modifications_made = ["تعديل 1"]
    agent.context.to_dict = Mock(return_value={"project_name": "MyApp"})
    
    agent.stats = {
        "tasks_executed": 10,
        "successful_tasks": 8,
        "failed_tasks": 2,
        "total_steps": 50,
        "start_time": datetime.now().isoformat(),
        "end_time": None
    }
    
    agent.browser = AsyncMock()
    agent.llm = Mock()
    agent.controller = Mock()
    agent.extractor = Mock()
    
    agent.checkpoints = Mock()
    agent.checkpoints.checkpoints = []
    agent.checkpoints.save_checkpoint = Mock(return_value="cp_123")
    agent.checkpoints.undo = Mock()
    agent.checkpoints.redo = Mock()
    agent.checkpoints.list_checkpoints = Mock(return_value=[])
    
    agent.registry = Mock()
    agent.registry.projects = {}
    agent.registry.register_project = Mock()
    agent.registry.register_clone = Mock()
    
    agent.conversation = Mock()
    agent.conversation.add = Mock()
    
    agent.logger = Mock()
    
    return agent


@pytest.fixture
def mock_agent_with_browser(mock_agent, mock_browser):
    """إنشاء وكيل مع متصفح وهمي"""
    mock_agent.browser = mock_browser
    mock_agent.is_initialized = True
    return mock_agent


# ============================================================
# Fixtures للـ API
# ============================================================

@pytest.fixture
def mock_api_client():
    """إنشاء عميل API وهمي"""
    client = Mock()
    
    # دوال GET
    client.get = AsyncMock(return_value={"status": "ok"})
    client.get_task_status = AsyncMock(return_value={"status": "completed", "result": "done"})
    client.get_status = AsyncMock(return_value={"status": "running", "version": "2.0.0"})
    client.get_checkpoints = AsyncMock(return_value=[{"id": "cp1", "step": 1}])
    client.get_screenshot = AsyncMock(return_value=b"screenshot_data")
    
    # دوال POST
    client.post = AsyncMock(return_value={"status": "success"})
    client.execute_task = AsyncMock(return_value={"task_id": "task_123", "status": "started"})
    client.create_checkpoint = AsyncMock(return_value={"checkpoint_id": "cp_123", "status": "success"})
    client.undo_checkpoint = AsyncMock(return_value={"status": "success"})
    client.redo_checkpoint = AsyncMock(return_value={"status": "success"})
    client.export_logs = AsyncMock(return_value={"file_path": "logs.zip", "status": "success"})
    
    return client


# ============================================================
# Fixtures للاختبارات المتكاملة
# ============================================================

@pytest.fixture
def integration_test_data():
    """بيانات للاختبارات المتكاملة"""
    return {
        "project": {
            "name": "IntegrationTestProject",
            "description": "مشروع اختبار متكامل",
            "template": "blank"
        },
        "user_inputs": [
            "أنشئ مشروع جديد اسمه IntegrationTestProject",
            "أضف Column و Text في الصفحة الرئيسية",
            "غيّر لون الخلفية إلى #6200EE"
        ],
        "expected_widgets": ["Column", "Row", "Text", "Container"],
        "expected_colors": ["#6200EE", "#03DAC6"]
    }


# ============================================================
# Fixtures للبيانات غير المتزامنة
# ============================================================

@pytest.fixture
def async_event_loop():
    """إنشاء حلقة أحداث للاختبارات غير المتزامنة"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ============================================================
# دوال مساعدة للاختبارات
# ============================================================

def create_mock_response(data=None, status_code=200, error=None):
    """إنشاء استجابة وهمية للاختبارات"""
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=data or {})
    response.text = json.dumps(data or {})
    response.content = json.dumps(data or {}).encode()
    
    if error:
        response.raise_for_status = Mock(side_effect=error)
    else:
        response.raise_for_status = Mock()
    
    return response


def assert_async_result(result, expected):
    """التحقق من نتيجة غير متزامنة"""
    assert result == expected


def async_test(func):
    """زخرفة لاختبار غير متزامن"""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


# ============================================================
# تصدير Fixtures للاستخدام في الاختبارات الأخرى
# ============================================================

__all__ = [
    # مجلدات مؤقتة
    'temp_dir',
    'temp_log_dir',
    'temp_checkpoint_dir',
    'sample_json_file',
    
    # بيانات
    'sample_project_data',
    'sample_checkpoint_data',
    'sample_user_inputs',
    'sample_widgets',
    'sample_colors',
    
    # Mocks
    'mock_browser',
    'mock_llm',
    'mock_controller',
    'mock_checkpoint_manager',
    'mock_context',
    'mock_registry',
    'mock_conversation_logger',
    'mock_agent',
    'mock_agent_with_browser',
    'mock_api_client',
    
    # اختبارات متكاملة
    'integration_test_data',
    
    # دوال مساعدة
    'create_mock_response',
    'assert_async_result',
    'async_test'
]