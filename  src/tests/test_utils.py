"""
LugyFlutter - اختبارات وحدة الأدوات المساعدة (Utils)
اختبارات للتحقق من صحة عمل الأدوات المساعدة المختلفة
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# إضافة المسار الرئيسي
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.colors import Colors, print_colored, print_success, print_error, print_warning, print_info, print_debug, print_lugy_logo
from src.utils.safe_input import SafeInput
from src.utils.logger import LoggerManager, get_logger, debug, info, warning, error, critical, exception, set_log_level
from src.utils.validators import Validators, validate_api_key, sanitize_input, is_interactive
from src.utils.helpers import (
    check_required_libraries,
    check_environment,
    export_logs_to_zip,
    ensure_directory,
    get_file_size,
    safe_filename,
    read_json_file,
    write_json_file,
    create_backup,
    get_files_in_directory,
    cleanup_old_files,
    format_duration,
    get_timestamp,
    get_timestamp_filename,
    time_function,
    truncate_text,
    convert_to_slug,
    extract_hashtags,
    extract_mentions,
    hash_string,
    hash_file,
    get_system_info,
    is_admin,
    get_terminal_size,
    open_url,
    is_interactive as helpers_is_interactive,
    print_progress_bar,
    chunk_list,
    flatten_list,
    unique_items,
    merge_dicts,
    retry_on_error,
    get_nested_value,
    set_nested_value,
    generate_id,
    get_ip_address,
    download_file,
    get_logs_summary,
    format_file_size
)


# ============================================================
# اختبارات Colors
# ============================================================

class TestColors:
    """اختبارات نظام الألوان"""
    
    def test_colors_exist(self):
        """اختبار وجود الألوان الأساسية"""
        assert Colors.RED is not None
        assert Colors.GREEN is not None
        assert Colors.BLUE is not None
        assert Colors.YELLOW is not None
        assert Colors.CYAN is not None
        assert Colors.MAGENTA is not None
        assert Colors.WHITE is not None
        assert Colors.BLACK is not None
    
    def test_color_names(self):
        """اختبار أسماء الألوان"""
        assert "red" in Colors.COLOR_NAMES
        assert "green" in Colors.COLOR_NAMES
        assert "blue" in Colors.COLOR_NAMES
        assert "lugy" in Colors.COLOR_NAMES
    
    def test_get_color(self):
        """اختبار الحصول على لون"""
        color = Colors.get_color("red")
        assert color == Colors.RED
        
        color = Colors.get_color("unknown", Colors.WHITE)
        assert color == Colors.WHITE
    
    def test_supports_color(self):
        """اختبار دعم الألوان"""
        # يجب أن تعمل بدون أخطاء
        supports = Colors.supports_color()
        assert isinstance(supports, bool)
    
    def test_print_colored(self, capsys):
        """اختبار الطباعة الملونة"""
        print_colored("Test message", Colors.GREEN)
        captured = capsys.readouterr()
        assert "Test message" in captured.out
    
    def test_print_success(self, capsys):
        """اختبار طباعة رسالة نجاح"""
        print_success("Success message")
        captured = capsys.readouterr()
        assert "Success message" in captured.out
    
    def test_print_error(self, capsys):
        """اختبار طباعة رسالة خطأ"""
        print_error("Error message")
        captured = capsys.readouterr()
        assert "Error message" in captured.out
    
    def test_print_warning(self, capsys):
        """اختبار طباعة رسالة تحذير"""
        print_warning("Warning message")
        captured = capsys.readouterr()
        assert "Warning message" in captured.out
    
    def test_print_info(self, capsys):
        """اختبار طباعة رسالة معلومات"""
        print_info("Info message")
        captured = capsys.readouterr()
        assert "Info message" in captured.out
    
    def test_print_debug(self, capsys):
        """اختبار طباعة رسالة تصحيح"""
        print_debug("Debug message")
        captured = capsys.readouterr()
        assert "Debug message" in captured.out
    
    def test_print_lugy_logo(self, capsys):
        """اختبار طباعة شعار LugyFlutter"""
        print_lugy_logo()
        captured = capsys.readouterr()
        assert "LugyFlutter" in captured.out


# ============================================================
# اختبارات SafeInput
# ============================================================

class TestSafeInput:
    """اختبارات نظام الإدخال الآمن"""
    
    def test_get_input(self, monkeypatch):
        """اختبار الحصول على إدخال"""
        monkeypatch.setattr('builtins.input', lambda _: "test input")
        result = SafeInput.get_input("Enter: ")
        assert result == "test input"
    
    def test_get_input_with_default(self, monkeypatch):
        """اختبار الحصول على إدخال مع قيمة افتراضية"""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = SafeInput.get_input("Enter: ", default="default")
        assert result == "default"
    
    def test_get_input_allow_empty(self, monkeypatch):
        """اختبار الحصول على إدخال فارغ مسموح"""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = SafeInput.get_input("Enter: ", allow_empty=True)
        assert result == ""
    
    def test_get_input_with_validator(self, monkeypatch):
        """اختبار الحصول على إدخال مع مدقق"""
        def validator(value):
            return len(value) > 3
        
        monkeypatch.setattr('builtins.input', lambda _: "test")
        result = SafeInput.get_input("Enter: ", validator=validator)
        assert result == "test"
    
    def test_get_input_invalid_then_valid(self, monkeypatch):
        """اختبار إدخال غير صالح ثم صالح"""
        inputs = ["ab", "valid"]
        monkeypatch.setattr('builtins.input', lambda _: inputs.pop(0))
        
        def validator(value):
            return len(value) > 2
        
        result = SafeInput.get_input("Enter: ", validator=validator, max_attempts=3)
        assert result == "valid"
    
    def test_get_choice(self, monkeypatch):
        """اختبار الحصول على اختيار"""
        monkeypatch.setattr('builtins.input', lambda _: "2")
        result = SafeInput.get_choice("Choose:", ["Option1", "Option2", "Option3"])
        assert result == "Option2"
    
    def test_get_choice_by_text(self, monkeypatch):
        """اختبار الحصول على اختيار بالنص"""
        monkeypatch.setattr('builtins.input', lambda _: "Option2")
        result = SafeInput.get_choice("Choose:", ["Option1", "Option2", "Option3"])
        assert result == "Option2"
    
    def test_get_choice_with_default(self, monkeypatch):
        """اختبار الحصول على اختيار مع قيمة افتراضية"""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = SafeInput.get_choice("Choose:", ["Option1", "Option2"], default="Option1")
        assert result == "Option1"
    
    def test_get_confirmation_yes(self, monkeypatch):
        """اختبار تأكيد بنعم"""
        monkeypatch.setattr('builtins.input', lambda _: "1")
        result = SafeInput.get_confirmation("Confirm?")
        assert result is True
    
    def test_get_confirmation_no(self, monkeypatch):
        """اختبار تأكيد بلا"""
        monkeypatch.setattr('builtins.input', lambda _: "2")
        result = SafeInput.get_confirmation("Confirm?")
        assert result is False
    
    def test_get_number(self, monkeypatch):
        """اختبار الحصول على رقم"""
        monkeypatch.setattr('builtins.input', lambda _: "42")
        result = SafeInput.get_number("Enter number:")
        assert result == 42
    
    def test_get_number_with_validation(self, monkeypatch):
        """اختبار الحصول على رقم مع تحقق"""
        monkeypatch.setattr('builtins.input', lambda _: "10")
        result = SafeInput.get_number("Enter number:", min_val=5, max_val=15)
        assert result == 10
    
    def test_get_int(self, monkeypatch):
        """اختبار الحصول على عدد صحيح"""
        monkeypatch.setattr('builtins.input', lambda _: "42")
        result = SafeInput.get_int("Enter int:")
        assert result == 42
    
    def test_get_float(self, monkeypatch):
        """اختبار الحصول على رقم عشري"""
        monkeypatch.setattr('builtins.input', lambda _: "3.14")
        result = SafeInput.get_float("Enter float:")
        assert result == 3.14
    
    def test_get_email(self, monkeypatch):
        """اختبار الحصول على بريد إلكتروني"""
        monkeypatch.setattr('builtins.input', lambda _: "test@example.com")
        result = SafeInput.get_email()
        assert result == "test@example.com"
    
    def test_get_email_invalid(self, monkeypatch):
        """اختبار الحصول على بريد إلكتروني غير صالح"""
        inputs = ["invalid", "test@example.com"]
        monkeypatch.setattr('builtins.input', lambda _: inputs.pop(0))
        result = SafeInput.get_email()
        assert result == "test@example.com"
    
    def test_get_url(self, monkeypatch):
        """اختبار الحصول على رابط"""
        monkeypatch.setattr('builtins.input', lambda _: "https://example.com")
        result = SafeInput.get_url()
        assert result == "https://example.com"
    
    def test_history(self, monkeypatch):
        """اختبار تاريخ الإدخالات"""
        monkeypatch.setattr('builtins.input', lambda _: "test")
        SafeInput.get_input("Enter:")
        
        history = SafeInput.get_history()
        assert len(history) > 0
        assert "test" in history


# ============================================================
# اختبارات Logger
# ============================================================

class TestLogger:
    """اختبارات نظام التسجيل"""
    
    def test_logger_manager_singleton(self):
        """اختبار نمط Singleton لمدير التسجيل"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        assert manager1 is manager2
    
    def test_get_logger(self):
        """اختبار الحصول على Logger"""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"
    
    def test_debug(self, caplog):
        """اختبار تسجيل رسالة تصحيح"""
        with caplog.at_level("DEBUG"):
            debug("Debug message")
            assert "Debug message" in caplog.text
    
    def test_info(self, caplog):
        """اختبار تسجيل رسالة معلومات"""
        with caplog.at_level("INFO"):
            info("Info message")
            assert "Info message" in caplog.text
    
    def test_warning(self, caplog):
        """اختبار تسجيل رسالة تحذير"""
        with caplog.at_level("WARNING"):
            warning("Warning message")
            assert "Warning message" in caplog.text
    
    def test_error(self, caplog):
        """اختبار تسجيل رسالة خطأ"""
        with caplog.at_level("ERROR"):
            error("Error message")
            assert "Error message" in caplog.text
    
    def test_critical(self, caplog):
        """اختبار تسجيل رسالة حرجة"""
        with caplog.at_level("CRITICAL"):
            critical("Critical message")
            assert "Critical message" in caplog.text
    
    def test_set_log_level(self):
        """اختبار تغيير مستوى التسجيل"""
        set_log_level("DEBUG")
        # التحقق من أن المستوى تغير
        logger = get_logger()
        assert logger.level == 10  # DEBUG


