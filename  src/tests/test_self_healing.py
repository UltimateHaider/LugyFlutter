"""
LugyFlutter - اختبارات وحدة الشفاء الذاتي (Self-Healing)
اختبارات للتحقق من صحة عمل نظام الشفاء الذاتي للعناصر
"""

import pytest
import asyncio
import json
import base64
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.browser.self_healing import SelfHealingSelector
from src.browser.vision_fallback import VisionFallback
from src.browser.selectors import SelectorManager
from src.browser.browser_manager import BrowserManager
from src.core.exceptions import SelfHealingError, ElementNotFoundError


# ============================================================
# بيانات الاختبار (Fixtures)
# ============================================================

@pytest.fixture
def mock_browser_manager():
    """إنشاء مدير متصفح وهمي"""
    browser = AsyncMock()
    browser.take_screenshot = AsyncMock(return_value=b"screenshot_data")
    browser.execute_js = AsyncMock(return_value={
        'x': 100,
        'y': 200,
        'width': 50,
        'height': 30,
        'text': 'Test Element',
        'selector': '#test-element',
        'tagName': 'div',
        'className': 'test-class',
        'id': 'test-element',
        'visible': True,
        'attributes': {'data-test': 'value'}
    })
    browser.find_element = AsyncMock(return_value={
        'x': 100,
        'y': 200,
        'width': 50,
        'height': 30,
        'text': 'Test Element',
        'selector': '#test-element'
    })
    
    manager = Mock()
    manager.browser = browser
    manager.execute_js = browser.execute_js
    manager.take_screenshot = browser.take_screenshot
    manager.find_element = browser.find_element
    return manager


@pytest.fixture
def self_healing(mock_browser_manager):
    """إنشاء نظام شفاء ذاتي للاختبار"""
    return SelfHealingSelector(mock_browser_manager)


@pytest.fixture
def vision_fallback(mock_browser_manager):
    """إنشاء نظام رؤية حاسوبية للاختبار"""
    return VisionFallback(mock_browser_manager)


@pytest.fixture
def selector_manager():
    """إنشاء مدير محددات للاختبار"""
    return SelectorManager()


@pytest.fixture
def sample_element_info():
    """معلومات عنصر عينة للاختبار"""
    return {
        'id': 'test-element',
        'tagName': 'div',
        'className': 'test-class another-class',
        'text': 'Test Element Content',
        'attributes': {
            'data-test': 'value',
            'role': 'button',
            'aria-label': 'Test Button'
        },
        'x': 100,
        'y': 200,
        'width': 50,
        'height': 30,
        'visible': True
    }


# ============================================================
# اختبارات SelfHealingSelector
# ============================================================

