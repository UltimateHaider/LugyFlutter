"""
LugyFlutter - اختبارات وحدة الوكيل الرئيسي (Agent)
اختبارات للتحقق من صحة عمل الوكيل الرئيسي LugyFlutter
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.agent import LugyFlutter
from src.core.enums import TaskType, InteractionMode
from src.core.config import config, Config
from src.core.exceptions import (
    AgentError,
    TaskExecutionError,
    TaskClassificationError,
    APIKeyError,
    BrowserError
)
from src.extraction.extractor import InformationExtractor
from src.context.context_manager import ProjectContext
from src.checkpoint.checkpoint_manager import CheckpointManager


# ============================================================
# بيانات الاختبار (Fixtures)
# ============================================================

@pytest.fixture
def mock_config():
    """إنشاء إعدادات وهمية"""
    with patch('src.core.config.config') as mock:
        mock.GOOGLE_API_KEY = "AI_test_api_key_12345"
        mock.BROWSER_HEADLESS = True
        mock.BROWSER_TIMEOUT = 30
        mock.MAX_STEPS = 30
        mock.RETRY_DELAY = 3
        mock.AUTO_HEALING_ENABLED = True
        mock.VISION_FALLBACK_ENABLED = True
        yield mock


@pytest.fixture
def mock_browser():
    """إنشاء متصفح وهمي"""
    browser = AsyncMock()
    browser.take_screenshot = AsyncMock(return_value=b"screenshot_data")
    browser.get_current_url = AsyncMock(return_value="https://app.flutterflow.io")
    browser.get_page_title = AsyncMock(return_value="FlutterFlow Builder")
    browser.navigate_to = AsyncMock(return_value=True)
    browser.execute_js = AsyncMock(return_value={})
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_llm():
    """إنشاء نموذج LLM وهمي"""
    llm = Mock()
    llm.invoke = Mock(return_value=Mock(content="مشروع اختبار"))
    return llm


@pytest.fixture
def agent(mock_config):
    """إنشاء وكيل للاختبار"""
    with patch('src.core.agent.LugyFlutter._test_api_key', return_value=True):
        agent = LugyFlutter(
            mode=InteractionMode.AUTO,
            api_key="AI_test_api_key_12345"
        )
        # تعطيل التهيئة التلقائية للمتصفح في الاختبارات
        agent.browser = None
        agent.is_initialized = False
        return agent


@pytest.fixture
def agent_with_browser(agent, mock_browser):
    """إنشاء وكيل مع متصفح وهمي"""
    agent.browser = mock_browser
    agent.is_initialized = True
    agent.llm = Mock()
    agent.controller = Mock()
    agent.extractor = InformationExtractor()
    agent.context = ProjectContext()
    agent.checkpoints = CheckpointManager()
    return agent


# ============================================================
# اختبارات تهيئة الوكيل
# ============================================================

class TestAgentInitialization:
    """اختبارات تهيئة الوكيل"""
    
    def test_agent_creation(self, mock_config):
        """اختبار إنشاء الوكيل"""
        with patch('src.core.agent.LugyFlutter._test_api_key', return_value=True):
            agent = LugyFlutter(
                mode=InteractionMode.AUTO,
                api_key="AI_test_api_key_12345"
            )
            
            assert agent is not None
            assert agent.mode == InteractionMode.AUTO
            assert agent.api_key == "AI_test_api_key_12345"
            assert agent.log_dir is not None
            assert agent.stats["tasks_executed"] == 0
    
    def test_agent_creation_without_api_key(self, mock_config):
        """اختبار إنشاء الوكيل بدون مفتاح API"""
        with patch('src.core.agent.APIKeyManager.get_api_key', return_value=None):
            with patch('src.core.agent.APIKeyManager.setup_api_key', return_value=None):
                with pytest.raises(ValueError):
                    LugyFlutter(api_key=None)
    
    def test_agent_creation_with_invalid_api_key(self, mock_config):
        """اختبار إنشاء الوكيل بمفتاح API غير صالح"""
        with patch('src.core.agent.LugyFlutter._test_api_key', return_value=False):
            with patch('src.core.agent.APIKeyManager.get_api_key', return_value="invalid_key"):
                with pytest.raises(ValueError):
                    LugyFlutter(api_key="invalid_key")
    
    def test_agent_components_initialization(self, mock_config):
        """اختبار تهيئة مكونات الوكيل"""
        with patch('src.core.agent.LugyFlutter._test_api_key', return_value=True):
            agent = LugyFlutter(
                mode=InteractionMode.AUTO,
                api_key="AI_test_api_key_12345"
            )
            
            assert agent.extractor is not None
            assert agent.context is not None
            assert agent.conversation is not None
            assert agent.registry is not None
            assert agent.checkpoints is not None
            assert agent.stats is not None
    
    def test_api_key_testing(self, mock_config):
        """اختبار اختبار مفتاح API"""
        with patch('src.core.agent.LugyFlutter._test_api_key', return_value=True):
            agent = LugyFlutter(api_key="AI_test_api_key_12345")
            assert agent._test_api_key("AI_valid_key") is True
        
        with patch('src.core.agent.LugyFlutter._test_api_key', return_value=False):
            with patch('src.core.agent.APIKeyManager.get_api_key', return_value=None):
                with patch('src.core.agent.APIKeyManager.setup_api_key', return_value=None):
                    with pytest.raises(ValueError):
                        LugyFlutter(api_key="invalid_key")


# ============================================================
# اختبارات تهيئة المتصفح
# ============================================================

class TestBrowserInitialization:
    """اختبارات تهيئة المتصفح"""
    
    @pytest.mark.asyncio
    async def test_initialize_browser(self, agent):
        """اختبار تهيئة المتصفح"""
        with patch('src.core.agent.Browser') as MockBrowser:
            with patch('src.core.agent.BrowserConfig') as MockConfig:
                with patch('src.core.agent.Controller') as MockController:
                    with patch('src.core.agent.ChatGoogleGenerativeAI') as MockLLM:
                        agent.llm = None
                        agent.controller = None
                        
                        mock_browser_instance = AsyncMock()
                        MockBrowser.return_value = mock_browser_instance
                        
                        result = await agent.initialize_browser()
                        
                        assert result is True
                        assert agent.browser is not None
                        assert agent.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_browser_already_initialized(self, agent_with_browser):
        """اختبار تهيئة متصفح مهيأ مسبقاً"""
        result = await agent_with_browser.initialize_browser()
        assert result is True
        assert agent_with_browser.browser is not None
    
    @pytest.mark.asyncio
    async def test_initialize_browser_error(self, agent):
        """اختبار خطأ في تهيئة المتصفح"""
        with patch('src.core.agent.Browser', side_effect=Exception("Browser error")):
            with pytest.raises(BrowserError):
                await agent.initialize_browser()


# ============================================================
# اختبارات معالجة الطلبات
# ============================================================

class TestRequestProcessing:
    """اختبارات معالجة طلبات المستخدم"""
    
    @pytest.mark.asyncio
    async def test_process_user_request_create(self, agent_with_browser):
        """اختبار معالجة طلب إنشاء مشروع"""
        with patch.object(agent_with_browser, 'check_missing_information', return_value=[]):
            with patch.object(agent_with_browser, 'confirm_execution_plan', return_value=True):
                with patch.object(agent_with_browser, 'execute_task', return_value=True):
                    result = await agent_with_browser.process_user_request(
                        "أنشئ مشروع جديد اسمه تطبيقي"
                    )
                    assert agent_with_browser.stats["tasks_executed"] == 1
    
    @pytest.mark.asyncio
    async def test_process_user_request_unknown(self, agent_with_browser):
        """اختبار معالجة طلب غير معروف"""
        with patch('src.utils.safe_input.SafeInput.get_input', return_value="أنشئ مشروع جديد"):
            result = await agent_with_browser.process_user_request("مرحباً")
            # يجب أن يعود بدون تنفيذ مهمة
            assert agent_with_browser.stats["tasks_executed"] == 0
    
    @pytest.mark.asyncio
    async def test_process_user_request_missing_info(self, agent_with_browser):
        """اختبار معالجة طلب مع معلومات ناقصة"""
        with patch.object(
            agent_with_browser,
            'check_missing_information',
            return_value=[{"question": "ما هو اسم المشروع؟", "field": "project_name"}]
        ):
            with patch.object(
                agent_with_browser,
                'ask_clarifications',
                return_value={"project_name": "تطبيقي"}
            ):
                with patch.object(agent_with_browser, 'confirm_execution_plan', return_value=True):
                    with patch.object(agent_with_browser, 'execute_task', return_value=True):
                        result = await agent_with_browser.process_user_request("أنشئ مشروع جديد")
                        assert agent_with_browser.stats["tasks_executed"] == 1
    
    @pytest.mark.asyncio
    async def test_process_user_request_error(self, agent_with_browser):
        """اختبار معالجة خطأ في الطلب"""
        with patch.object(agent_with_browser, 'check_missing_information', side_effect=Exception("Test error")):
            with patch('src.utils.safe_input.SafeInput.get_choice', return_value="محاولة مرة أخرى"):
                # يجب أن يتعامل مع الخطأ بدون انهيار
                await agent_with_browser.process_user_request("أنشئ مشروع")


# ============================================================
# اختبارات تنفيذ المهام
# ============================================================

class TestTaskExecution:
    """اختبارات تنفيذ المهام"""
    
    @pytest.mark.asyncio
    async def test_execute_task(self, agent_with_browser):
        """اختبار تنفيذ مهمة"""
        with patch('src.core.agent.Agent') as MockAgent:
            mock_agent_instance = AsyncMock()
            mock_agent_instance.run = AsyncMock(return_value="Task completed")
            MockAgent.return_value = mock_agent_instance
            
            with patch.object(agent_with_browser, 'build_dynamic_prompt', return_value="Test prompt"):
                await agent_with_browser.execute_task(
                    "أنشئ مشروع جديد",
                    TaskType.CREATE_NEW
                )
                
                assert agent_with_browser.stats["tasks_executed"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_task_with_error(self, agent_with_browser):
        """اختبار تنفيذ مهمة مع خطأ"""
        with patch('src.core.agent.Agent') as MockAgent:
            mock_agent_instance = AsyncMock()
            mock_agent_instance.run = AsyncMock(side_effect=Exception("Execution error"))
            MockAgent.return_value = mock_agent_instance
            
            with patch('src.utils.safe_input.SafeInput.get_choice', return_value="إلغاء"):
                with patch.object(agent_with_browser, 'build_dynamic_prompt', return_value="Test prompt"):
                    await agent_with_browser.execute_task(
                        "أنشئ مشروع جديد",
                        TaskType.CREATE_NEW
                    )
                    # يجب أن يتعامل مع الخطأ بدون انهيار
    
    @pytest.mark.asyncio
    async def test_execute_task_undo(self, agent_with_browser):
        """اختبار تنفيذ مهمة مع التراجع"""
        # حفظ نقطة تفتيش أولاً
        agent_with_browser.checkpoints.save_checkpoint(1, {}, "نقطة 1")
        
        with patch('src.core.agent.Agent') as MockAgent:
            mock_agent_instance = AsyncMock()
            mock_agent_instance.run = AsyncMock(side_effect=Exception("Execution error"))
            MockAgent.return_value = mock_agent_instance
            
            with patch('src.utils.safe_input.SafeInput.get_choice', return_value="التراجع عن آخر خطوة"):
                with patch.object(agent_with_browser, 'build_dynamic_prompt', return_value="Test prompt"):
                    # يجب أن يعالج التراجع
                    await agent_with_browser.execute_task(
                        "أنشئ مشروع جديد",
                        TaskType.CREATE_NEW
                    )


# ============================================================
# اختبارات بناء البرومبت
# ============================================================

class TestPromptBuilding:
    """اختبارات بناء البرومبت الديناميكي"""
    
    def test_build_prompt_create(self, agent):
        """اختبار بناء برومبت إنشاء مشروع"""
        agent.extractor = InformationExtractor()
        
        prompt = agent.build_dynamic_prompt(
            "أنشئ مشروع جديد اسمه تطبيقي",
            TaskType.CREATE_NEW
        )
        
        assert "إنشاء مشروع جديد" in prompt
        assert "تطبيقي" in prompt
        assert "Blank App" in prompt
    
    def test_build_prompt_edit(self, agent):
        """اختبار بناء برومبت تعديل مشروع"""
        agent.extractor = InformationExtractor()
        agent.context.project_name = "مشروعي"
        
        prompt = agent.build_dynamic_prompt(
            "عدل مشروعي وأضف زر",
            TaskType.EDIT_EXISTING
        )
        
        assert "تعديل مشروع موجود" in prompt
        assert "مشروعي" in prompt
    
    def test_build_prompt_clone_figma(self, agent):
        """اختبار بناء برومبت نسخ من Figma"""
        agent.extractor = InformationExtractor()
        
        prompt = agent.build_dynamic_prompt(
            "انسخ من Figma https://figma.com/design/abc123",
            TaskType.CLONE_FROM_FIGMA
        )
        
        assert "نسخ تصميم من Figma" in prompt
        assert "figma.com" in prompt
    
    def test_build_prompt_with_interaction_mode(self, agent):
        """اختبار بناء برومبت مع وضع تفاعلي"""
        agent.mode = InteractionMode.FULL_INTERACTIVE
        agent.extractor = InformationExtractor()
        
        prompt = agent.build_dynamic_prompt(
            "أنشئ مشروع جديد",
            TaskType.CREATE_NEW
        )
        
        assert "ask_user_confirmation" in prompt
        assert "report_progress" in prompt


# ============================================================
# اختبارات التحقق من المعلومات
# ============================================================

class TestInformationValidation:
    """اختبارات التحقق من المعلومات"""
    
    @pytest.mark.asyncio
    async def test_check_missing_info_create(self, agent):
        """اختبار التحقق من معلومات إنشاء مشروع"""
        agent.extractor = InformationExtractor()
        
        # طلب بدون اسم مشروع
        missing = await agent.check_missing_information(
            "أنشئ مشروع جديد",
            TaskType.CREATE_NEW
        )
        
        assert len(missing) > 0
        assert any("اسم المشروع" in q["question"] for q in missing)
    
    @pytest.mark.asyncio
    async def test_check_missing_info_edit(self, agent):
        """اختبار التحقق من معلومات تعديل مشروع"""
        agent.extractor = InformationExtractor()
        
        # طلب بدون اسم مشروع
        missing = await agent.check_missing_information(
            "عدل المشروع",
            TaskType.EDIT_EXISTING
        )
        
        assert len(missing) > 0
        assert any("اسم المشروع" in q["question"] for q in missing)
    
    @pytest.mark.asyncio
    async def test_check_missing_info_complete(self, agent):
        """اختبار التحقق من طلب مكتمل"""
        agent.extractor = InformationExtractor()
        
        missing = await agent.check_missing_information(
            "أنشئ مشروع جديد اسمه تطبيقي يحتوي على Column و Text",
            TaskType.CREATE_NEW
        )
        
        # يجب أن يكون قائمة فارغة لأن المعلومات مكتملة
        assert len(missing) == 0
    
    @pytest.mark.asyncio
    async def test_ask_clarifications(self, agent):
        """اختبار طرح أسئلة توضيحية"""
        questions = [
            {"question": "ما هو اسم المشروع؟", "field": "project_name"},
            {"question": "ما هي الـ Widgets المطلوبة؟", "field": "widgets"}
        ]
        
        with patch('src.utils.safe_input.SafeInput.get_input', return_value="تطبيقي"):
            answers = await agent.ask_clarifications(questions)
            
            assert "project_name" in answers
            assert answers["project_name"] == "تطبيقي"


# ============================================================
# اختبارات تأكيد الخطة
# ============================================================

class TestPlanConfirmation:
    """اختبارات تأكيد خطة التنفيذ"""
    
    @pytest.mark.asyncio
    async def test_confirm_plan_yes(self, agent):
        """اختبار تأكيد الخطة بنعم"""
        with patch('src.utils.safe_input.SafeInput.get_input', return_value="نعم"):
            result = await agent.confirm_execution_plan(
                TaskType.CREATE_NEW,
                "أنشئ مشروع جديد"
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_confirm_plan_no(self, agent):
        """اختبار تأكيد الخطة بلا"""
        with patch('src.utils.safe_input.SafeInput.get_input', return_value="لا"):
            result = await agent.confirm_execution_plan(
                TaskType.CREATE_NEW,
                "أنشئ مشروع جديد"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_confirm_plan_edit(self, agent):
        """اختبار تأكيد الخطة مع تعديل"""
        with patch('src.utils.safe_input.SafeInput.get_input', side_effect=["تعديل", "تعديل خطة", "نعم"]):
            result = await agent.confirm_execution_plan(
                TaskType.CREATE_NEW,
                "أنشئ مشروع جديد"
            )
            assert result is True


# ============================================================
# اختبارات توليد خطوات الخطة
# ============================================================

class TestPlanGeneration:
    """اختبارات توليد خطوات الخطة"""
    
    def test_generate_plan_create(self, agent):
        """اختبار توليد خطوات إنشاء مشروع"""
        agent.extractor = InformationExtractor()
        
        steps = agent.generate_plan_steps(
            TaskType.CREATE_NEW,
            "أنشئ مشروع جديد اسمه تطبيقي"
        )
        
        assert len(steps) > 0
        assert any("تطبيقي" in step for step in steps)
        assert any("New Project" in step for step in steps)
    
    def test_generate_plan_edit(self, agent):
        """اختبار توليد خطوات تعديل مشروع"""
        agent.extractor = InformationExtractor()
        agent.context.project_name = "مشروعي"
        
        steps = agent.generate_plan_steps(
            TaskType.EDIT_EXISTING,
            "عدل مشروعي"
        )
        
        assert len(steps) > 0
        assert any("مشروعي" in step for step in steps)
    
    def test_generate_plan_clone(self, agent):
        """اختبار توليد خطوات نسخ مشروع"""
        agent.extractor = InformationExtractor()
        
        steps = agent.generate_plan_steps(
            TaskType.CLONE_FROM_FIGMA,
            "انسخ من Figma https://figma.com/design/abc123"
        )
        
        assert len(steps) > 0
        assert any("Figma" in step for step in steps)


# ============================================================
# اختبارات نظام المحادثة
# ============================================================

class TestConversation:
    """اختبارات نظام المحادثة"""
    
    @pytest.mark.asyncio
    async def test_start_conversation_exit(self, agent):
        """اختبار بدء المحادثة والخروج"""
        with patch('src.utils.safe_input.SafeInput.get_input', return_value="/exit"):
            with patch.object(agent, '_save_final_state'):
                await agent.start_conversation()
                # يجب أن ينتهي بدون أخطاء
    
    @pytest.mark.asyncio
    async def test_start_conversation_help(self, agent):
        """اختبار بدء المحادثة وعرض المساعدة"""
        with patch('src.utils.safe_input.SafeInput.get_input', side_effect=["/help", "/exit"]):
            with patch.object(agent, '_show_help'):
                with patch.object(agent, '_save_final_state'):
                    await agent.start_conversation()
    
    @pytest.mark.asyncio
    async def test_start_conversation_status(self, agent):
        """اختبار بدء المحادثة وعرض الحالة"""
        with patch('src.utils.safe_input.SafeInput.get_input', side_effect=["/status", "/exit"]):
            with patch.object(agent, '_show_status'):
                with patch.object(agent, '_save_final_state'):
                    await agent.start_conversation()
    
    @pytest.mark.asyncio
    async def test_start_conversation_undo(self, agent):
        """اختبار بدء المحادثة والتراجع"""
        with patch('src.utils.safe_input.SafeInput.get_input', side_effect=["/undo", "/exit"]):
            with patch.object(agent, '_handle_undo'):
                with patch.object(agent, '_save_final_state'):
                    await agent.start_conversation()
    
    @pytest.mark.asyncio
    async def test_start_conversation_user_input(self, agent):
        """اختبار بدء المحادثة مع إدخال مستخدم"""
        with patch('src.utils.safe_input.SafeInput.get_input', side_effect=["أنشئ مشروع", "/exit"]):
            with patch.object(agent, 'process_user_request', return_value=True):
                with patch.object(agent, '_save_final_state'):
                    await agent.start_conversation()


# ============================================================
# اختبارات حفظ الحالة
# ============================================================

class TestStateSaving:
    """اختبارات حفظ الحالة"""
    
    def test_save_final_state(self, agent, tmp_path):
        """اختبار حفظ الحالة النهائية"""
        agent.log_dir = tmp_path
        agent.stats["tasks_executed"] = 5
        
        with patch('src.utils.helpers.export_logs_to_zip', return_value=None):
            agent._save_final_state()
            
            # التحقق من وجود ملف الإحصائيات
            stats_files = list(tmp_path.glob("lugy_stats_*.json"))
            assert len(stats_files) > 0
    
    def test_show_help(self, agent):
        """اختبار عرض المساعدة"""
        # يجب أن يعمل بدون أخطاء
        agent._show_help()
    
    def test_show_status(self, agent):
        """اختبار عرض الحالة"""
        agent.stats["tasks_executed"] = 10
        agent.stats["successful_tasks"] = 8
        
        # يجب أن يعمل بدون أخطاء
        agent._show_status()
    
    def test_show_checkpoints(self, agent):
        """اختبار عرض نقاط التفتيش"""
        agent.checkpoints.save_checkpoint(1, {}, "نقطة 1")
        agent.checkpoints.save_checkpoint(2, {}, "نقطة 2")
        
        # يجب أن يعمل بدون أخطاء
        agent._show_checkpoints()


# ============================================================
# اختبارات الأدوات المساعدة
# ============================================================

class TestHelperMethods:
    """اختبارات الأدوات المساعدة للوكيل"""
    
    @pytest.mark.asyncio
    async def test_handle_undo(self, agent):
        """اختبار معالجة التراجع"""
        agent.checkpoints.save_checkpoint(1, {}, "نقطة 1")
        agent.checkpoints.save_checkpoint(2, {}, "نقطة 2")
        
        await agent._handle_undo()
        assert agent.checkpoints.current_index == 0
    
    @pytest.mark.asyncio
    async def test_handle_undo_no_checkpoints(self, agent):
        """اختبار معالجة التراجع بدون نقاط تفتيش"""
        # يجب أن يعمل بدون أخطاء
        await agent._handle_undo()
    
    def test_get_chrome_user_data_dir(self, agent):
        """اختبار الحصول على مسار Chrome"""
        path = agent.get_chrome_user_data_dir()
        assert path is not None
        assert len(path) > 0


# ============================================================
# اختبارات الأخطاء
# ============================================================

class TestErrorHandling:
    """اختبارات معالجة الأخطاء"""
    
    @pytest.mark.asyncio
    async def test_process_request_exception(self, agent_with_browser):
        """اختبار معالجة استثناء في معالجة الطلب"""
        with patch.object(agent_with_browser, 'check_missing_information', side_effect=Exception("Test error")):
            with patch('src.utils.safe_input.SafeInput.get_choice', return_value="إلغاء الكل"):
                await agent_with_browser.process_user_request("أنشئ مشروع")
                # يجب أن يتعامل مع الاستثناء
    
    @pytest.mark.asyncio
    async def test_ask_next_action(self, agent):
        """اختبار سؤال المستخدم عن الإجراء التالي"""
        with patch('src.utils.safe_input.SafeInput.get_choice', return_value="متابعة مع طلب آخر"):
            agent._ask_next_action()
            # يجب أن يعمل بدون أخطاء
    
    @pytest.mark.asyncio
    async def test_ask_next_action_undo(self, agent):
        """اختبار سؤال المستخدم عن التراجع"""
        with patch('src.utils.safe_input.SafeInput.get_choice', return_value="التراجع عن آخر تعديل"):
            with patch.object(agent, '_handle_undo'):
                agent._ask_next_action()


# ============================================================
# اختبارات التكامل
# ============================================================

class TestIntegration:
    """اختبارات التكامل بين مكونات الوكيل"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, agent_with_browser):
        """اختبار تدفق العمل الكامل"""
        # تهيئة البيانات
        agent_with_browser.extractor = InformationExtractor()
        
        # محاكاة طلب المستخدم
        with patch.object(agent_with_browser, 'check_missing_information', return_value=[]):
            with patch.object(agent_with_browser, 'confirm_execution_plan', return_value=True):
                with patch('src.core.agent.Agent') as MockAgent:
                    mock_agent_instance = AsyncMock()
                    mock_agent_instance.run = AsyncMock(return_value="Task completed")
                    MockAgent.return_value = mock_agent_instance
                    
                    with patch.object(agent_with_browser, 'build_dynamic_prompt', return_value="Test prompt"):
                        await agent_with_browser.process_user_request(
                            "أنشئ مشروع جديد اسمه تطبيقي يحتوي على Column و Text"
                        )
                        
                        # التحقق من تحديث الإحصائيات
                        assert agent_with_browser.stats["tasks_executed"] == 1
                        
                        # التحقق من تحديث السياق
                        assert agent_with_browser.context.current_step > 0


# ============================================================
# تشغيل الاختبارات
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])