# ============================================================
# اختبارات Validators
# ============================================================

class TestValidators:
    """اختبارات نظام التحقق"""
    
    def test_validate_email(self):
        """اختبار التحقق من البريد الإلكتروني"""
        assert Validators.validate_email("test@example.com") is True
        assert Validators.validate_email("invalid-email") is False
        assert Validators.validate_email("") is False
    
    def test_validate_url(self):
        """اختبار التحقق من الرابط"""
        assert Validators.validate_url("https://example.com") is True
        assert Validators.validate_url("http://example.com") is True
        assert Validators.validate_url("invalid-url") is False
        assert Validators.validate_url("") is False
    
    def test_validate_url_https(self):
        """اختبار التحقق من رابط HTTPS"""
        assert Validators.validate_url("https://example.com", require_https=True) is True
        assert Validators.validate_url("http://example.com", require_https=True) is False
    
    def test_validate_phone(self):
        """اختبار التحقق من رقم الهاتف"""
        assert Validators.validate_phone("+966501234567") is True
        assert Validators.validate_phone("050-123-4567") is True
        assert Validators.validate_phone("") is False
    
    def test_validate_project_name(self):
        """اختبار التحقق من اسم المشروع"""
        assert Validators.validate_project_name("مشروعي") is True
        assert Validators.validate_project_name("MyProject") is True
        assert Validators.validate_project_name("a") is False  # قصير جداً
        assert Validators.validate_project_name("") is False
    
    def test_validate_color_hex(self):
        """اختبار التحقق من لون HEX"""
        assert Validators.validate_color("#FF6B6B") is True
        assert Validators.validate_color("#F00") is True
        assert Validators.validate_color("red") is True
        assert Validators.validate_color("invalid") is False
    
    def test_validate_hex_color(self):
        """اختبار التحقق من لون HEX فقط"""
        assert Validators.validate_hex_color("#FF6B6B") is True
        assert Validators.validate_hex_color("#F00") is True
        assert Validators.validate_hex_color("FF6B6B") is False
    
    def test_validate_flutterflow_id(self):
        """اختبار التحقق من معرف FlutterFlow"""
        assert Validators.validate_flutterflow_id("ff_123456") is True
        assert Validators.validate_flutterflow_id("invalid") is False
    
    def test_validate_figma_url(self):
        """اختبار التحقق من رابط Figma"""
        assert Validators.validate_figma_url("https://figma.com/design/abc123") is True
        assert Validators.validate_figma_url("invalid") is False
    
    def test_validate_lovable_url(self):
        """اختبار التحقق من رابط Lovable"""
        assert Validators.validate_lovable_url("https://lovable.com/project/xyz") is True
        assert Validators.validate_lovable_url("invalid") is False
    
    def test_validate_json(self):
        """اختبار التحقق من JSON"""
        assert Validators.validate_json('{"key": "value"}') is True
        assert Validators.validate_json('invalid json') is False
    
    def test_validate_number(self):
        """اختبار التحقق من الرقم"""
        assert Validators.validate_number(42, min_val=0, max_val=100) is True
        assert Validators.validate_number(150, min_val=0, max_val=100) is False
        assert Validators.validate_number(None) is False
    
    def test_validate_range(self):
        """اختبار التحقق من النطاق"""
        assert Validators.validate_range("red", ["red", "blue", "green"]) is True
        assert Validators.validate_range("yellow", ["red", "blue", "green"]) is False
    
    def test_validate_length(self):
        """اختبار التحقق من الطول"""
        assert Validators.validate_length("test", min_len=2, max_len=10) is True
        assert Validators.validate_length("t", min_len=2, max_len=10) is False
        assert Validators.validate_length("", min_len=2) is False
    
    def test_validate_regex(self):
        """اختبار التحقق باستخدام Regex"""
        assert Validators.validate_regex("test@example.com", r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') is True
        assert Validators.validate_regex("invalid", r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') is False
    
    def test_create_validator(self):
        """اختبار إنشاء مدقق مخصص"""
        validator = Validators.create_validator(r'^[0-9]+$')
        assert validator("123") is True
        assert validator("abc") is False
    
    def test_validate_api_key(self):
        """اختبار التحقق من مفتاح API"""
        assert validate_api_key("AI_1234567890abcdef") is True
        assert validate_api_key("invalid") is False
        assert validate_api_key("") is False
    
    def test_sanitize_input(self):
        """اختبار تنظيف الإدخال"""
        result = sanitize_input("<script>alert('test')</script>")
        assert "<script>" not in result
        assert "alert" not in result


# ============================================================
# اختبارات Helpers - الملفات والمجلدات
# ============================================================

class TestHelpersFiles:
    """اختبارات دوال الملفات والمجلدات"""
    
    def test_ensure_directory(self, tmp_path):
        """اختبار التأكد من وجود مجلد"""
        test_dir = tmp_path / "test" / "subdir"
        result = ensure_directory(test_dir)
        assert result.exists()
        assert result.is_dir()
    
    def test_get_file_size(self, tmp_path):
        """اختبار الحصول على حجم الملف"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        size = get_file_size(test_file)
        assert "B" in size
        assert int(size.split()[0]) > 0
    
    def test_safe_filename(self):
        """اختبار تحويل النص إلى اسم ملف آمن"""
        assert safe_filename("My Project Name") == "My_Project_Name"
        assert safe_filename("اسم مشروع") == "اسم_مشروع"
        assert safe_filename("very long name " * 10, max_length=20) is not None
        assert len(safe_filename("very long name " * 10, max_length=20)) <= 20
    
    def test_read_json_file(self, tmp_path):
        """اختبار قراءة ملف JSON"""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}', encoding='utf-8')
        
        data = read_json_file(test_file)
        assert data == {"key": "value"}
        
        # ملف غير موجود
        data = read_json_file(tmp_path / "non_existent.json")
        assert data is None
    
    def test_write_json_file(self, tmp_path):
        """اختبار كتابة ملف JSON"""
        test_file = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        
        result = write_json_file(test_file, data)
        assert result is True
        assert test_file.exists()
        
        loaded = json.loads(test_file.read_text(encoding='utf-8'))
        assert loaded == data
    
    def test_create_backup(self, tmp_path):
        """اختبار إنشاء نسخة احتياطية"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        backup = create_backup(test_file)
        assert backup is not None
        assert backup.exists()
        assert backup != test_file
    
    def test_get_files_in_directory(self, tmp_path):
        """اختبار الحصول على الملفات في مجلد"""
        # إنشاء ملفات
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").touch()
        
        files = get_files_in_directory(tmp_path, "*.txt")
        assert len(files) == 2
        
        files_recursive = get_files_in_directory(tmp_path, "*.txt", recursive=True)
        assert len(files_recursive) == 3
    
    def test_cleanup_old_files(self, tmp_path):
        """اختبار حذف الملفات القديمة"""
        # إنشاء ملفات قديمة وحديثة
        old_file = tmp_path / "old.txt"
        old_file.touch()
        # تغيير وقت التعديل إلى أقدم
        old_time = datetime.now() - timedelta(days=40)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        new_file = tmp_path / "new.txt"
        new_file.touch()
        
        count = cleanup_old_files(tmp_path, days_old=30)
        assert count == 1
        assert not old_file.exists()
        assert new_file.exists()


# ============================================================
# اختبارات Helpers - الوقت والتاريخ
# ============================================================

class TestHelpersTime:
    """اختبارات دوال الوقت والتاريخ"""
    
    def test_format_duration(self):
        """اختبار تنسيق المدة"""
        assert "ثانية" in format_duration(30)
        assert "دقيقة" in format_duration(90)
        assert "ساعة" in format_duration(4000)
        assert "يوم" in format_duration(100000)
    
    def test_get_timestamp(self):
        """اختبار الحصول على طابع زمني"""
        timestamp = get_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
    
    def test_get_timestamp_filename(self):
        """اختبار الحصول على اسم ملف بزمن"""
        filename = get_timestamp_filename()
        assert isinstance(filename, str)
        assert len(filename) > 0
    
    def test_time_function(self):
        """اختبار قياس وقت تنفيذ دالة"""
        def slow_function():
            import time
            time.sleep(0.1)
            return "done"
        
        result, elapsed = time_function(slow_function)
        assert result == "done"
        assert elapsed >= 0.1


# ============================================================
# اختبارات Helpers - النصوص والتحويلات
# ============================================================

class TestHelpersText:
    """اختبارات دوال النصوص والتحويلات"""
    
    def test_truncate_text(self):
        """اختبار تقليل طول النص"""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, 20)
        assert len(result) <= 20
        assert "..." in result
        
        # نص قصير
        result = truncate_text("short", 20)
        assert result == "short"
    
    def test_convert_to_slug(self):
        """اختبار تحويل النص إلى Slug"""
        assert convert_to_slug("My Project Name") == "my-project-name"
        assert convert_to_slug("اسم مشروع") == "اسم-مشروع"
        assert convert_to_slug("Hello World!") == "hello-world"
    
    def test_extract_hashtags(self):
        """اختبار استخراج الهاشتاجات"""
        text = "Hello #world and #python #coding"
        result = extract_hashtags(text)
        assert "world" in result
        assert "python" in result
        assert "coding" in result
    
    def test_extract_mentions(self):
        """اختبار استخراج الإشارات"""
        text = "Hello @user1 and @user2"
        result = extract_mentions(text)
        assert "user1" in result
        assert "user2" in result


# ============================================================
# اختبارات Helpers - التجزئة والتشفير
# ============================================================

class TestHelpersHash:
    """اختبارات دوال التجزئة والتشفير"""
    
    def test_hash_string(self):
        """اختبار تجزئة النص"""
        result = hash_string("test")
        assert len(result) == 32  # MD5
        assert result == hash_string("test")  # يجب أن تكون متطابقة
        assert hash_string("test") != hash_string("different")
    
    def test_hash_string_sha256(self):
        """اختبار تجزئة النص باستخدام SHA256"""
        result = hash_string("test", "sha256")
        assert len(result) == 64  # SHA256
    
    def test_hash_file(self, tmp_path):
        """اختبار تجزئة الملف"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = hash_file(test_file)
        assert result is not None
        assert len(result) == 32


# ============================================================
# اختبارات Helpers - النظام والبيئة
# ============================================================

class TestHelpersSystem:
    """اختبارات دوال النظام والبيئة"""
    
    def test_get_system_info(self):
        """اختبار الحصول على معلومات النظام"""
        info = get_system_info()
        assert "system" in info
        assert "python" in info
        assert "cpu_count" in info
        assert isinstance(info["cpu_count"], int)
    
    def test_get_terminal_size(self):
        """اختبار الحصول على حجم المحطة"""
        width, height = get_terminal_size()
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0


# ============================================================
# اختبارات Helpers - القوائم والمجموعات
# ============================================================

class TestHelpersLists:
    """اختبارات دوال القوائم والمجموعات"""
    
    def test_chunk_list(self):
        """اختبار تقسيم القائمة"""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunks = chunk_list(items, 3)
        assert len(chunks) == 4
        assert chunks[0] == [1, 2, 3]
        assert chunks[-1] == [10]
    
    def test_flatten_list(self):
        """اختبار تسوية القائمة"""
        nested = [1, [2, 3], [4, [5, 6]]]
        flat = flatten_list(nested)
        assert flat == [1, 2, 3, 4, 5, 6]
    
    def test_unique_items(self):
        """اختبار إزالة المكررات"""
        items = [1, 2, 2, 3, 3, 3, 4]
        unique = unique_items(items)
        assert unique == [1, 2, 3, 4]
        
        # بدون الحفاظ على الترتيب
        unique_no_order = unique_items(items, preserve_order=False)
        assert set(unique_no_order) == {1, 2, 3, 4}
    
    def test_merge_dicts(self):
        """اختبار دمج القواميس"""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        
        merged = merge_dicts(dict1, dict2)
        assert merged["a"] == 1
        assert merged["b"]["c"] == 2
        assert merged["b"]["d"] == 3
        assert merged["e"] == 4


# ============================================================
# اختبارات Helpers - دوال مساعدة أخرى
# ============================================================

class TestHelpersOther:
    """اختبارات دوال مساعدة أخرى"""
    
    def test_get_nested_value(self):
        """اختبار الحصول على قيمة متداخلة"""
        data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        
        assert get_nested_value(data, "user.profile.name") == "John"
        assert get_nested_value(data, "user.profile.age") == 30
        assert get_nested_value(data, "user.profile.email", "default") == "default"
    
    def test_set_nested_value(self):
        """اختبار تعيين قيمة متداخلة"""
        data = {}
        result = set_nested_value(data, "user.profile.name", "John")
        assert result["user"]["profile"]["name"] == "John"
    
    def test_generate_id(self):
        """اختبار إنشاء معرف"""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        assert len(id1) == 8
        
        id_with_prefix = generate_id("test", 10)
        assert id_with_prefix.startswith("test_")
        assert len(id_with_prefix) > 10
    
    def test_format_file_size(self):
        """اختبار تنسيق حجم الملف"""
        assert format_file_size(500) == "500.0 B"
        assert "KB" in format_file_size(2048)
        assert "MB" in format_file_size(2 * 1024 * 1024)


# ============================================================
# اختبارات Helpers - السجلات والإحصائيات
# ============================================================

class TestHelpersLogs:
    """اختبارات دوال السجلات والإحصائيات"""
    
    def test_export_logs_to_zip(self, tmp_path):
        """اختبار تصدير السجلات إلى ZIP"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        # إنشاء ملف سجل
        log_file = log_dir / "test.log"
        log_file.write_text("test log content")
        
        result = export_logs_to_zip(log_dir, output_name="logs.zip")
        assert result is not None
        assert result.exists()
    
    def test_get_logs_summary(self, tmp_path):
        """اختبار الحصول على ملخص السجلات"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        # إنشاء ملفات سجل
        for i in range(3):
            log_file = log_dir / f"test{i}.log"
            log_file.write_text(f"test content {i}")
        
        summary = get_logs_summary(log_dir)
        assert summary["total_files"] == 3
        assert "total_size" in summary


# ============================================================
# تشغيل الاختبارات
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])