class TestSelfHealingSelector:
    """اختبارات نظام الشفاء الذاتي"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, self_healing):
        """اختبار تهيئة النظام"""
        assert self_healing is not None
        assert self_healing.browser is not None
        assert self_healing.selector_history == []
        assert self_healing.healing_cache == {}
        assert self_healing.stats["total_attempts"] == 0
    
    @pytest.mark.asyncio
    async def test_find_element_dom_success(self, self_healing):
        """اختبار العثور على عنصر باستخدام DOM"""
        selectors = ["#test-element", ".test-class", "div[data-test='value']"]
        
        element = await self_healing.find_element(selectors)
        
        assert element is not None
        assert element.get('x') == 100
        assert element.get('y') == 200
        assert self_healing.stats["dom_success"] == 1
        assert self_healing.stats["total_attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_find_element_text_success(self, self_healing):
        """اختبار العثور على عنصر باستخدام النص"""
        # محاكاة فشل DOM
        self_healing.browser.execute_js = AsyncMock(return_value=None)
        
        # محاكاة نجاح البحث بالنص
        self_healing.browser.execute_js = AsyncMock(side_effect=[
            None,  # DOM fail
            {  # Text success
                'x': 100,
                'y': 200,
                'width': 50,
                'height': 30,
                'text': 'Click Here',
                'selector': 'text:Click Here'
            }
        ])
        
        element = await self_healing.find_element(
            selectors=["#non-existent"],
            target_description="Click Here"
        )
        
        assert element is not None
        assert element.get('text') == 'Click Here'
        assert self_healing.stats["text_success"] == 1
        assert self_healing.stats["total_attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_find_element_cache_hit(self, self_healing):
        """اختبار العثور على عنصر من التخزين المؤقت"""
        selectors = ["#test-element"]
        
        # أول محاولة
        element1 = await self_healing.find_element(selectors)
        assert element1 is not None
        
        # محاولة ثانية (يجب أن تأتي من الكاش)
        element2 = await self_healing.find_element(selectors)
        assert element2 is not None
        assert len(self_healing.healing_cache) > 0
    
    @pytest.mark.asyncio
    async def test_find_element_not_found(self, self_healing):
        """اختبار فشل العثور على عنصر"""
        self_healing.browser.execute_js = AsyncMock(return_value=None)
        
        with patch('src.browser.self_healing.SelfHealingSelector._find_by_vision', return_value=None):
            element = await self_healing.find_element(
                selectors=["#non-existent"],
                target_description="Non existent"
            )
            
            assert element is None
            assert self_healing.stats["failed_healings"] == 1
    
    @pytest.mark.asyncio
    async def test_find_element_with_successful_selectors(self, self_healing):
        """اختبار العثور على عنصر باستخدام محددات ناجحة سابقة"""
        # تسجيل محدد ناجح
        self_healing.successful_selectors["#old-selector"] = "#new-selector"
        
        # محاكاة نجاح المحدد الجديد
        self_healing.browser.execute_js = AsyncMock(return_value={
            'x': 100,
            'y': 200,
            'width': 50,
            'height': 30,
            'text': 'Found Element',
            'selector': '#new-selector'
        })
        
        element = await self_healing.find_element(
            selectors=["#old-selector"]
        )
        
        assert element is not None
        assert self_healing.stats["healing_events"] == 1
    
    def test_is_element_valid(self, self_healing):
        """اختبار التحقق من صحة العنصر"""
        # عنصر صحيح
        valid_element = {
            'x': 100,
            'y': 200,
            'width': 50,
            'height': 30,
            'visible': True
        }
        assert self_healing._is_element_valid(valid_element) is True
        
        # عنصر غير مرئي
        invisible_element = {
            'x': 100,
            'y': 200,
            'width': 0,
            'height': 0,
            'visible': False
        }
        assert self_healing._is_element_valid(invisible_element) is False
        
        # عنصر فارغ
        assert self_healing._is_element_valid(None) is False
    
    def test_get_cache_key(self, self_healing):
        """اختبار إنشاء مفتاح التخزين المؤقت"""
        selectors = ["#test", ".class"]
        description = "Test Button"
        
        key = self_healing._get_cache_key(selectors, description)
        
        assert key is not None
        assert len(key) == 32  # MD5 hash length
    
    def test_update_cache(self, self_healing):
        """اختبار تحديث التخزين المؤقت"""
        key = "test_key"
        element = {'x': 100, 'y': 200}
        
        self_healing._update_cache(key, element)
        assert key in self_healing.healing_cache
        assert self_healing.healing_cache[key] == element
    
    def test_update_cache_limit(self, self_healing):
        """اختبار حد التخزين المؤقت"""
        # إضافة أكثر من 100 عنصر
        for i in range(150):
            key = f"key_{i}"
            element = {'x': i, 'y': i}
            self_healing._update_cache(key, element)
        
        # يجب أن يكون الحجم أقل من أو يساوي 100
        assert len(self_healing.healing_cache) <= 100
    
    def test_record_success(self, self_healing):
        """اختبار تسجيل محدد ناجح"""
        element = {'selector': '#test', 'x': 100, 'y': 200}
        
        self_healing._record_success("#test", "dom", element)
        
        assert len(self_healing.selector_history) == 1
        assert self_healing.learning_stats["dom"] == 1
        assert "#test" in self_healing.successful_selectors
    
    def test_record_success_history_limit(self, self_healing):
        """اختبار حد تاريخ المحددات"""
        # إضافة أكثر من 100 مدخل
        for i in range(150):
            element = {'selector': f'#test_{i}', 'x': i, 'y': i}
            self_healing._record_success(f"#test_{i}", "dom", element)
        
        assert len(self_healing.selector_history) <= 100
    
    def test_generate_alternative_selectors(self, self_healing, sample_element_info):
        """اختبار توليد محددات بديلة"""
        selectors = self_healing.generate_alternative_selectors(sample_element_info)
        
        assert len(selectors) > 0
        assert "#test-element" in selectors
        assert "div.test-class" in selectors
        assert "[data-test='value']" in selectors
    
    def test_get_healing_stats(self, self_healing):
        """اختبار الحصول على إحصائيات الشفاء"""
        self_healing.stats["dom_success"] = 10
        self_healing.stats["text_success"] = 5
        self_healing.stats["vision_success"] = 3
        self_healing.stats["total_attempts"] = 18
        
        stats = self_healing.get_healing_stats()
        
        assert stats["dom_success"] == 10
        assert stats["text_success"] == 5
        assert stats["vision_success"] == 3
        assert stats["success_rate"] == "100.0%"
    
    def test_clear_cache(self, self_healing):
        """اختبار مسح التخزين المؤقت"""
        self_healing.healing_cache["test"] = {'x': 100}
        assert len(self_healing.healing_cache) > 0
        
        self_healing.clear_cache()
        assert len(self_healing.healing_cache) == 0
    
    def test_reset_stats(self, self_healing):
        """اختبار إعادة تعيين الإحصائيات"""
        self_healing.stats["dom_success"] = 10
        self_healing.stats["total_attempts"] = 15
        self_healing.learning_stats["dom"] = 10
        
        self_healing.reset_stats()
        
        assert self_healing.stats["dom_success"] == 0
        assert self_healing.stats["total_attempts"] == 0
        assert len(self_healing.learning_stats) == 0


# ============================================================
# اختبارات VisionFallback
# ============================================================

class TestVisionFallback:
    """اختبارات نظام الرؤية الحاسوبية"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, vision_fallback):
        """اختبار تهيئة النظام"""
        assert vision_fallback is not None
        assert vision_fallback.browser is not None
        assert vision_fallback.last_screenshot is None
        assert vision_fallback.previous_screenshots == []
        assert vision_fallback.stats["total_detections"] == 0
    
    @pytest.mark.asyncio
    async def test_detect_text(self, vision_fallback):
        """اختبار الكشف عن النص"""
        # محاكاة لقطة شاشة مع نص
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.threshold') as mock_threshold:
                    with patch('pytesseract.image_to_data') as mock_ocr:
                        # محاكاة OCR
                        mock_ocr.return_value = {
                            'text': ['', 'Click', 'Here', ''],
                            'left': [0, 10, 20, 30],
                            'top': [0, 5, 15, 25],
                            'width': [0, 50, 40, 30],
                            'height': [0, 20, 15, 10],
                            'conf': [0, 90, 85, 75]
                        }
                        
                        result = await vision_fallback.detect_text("Click")
                        
                        assert result is not None
                        assert result['text'] == 'Click'
                        assert result['method'] == 'ocr'
                        assert vision_fallback.stats["ocr_success"] == 1
    
    @pytest.mark.asyncio
    async def test_detect_text_not_found(self, vision_fallback):
        """اختبار عدم العثور على النص"""
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.threshold') as mock_threshold:
                    with patch('pytesseract.image_to_data') as mock_ocr:
                        mock_ocr.return_value = {
                            'text': ['', 'Other', 'Text', ''],
                            'left': [0, 10, 20, 30],
                            'top': [0, 5, 15, 25],
                            'width': [0, 50, 40, 30],
                            'height': [0, 20, 15, 10],
                            'conf': [0, 90, 85, 75]
                        }
                        
                        result = await vision_fallback.detect_text("NotFound")
                        
                        assert result is None
                        assert vision_fallback.stats["ocr_success"] == 0
    
    @pytest.mark.asyncio
    async def test_detect_text_with_region(self, vision_fallback):
        """اختبار الكشف عن النص في منطقة محددة"""
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.threshold') as mock_threshold:
                    with patch('pytesseract.image_to_data') as mock_ocr:
                        mock_ocr.return_value = {
                            'text': ['', 'Button', ''],
                            'left': [0, 5, 10],
                            'top': [0, 3, 8],
                            'width': [0, 40, 30],
                            'height': [0, 15, 10],
                            'conf': [0, 95, 80]
                        }
                        
                        result = await vision_fallback.detect_text(
                            "Button",
                            region=(10, 20, 200, 100)
                        )
                        
                        assert result is not None
                        assert result['x'] >= 10  # يجب أن تكون الإحداثيات معدلة
    
    @pytest.mark.asyncio
    async def test_detect_button(self, vision_fallback):
        """اختبار الكشف عن زر"""
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.Canny') as mock_canny:
                    with patch('cv2.findContours') as mock_contours:
                        # محاكاة اكتشاف زر
                        mock_contour = Mock()
                        mock_contour.__iter__ = Mock(return_value=iter([
                            [(0, 0), (50, 0), (50, 30), (0, 30)]
                        ]))
                        mock_contours.return_value = (None, mock_contour)
                        
                        with patch('cv2.boundingRect', return_value=(10, 20, 60, 30)):
                            result = await vision_fallback.detect_button()
                            
                            assert result is not None
                            assert result['width'] == 60
                            assert result['height'] == 30
                            assert result['method'] == 'contour'
                            assert vision_fallback.stats["contour_detections"] == 1
    
    @pytest.mark.asyncio
    async def test_detect_button_with_region(self, vision_fallback):
        """اختبار الكشف عن زر في منطقة محددة"""
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.Canny') as mock_canny:
                    with patch('cv2.findContours') as mock_contours:
                        mock_contour = Mock()
                        mock_contour.__iter__ = Mock(return_value=iter([
                            [(0, 0), (50, 0), (50, 30), (0, 30)]
                        ]))
                        mock_contours.return_value = (None, mock_contour)
                        
                        with patch('cv2.boundingRect', return_value=(5, 10, 60, 30)):
                            result = await vision_fallback.detect_button(
                                region=(20, 30, 200, 150)
                            )
                            
                            assert result is not None
                            assert result['x'] >= 20  # إزاحة المنطقة
    
    @pytest.mark.asyncio
    async def test_compare_screenshots(self, vision_fallback):
        """اختبار مقارنة لقطات الشاشة"""
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.absdiff') as mock_absdiff:
                    with patch('cv2.cvtColor') as mock_cvt2:
                        with patch('numpy.sum') as mock_sum:
                            mock_sum.return_value = 1000
                            
                            # أول لقطة
                            result1 = await vision_fallback.compare_screenshots()
                            assert result1['has_changes'] is False
                            
                            # لقطة ثانية
                            result2 = await vision_fallback.compare_screenshots()
                            assert result2['has_changes'] is True
                            assert vision_fallback.stats["comparisons"] == 2
    
    @pytest.mark.asyncio
    async def test_compare_screenshots_save_diff(self, vision_fallback):
        """اختبار مقارنة لقطات الشاشة مع حفظ الفرق"""
        with patch('PIL.Image.open') as mock_image:
            with patch('cv2.cvtColor') as mock_cvt:
                with patch('cv2.absdiff') as mock_absdiff:
                    with patch('cv2.cvtColor') as mock_cvt2:
                        with patch('numpy.sum') as mock_sum:
                            mock_sum.return_value = 10000
                            
                            with patch('cv2.imwrite') as mock_write:
                                result = await vision_fallback.compare_screenshots(
                                    save_diff=True
                                )
                                
                                assert result['has_changes'] is True
                                assert result['diff_image_path'] is not None
    
    @pytest.mark.asyncio
    async def test_find_template(self, vision_fallback):
        """اختبار البحث عن قالب"""
        with patch('cv2.imread') as mock_read:
            with patch('PIL.Image.open') as mock_image:
                with patch('cv2.matchTemplate') as mock_match:
                    mock_match.return_value = (None, 0.95, None, (10, 20))
                    mock_read.return_value = Mock(shape=(30, 50, 3))
                    
                    result = await vision_fallback.find_template(
                        "template.png",
                        threshold=0.8
                    )
                    
                    assert result is not None
                    assert result['confidence'] >= 0.8
                    assert result['method'] == 'template_matching'
                    assert vision_fallback.stats["template_matches"] == 1
    
    @pytest.mark.asyncio
    async def test_find_template_not_found(self, vision_fallback):
        """اختبار عدم العثور على القالب"""
        with patch('cv2.imread', return_value=None):
            result = await vision_fallback.find_template("non_existent.png")
            
            assert result is None
    
    def test_hex_to_rgb(self, vision_fallback):
        """اختبار تحويل HEX إلى RGB"""
        # HEX 6 أحرف
        rgb = vision_fallback._hex_to_rgb("#FF6B6B")
        assert rgb == (255, 107, 107)
        
        # HEX 3 أحرف
        rgb = vision_fallback._hex_to_rgb("#F00")
        assert rgb == (255, 0, 0)
        
        # HEX غير صالح
        rgb = vision_fallback._hex_to_rgb("invalid")
        assert rgb is None
    
    def test_color_name_to_rgb(self, vision_fallback):
        """اختبار تحويل اسم اللون إلى RGB"""
        rgb = vision_fallback._color_name_to_rgb("red")
        assert rgb == (255, 0, 0)
        
        rgb = vision_fallback._color_name_to_rgb("أحمر")
        assert rgb == (255, 0, 0)
        
        rgb = vision_fallback._color_name_to_rgb("unknown")
        assert rgb is None
    
    def test_color_distance(self, vision_fallback):
        """اختبار حساب المسافة بين لونين"""
        color1 = (255, 0, 0)
        color2 = (0, 255, 0)
        
        distance = vision_fallback._color_distance(color1, color2)
        assert distance > 0
        
        # نفس اللون
        distance = vision_fallback._color_distance(color1, color1)
        assert distance == 0
    
    def test_get_stats(self, vision_fallback):
        """اختبار الحصول على الإحصائيات"""
        vision_fallback.stats["ocr_success"] = 5
        vision_fallback.stats["total_detections"] = 10
        
        stats = vision_fallback.get_stats()
        
        assert stats["ocr_success"] == 5
        assert stats["total_detections"] == 10
        assert "tesseract_available" in stats
    
    def test_reset_stats(self, vision_fallback):
        """اختبار إعادة تعيين الإحصائيات"""
        vision_fallback.stats["ocr_success"] = 5
        vision_fallback.stats["total_detections"] = 10
        
        vision_fallback.reset_stats()
        
        assert vision_fallback.stats["ocr_success"] == 0
        assert vision_fallback.stats["total_detections"] == 0


