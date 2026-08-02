"""
LugyFlutter - اختبارات وحدة استخراج المعلومات (Information Extractor)
اختبارات للتحقق من صحة عمل نظام استخراج المعلومات
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.extraction.extractor import InformationExtractor
from src.extraction.regex_patterns import RegexPatterns
from src.extraction.llm_fallback import LLMFallback
from src.core.exceptions import ExtractionError, LLMExtractionError


# ============================================================
# بيانات الاختبار (Fixtures)
# ============================================================

@pytest.fixture
def extractor():
    """إنشاء مستخرج معلومات للاختبار"""
    return InformationExtractor()


@pytest.fixture
def extractor_with_llm():
    """إنشاء مستخرج معلومات مع LLM وهمي"""
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="مشروع الاختبار"))
    return InformationExtractor(llm_model=mock_llm)


@pytest.fixture
def sample_texts():
    """نصوص عينة للاختبار"""
    return {
        "arabic_project": "أنشئ مشروع جديد اسمه تطبيقي",
        "english_project": "Create a new project called MyApp",
        "mixed_project": "أريد مشروع اسمه 'تطبيق التسوق'",
        "figma_url": "انسخ من https://figma.com/design/abc123",
        "lovable_url": "الرجاء نسخ من lovable.com/project/xyz",
        "widgets": "أضف Column و Text و Button في الصفحة الرئيسية",
        "widgets_synonyms": "ضع عمود به نص وزر",
        "modifications": "أضف زر في الصفحة الرئيسية واحذف النص القديم",
        "colors": "استخدم لون #FF6B6B وخلفية زرقاء",
        "empty": "",
        "complex": """
            مرحباً، أريد إنشاء مشروع جديد اسمه "تطبيق المطعم".
            أضف Column و Row و Text في الصفحة الرئيسية.
            استخدم ألوان #6200EE و #03DAC6.
            الرجاء نسخ التصميم من https://figma.com/design/restaurant
        """
    }


# ============================================================
# اختبارات InformationExtractor
# ============================================================

class TestInformationExtractor:
    """اختبارات مستخرج المعلومات"""
    
    def test_initialization(self, extractor):
        """اختبار تهيئة المستخرج"""
        assert extractor is not None
        assert extractor._cache == {}
        assert extractor._context_memory == []
        assert extractor.stats["total_extractions"] == 0
    
    def test_extract_project_name_arabic(self, extractor, sample_texts):
        """اختبار استخراج اسم المشروع بالعربية"""
        result = extractor.extract_project_name(sample_texts["arabic_project"])
        assert result == "تطبيقي"
    
    def test_extract_project_name_english(self, extractor, sample_texts):
        """اختبار استخراج اسم المشروع بالإنجليزية"""
        result = extractor.extract_project_name(sample_texts["english_project"])
        assert result == "MyApp"
    
    def test_extract_project_name_with_quotes(self, extractor, sample_texts):
        """اختبار استخراج اسم المشروع بين علامات اقتباس"""
        result = extractor.extract_project_name(sample_texts["mixed_project"])
        assert result == "تطبيق التسوق"
    
    def test_extract_project_name_empty(self, extractor, sample_texts):
        """اختبار استخراج اسم المشروع من نص فارغ"""
        result = extractor.extract_project_name(sample_texts["empty"])
        assert result is None
    
    def test_extract_project_name_complex(self, extractor, sample_texts):
        """اختبار استخراج اسم المشروع من نص معقد"""
        result = extractor.extract_project_name(sample_texts["complex"])
        assert result == "تطبيق المطعم"
    
    def test_extract_url_figma(self, extractor, sample_texts):
        """اختبار استخراج رابط Figma"""
        result = extractor.extract_url(sample_texts["figma_url"], "figma")
        assert "figma.com" in result
        assert "abc123" in result
    
    def test_extract_url_lovable(self, extractor, sample_texts):
        """اختبار استخراج رابط Lovable"""
        result = extractor.extract_url(sample_texts["lovable_url"], "lovable")
        assert "lovable.com" in result
    
    def test_extract_url_generic(self, extractor, sample_texts):
        """اختبار استخراج رابط عام"""
        text = "تفضل بزيارة https://example.com/page"
        result = extractor.extract_url(text, "generic")
        assert "example.com" in result
    
    def test_extract_url_empty(self, extractor):
        """اختبار استخراج رابط من نص فارغ"""
        result = extractor.extract_url("", "generic")
        assert result is None
    
    def test_extract_widgets(self, extractor, sample_texts):
        """اختبار استخراج الـ Widgets"""
        result = extractor.extract_widgets(sample_texts["widgets"])
        assert "Column" in result
        assert "Text" in result
        assert "Button" in result
    
    def test_extract_widgets_with_synonyms(self, extractor, sample_texts):
        """اختبار استخراج الـ Widgets باستخدام المرادفات"""
        result = extractor.extract_widgets(sample_texts["widgets_synonyms"])
        assert "Column" in result
        assert "Text" in result
        assert "Button" in result
    
    def test_extract_widgets_empty(self, extractor):
        """اختبار استخراج الـ Widgets من نص فارغ"""
        result = extractor.extract_widgets("")
        assert result == []
    
    def test_extract_widgets_no_match(self, extractor):
        """اختبار استخراج الـ Widgets من نص لا يحتوي عليها"""
        result = extractor.extract_widgets("مرحباً كيف حالك")
        assert result == []
    
    def test_extract_modifications(self, extractor, sample_texts):
        """اختبار استخراج التعديلات"""
        result = extractor.extract_modifications(sample_texts["modifications"])
        assert len(result) > 0
    
    def test_extract_modifications_empty(self, extractor):
        """اختبار استخراج التعديلات من نص فارغ"""
        result = extractor.extract_modifications("")
        assert result == []
    
    def test_extract_colors(self, extractor, sample_texts):
        """اختبار استخراج الألوان"""
        result = extractor.extract_colors(sample_texts["colors"])
        assert len(result) > 0
        assert "#FF6B6B" in result or "FF6B6B" in result
    
    def test_extract_colors_empty(self, extractor):
        """اختبار استخراج الألوان من نص فارغ"""
        result = extractor.extract_colors("")
        assert result == []
    
    def test_extract_all(self, extractor, sample_texts):
        """اختبار استخراج جميع المعلومات دفعة واحدة"""
        result = extractor.extract_all(sample_texts["complex"])
        
        assert result["project_name"] is not None
        assert result["has_project_name"] is True
        assert result["has_url"] is True
        assert result["has_widgets"] is True
        assert result["has_colors"] is True
        assert len(result["widgets"]) > 0
        assert len(result["colors"]) > 0
    
    def test_cache_functionality(self, extractor, sample_texts):
        """اختبار عمل التخزين المؤقت"""
        # أول استخراج
        result1 = extractor.extract_project_name(sample_texts["arabic_project"])
        assert result1 == "تطبيقي"
        assert extractor.stats["cache_hits"] == 0
        
        # استخراج متكرر (يجب أن يأتي من الكاش)
        result2 = extractor.extract_project_name(sample_texts["arabic_project"])
        assert result2 == "تطبيقي"
        assert extractor.stats["cache_hits"] == 1
    
    def test_context_memory(self, extractor, sample_texts):
        """اختبار الذاكرة السياقية"""
        # استخراج معلومات
        extractor.extract_project_name(sample_texts["arabic_project"])
        extractor.extract_widgets(sample_texts["widgets"])
        
        memory = extractor.get_context_memory()
        assert len(memory) == 2
        assert memory[0]["key"] == "project_name"
        assert memory[1]["key"] == "widgets"
    
    def test_clear_cache(self, extractor, sample_texts):
        """اختبار مسح التخزين المؤقت"""
        extractor.extract_project_name(sample_texts["arabic_project"])
        assert len(extractor._cache) > 0
        
        extractor.clear_cache()
        assert len(extractor._cache) == 0
    
    def test_clear_memory(self, extractor, sample_texts):
        """اختبار مسح الذاكرة السياقية"""
        extractor.extract_project_name(sample_texts["arabic_project"])
        assert len(extractor._context_memory) > 0
        
        extractor.clear_memory()
        assert len(extractor._context_memory) == 0
    
    def test_get_stats(self, extractor, sample_texts):
        """اختبار الحصول على الإحصائيات"""
        extractor.extract_project_name(sample_texts["arabic_project"])
        extractor.extract_widgets(sample_texts["widgets"])
        
        stats = extractor.get_stats()
        assert stats["total_extractions"] == 2
        assert stats["regex_attempts"] == 2
        assert stats["cache_size"] >= 0
        assert "success_rate" in stats


class TestInformationExtractorWithLLM:
    """اختبارات مستخرج المعلومات مع LLM"""
    
    def test_llm_fallback_project_name(self, extractor_with_llm, sample_texts):
        """اختبار استخدام LLM كخيار بديل لاستخراج اسم المشروع"""
        # نص لا يحتوي على اسم مشروع واضح
        text = "أريد تطبيق جديد"
        result = extractor_with_llm.extract_project_name(text)
        # النتيجة يجب أن تأتي من LLM الوهمي
        assert result == "مشروع الاختبار"
    
    def test_llm_attempts_count(self, extractor_with_llm, sample_texts):
        """اختبار حساب محاولات LLM"""
        text = "نص بدون معلومات"
        extractor_with_llm.extract_project_name(text)
        
        stats = extractor_with_llm.get_stats()
        assert stats["llm_attempts"] > 0


# ============================================================
# اختبارات RegexPatterns
# ============================================================

class TestRegexPatterns:
    """اختبارات أنماط Regex"""
    
    def test_email_pattern(self):
        """اختبار نمط البريد الإلكتروني"""
        assert RegexPatterns.EMAIL.search("test@example.com") is not None
        assert RegexPatterns.EMAIL.search("user.name@domain.co") is not None
        assert RegexPatterns.EMAIL.search("invalid-email") is None
    
    def test_phone_pattern(self):
        """اختبار نمط رقم الهاتف"""
        assert RegexPatterns.PHONE.search("+966501234567") is not None
        assert RegexPatterns.PHONE.search("050-123-4567") is not None
        assert RegexPatterns.PHONE.search("12345") is not None
    
    def test_url_pattern(self):
        """اختبار نمط الرابط"""
        assert RegexPatterns.URL.search("https://example.com") is not None
        assert RegexPatterns.URL.search("http://test.org/page") is not None
        assert RegexPatterns.URL.search("invalid-url") is None
    
    def test_hex_color_pattern(self):
        """اختبار نمط لون HEX"""
        assert RegexPatterns.HEX_COLOR.search("#FF6B6B") is not None
        assert RegexPatterns.HEX_COLOR.search("#F00") is not None
        assert RegexPatterns.HEX_COLOR.search("FF6B6B") is None  # بدون #
    
    def test_figma_url_pattern(self):
        """اختبار نمط رابط Figma"""
        assert RegexPatterns.FIGMA_URL.search("https://figma.com/design/abc123") is not None
        assert RegexPatterns.FIGMA_URL.search("figma.com/file/xyz789") is not None
    
    def test_lovable_url_pattern(self):
        """اختبار نمط رابط Lovable"""
        assert RegexPatterns.LOVABLE_URL.search("https://lovable.com/project/xyz") is not None
        assert RegexPatterns.LOVABLE_URL.search("lovable.ai/project/abc") is not None
    
    def test_get_all_patterns(self):
        """اختبار الحصول على جميع الأنماط"""
        patterns = RegexPatterns.get_all_patterns()
        assert "email" in patterns
        assert "url" in patterns
        assert "hex_color" in patterns
        assert "figma_url" in patterns
    
    def test_extract_all(self):
        """اختبار استخراج جميع الأنماط من نص"""
        text = "البريد: test@example.com والرابط: https://example.com"
        result = RegexPatterns.extract_all(text)
        assert "email" in result
        assert "url" in result
    
    def test_has_pattern(self):
        """اختبار التحقق من وجود نمط"""
        text = "test@example.com"
        assert RegexPatterns.has_pattern(text, "email") is True
        assert RegexPatterns.has_pattern(text, "url") is False
    
    def test_get_matching_patterns(self):
        """اختبار الحصول على الأنماط المتطابقة"""
        text = "test@example.com https://example.com"
        patterns = RegexPatterns.get_matching_patterns(text)
        assert "email" in patterns
        assert "url" in patterns


# ============================================================
# اختبارات LLMFallback
# ============================================================

class TestLLMFallback:
    """اختبارات نظام LLM Fallback"""
    
    def test_initialization(self):
        """اختبار تهيئة النظام"""
        mock_llm = Mock()
        fallback = LLMFallback(mock_llm)
        assert fallback is not None
        assert fallback.templates is not None
        assert fallback.stats["attempts"] == 0
    
    def test_extract_project_name(self):
        """اختبار استخراج اسم المشروع باستخدام LLM"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "مشروع اختبار"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        fallback = LLMFallback(mock_llm)
        result = fallback.extract("نص تجريبي", "project_name")
        assert result == "مشروع اختبار"
        assert fallback.stats["attempts"] == 1
        assert fallback.stats["success"] == 1
    
    def test_extract_with_empty_text(self):
        """اختبار الاستخراج من نص فارغ"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "غير محدد"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        fallback = LLMFallback(mock_llm)
        result = fallback.extract("", "project_name")
        assert result is None
        assert fallback.stats["failures"] == 1
    
    def test_extract_with_unknown_field(self):
        """اختبار الاستخراج بحقل غير معروف"""
        mock_llm = Mock()
        fallback = LLMFallback(mock_llm)
        result = fallback.extract("نص", "unknown_field")
        assert result is None
    
    def test_get_stats(self):
        """اختبار الحصول على الإحصائيات"""
        mock_llm = Mock()
        fallback = LLMFallback(mock_llm)
        
        # تنفيذ بعض العمليات
        mock_response = Mock()
        mock_response.content = "ناتج"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        fallback.extract("نص1", "project_name")
        fallback.extract("نص2", "project_name")
        
        stats = fallback.get_stats()
        assert stats["attempts"] == 2
        assert stats["success"] == 2
        assert stats["success_rate"] == "100.0%"


# ============================================================
# اختبارات التكامل (Integration Tests)
# ============================================================

class TestIntegration:
    """اختبارات التكامل بين المكونات"""
    
    def test_full_extraction_flow(self):
        """اختبار تدفق الاستخراج الكامل"""
        extractor = InformationExtractor()
        
        text = """
        مشروع اسمه "تطبيق المطعم"
        أضف Column و Row و Text
        استخدم ألوان #6200EE و #03DAC6
        https://figma.com/design/restaurant
        """
        
        result = extractor.extract_all(text)
        
        assert result["project_name"] == "تطبيق المطعم"
        assert result["has_url"] is True
        assert result["has_widgets"] is True
        assert result["has_colors"] is True
        assert len(result["widgets"]) >= 3
        assert len(result["colors"]) >= 2
    
    def test_extractor_save_memory(self, tmp_path):
        """اختبار حفظ الذاكرة إلى ملف"""
        extractor = InformationExtractor()
        extractor.extract_project_name("مشروع اسمه اختبار")
        
        file_path = tmp_path / "memory.json"
        success = extractor.save_memory_to_file(str(file_path))
        
        assert success is True
        assert file_path.exists()
        
        data = json.loads(file_path.read_text(encoding='utf-8'))
        assert "memory" in data
        assert len(data["memory"]) > 0
    
    def test_extractor_load_memory(self, tmp_path):
        """اختبار تحميل الذاكرة من ملف"""
        extractor = InformationExtractor()
        extractor.extract_project_name("مشروع اسمه اختبار")
        
        file_path = tmp_path / "memory.json"
        extractor.save_memory_to_file(str(file_path))
        
        # إنشاء مستخرج جديد وتحميل الذاكرة
        new_extractor = InformationExtractor()
        success = new_extractor.load_memory_from_file(str(file_path))
        
        assert success is True
        assert len(new_extractor._context_memory) > 0
    
    def test_cache_limits(self):
        """اختبار حدود التخزين المؤقت"""
        extractor = InformationExtractor()
        
        # استخراج العديد من النصوص
        for i in range(50):
            text = f"مشروع اسمه Project{i}"
            extractor.extract_project_name(text)
        
        # التحقق من أن الكاش لا يتجاوز الحد
        assert len(extractor._cache) <= 50  # الحد الافتراضي 100


# ============================================================
# اختبارات الأخطاء (Error Tests)
# ============================================================

class TestErrors:
    """اختبارات معالجة الأخطاء"""
    
    def test_extraction_error(self):
        """اختبار خطأ الاستخراج"""
        extractor = InformationExtractor()
        
        # يجب أن يعالج النصوص الفارغة بدون أخطاء
        result = extractor.extract_project_name("")
        assert result is None
        
        result = extractor.extract_widgets("")
        assert result == []
    
    def test_llm_extraction_error(self):
        """اختبار خطأ LLM"""
        mock_llm = Mock()
        mock_llm.invoke = Mock(side_effect=Exception("LLM Error"))
        
        extractor = InformationExtractor(llm_model=mock_llm)
        
        # يجب أن يتعامل مع خطأ LLM بدون انهيار
        result = extractor.extract_project_name("نص عشوائي")
        assert result is None
    
    def test_invalid_regex_pattern(self):
        """اختبار نمط Regex غير صالح"""
        # هذا الاختبار يجب أن يمر بدون أخطاء
        extractor = InformationExtractor()
        
        # محاولة استخراج بنمط غير موجود
        result = extractor.extract_url("https://example.com", "unknown_platform")
        assert result is not None  # سيستخدم النمط العام


# ============================================================
# تشغيل الاختبارات
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])