# ============================================================
# اختبارات SelectorManager
# ============================================================

class TestSelectorManager:
    """اختبارات مدير المحددات"""
    
    def test_initialization(self, selector_manager):
        """اختبار تهيئة المدير"""
        assert selector_manager is not None
        assert selector_manager.selector_cache == {}
        assert selector_manager.selector_performance == {}
        assert selector_manager.selector_blacklist == set()
    
    def test_generate_css_selectors(self, selector_manager, sample_element_info):
        """اختبار توليد محددات CSS"""
        selectors = selector_manager.generate_css_selectors(sample_element_info)
        
        assert len(selectors) > 0
        assert "#test-element" in selectors
        assert ".test-class" in selectors
        assert "div.test-class" in selectors
        assert "[data-test='value']" in selectors
    
    def test_generate_css_selectors_empty(self, selector_manager):
        """اختبار توليد محددات CSS من معلومات فارغة"""
        selectors = selector_manager.generate_css_selectors({})
        assert selectors == []
    
    def test_generate_xpath_selectors(self, selector_manager, sample_element_info):
        """اختبار توليد محددات XPath"""
        selectors = selector_manager.generate_xpath_selectors(sample_element_info)
        
        assert len(selectors) > 0
        assert "//*[@id='test-element']" in selectors
        assert "//div[contains(text(),'Test Element Content')]" in selectors
    
    def test_generate_all_selectors(self, selector_manager, sample_element_info):
        """اختبار توليد جميع المحددات"""
        selectors = selector_manager.generate_all_selectors(sample_element_info)
        
        assert len(selectors) > 0
        # يجب أن تحتوي على محددات CSS و XPath
        assert any(s.startswith('#') or s.startswith('.') for s in selectors)
        assert any(s.startswith('//') for s in selectors)
    
    def test_get_optimal_selectors(self, selector_manager, sample_element_info):
        """اختبار الحصول على المحددات المثلى"""
        selectors = selector_manager.get_optimal_selectors(sample_element_info)
        
        assert len(selectors) > 0
        assert len(selectors) <= 5  # الحد الأقصى 5 محددات
    
    def test_record_selector_performance_success(self, selector_manager):
        """اختبار تسجيل أداء محدد ناجح"""
        selector_manager.record_selector_performance("#test", True)
        assert selector_manager.selector_performance["#test"] == 1
    
    def test_record_selector_performance_failure(self, selector_manager):
        """اختبار تسجيل أداء محدد فاشل"""
        # فشل 4 مرات لدخول القائمة السوداء
        for _ in range(4):
            selector_manager.record_selector_performance("#test", False)
        
        assert selector_manager.selector_performance["#test"] == -4
        assert "#test" in selector_manager.selector_blacklist
    
    def test_get_selector_history(self, selector_manager):
        """اختبار الحصول على تاريخ المحدد"""
        selector_manager.record_selector_performance("#test", True)
        selector_manager.record_selector_performance("#test", True)
        
        history = selector_manager.get_selector_history("#test")
        
        assert history["selector"] == "#test"
        assert history["performance"] == 2
        assert history["is_blacklisted"] is False
        assert history["is_optimal"] is False  # يحتاج 5+ للتفوق
    
    def test_clear_performance_data(self, selector_manager):
        """اختبار مسح بيانات الأداء"""
        selector_manager.record_selector_performance("#test", True)
        selector_manager.record_selector_performance("#test2", False)
        
        assert len(selector_manager.selector_performance) > 0
        
        selector_manager.clear_performance_data()
        
        assert len(selector_manager.selector_performance) == 0
        assert len(selector_manager.selector_blacklist) == 0
    
    def test_get_stats(self, selector_manager):
        """اختبار الحصول على الإحصائيات"""
        for i in range(10):
            selector_manager.record_selector_performance(f"#test_{i}", True)
        
        stats = selector_manager.get_stats()
        
        assert stats["total_selectors_tracked"] == 10
        assert stats["blacklisted_selectors"] == 0
        assert stats["avg_performance"] == 1.0


# ============================================================
# اختبارات الأخطاء
# ============================================================

class TestSelfHealingErrors:
    """اختبارات معالجة الأخطاء في نظام الشفاء الذاتي"""
    
    @pytest.mark.asyncio
    async def test_browser_error_handling(self, self_healing):
        """اختبار معالجة أخطاء المتصفح"""
        self_healing.browser.execute_js = AsyncMock(side_effect=Exception("Browser error"))
        
        element = await self_healing.find_element(["#test"])
        
        assert element is None
        assert self_healing.stats["failed_healings"] == 1
    
    @pytest.mark.asyncio
    async def test_vision_error_handling(self, vision_fallback):
        """اختبار معالجة أخطاء الرؤية الحاسوبية"""
        with patch('PIL.Image.open', side_effect=Exception("Image error")):
            result = await vision_fallback.detect_text("test")
            assert result is None
    
    def test_selector_generation_error(self, selector_manager):
        """اختبار أخطاء توليد المحددات"""
        # معلومات عنصر غير صالحة
        selectors = selector_manager.generate_css_selectors(None)
        assert selectors == []
        
        selectors = selector_manager.generate_xpath_selectors(None)
        assert selectors == []


# ============================================================
# تشغيل الاختبارات
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])