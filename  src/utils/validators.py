"""
LugyFlutter - نظام التحقق من صحة البيانات (Validators)
مجموعة متكاملة من دوال التحقق من صحة المدخلات والبيانات
"""

import re
from typing import Optional, Any, List, Union, Callable
from datetime import datetime
from urllib.parse import urlparse
import json

from .colors import Colors, print_colored


class Validators:
    """
    مجموعة دوال التحقق من صحة البيانات
    الميزات:
    - التحقق من البريد الإلكتروني
    - التحقق من الروابط
    - التحقق من أرقام الهواتف
    - التحقق من أسماء المشاريع
    - التحقق من الألوان
    - التحقق من التواريخ
    - التحقق من الملفات
    - إنشاء دوال تحقق مخصصة
    """
    
    # أنماط Regex الشائعة
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[^\s]+$',
        'phone': r'^\+?[0-9]{1,3}[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,4}$',
        'project_name': r'^[\w\s\-_\u0600-\u06FF]{2,50}$',
        'hex_color': r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        'rgb_color': r'^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$',
        'rgba_color': r'^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([01]?\.?\d*?)\s*\)$',
        'widget_name': r'^[A-Z][a-zA-Z0-9]*$',
        'flutterflow_id': r'^ff_[a-zA-Z0-9]+$',
        'figma_url': r'^https?://(?:www\.)?figma\.com/(?:file|design)/[^\s]+$',
        'lovable_url': r'^https?://(?:www\.)?lovable\.(?:com|ai|dev)/[^\s]+$',
    }
    
    # أسماء الألوان المدعومة
    COLOR_NAMES = {
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
        'brown', 'black', 'white', 'gray', 'grey', 'cyan', 'magenta',
        'أحمر', 'أزرق', 'أخضر', 'أصفر', 'برتقالي', 'بنفسجي', 'وردي',
        'بني', 'أسود', 'أبيض', 'رمادي', 'سماوي', 'نيلي'
    }
    
    @classmethod
    def validate_email(cls, value: str) -> bool:
        """
        التحقق من صحة البريد الإلكتروني
        
        Args:
            value: البريد الإلكتروني المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['email'], value))
    
    @classmethod
    def validate_url(cls, value: str, require_https: bool = False) -> bool:
        """
        التحقق من صحة الرابط
        
        Args:
            value: الرابط المراد التحقق منه
            require_https: طلب استخدام HTTPS
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        
        if not re.match(cls.PATTERNS['url'], value):
            return False
        
        if require_https and not value.startswith('https://'):
            return False
        
        try:
            parsed = urlparse(value)
            return bool(parsed.netloc)
        except:
            return False
    
    @classmethod
    def validate_phone(cls, value: str) -> bool:
        """
        التحقق من صحة رقم الهاتف
        
        Args:
            value: رقم الهاتف المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['phone'], value))
    
    @classmethod
    def validate_project_name(cls, value: str) -> bool:
        """
        التحقق من صحة اسم المشروع
        
        Args:
            value: اسم المشروع المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        
        # التحقق من الطول
        if len(value) < 2 or len(value) > 50:
            return False
        
        # التحقق من الأحرف المسموحة
        return bool(re.match(cls.PATTERNS['project_name'], value))
    
    @classmethod
    def validate_color(cls, value: str) -> bool:
        """
        التحقق من صحة اللون (HEX, RGB, RGBA, أو اسم)
        
        Args:
            value: اللون المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        
        # التحقق من HEX
        if re.match(cls.PATTERNS['hex_color'], value):
            return True
        
        # التحقق من RGB
        if re.match(cls.PATTERNS['rgb_color'], value):
            return True
        
        # التحقق من RGBA
        if re.match(cls.PATTERNS['rgba_color'], value):
            return True
        
        # التحقق من اسم اللون
        return value.lower() in cls.COLOR_NAMES
    
    @classmethod
    def validate_widget_name(cls, value: str) -> bool:
        """
        التحقق من صحة اسم Widget (يبدأ بحرف كبير)
        
        Args:
            value: اسم الـ Widget المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['widget_name'], value))
    
    @classmethod
    def validate_hex_color(cls, value: str) -> bool:
        """
        التحقق من صحة لون HEX
        
        Args:
            value: لون HEX المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['hex_color'], value))
    
    @classmethod
    def validate_rgb_color(cls, value: str) -> bool:
        """
        التحقق من صحة لون RGB
        
        Args:
            value: لون RGB المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['rgb_color'], value))
    
    @classmethod
    def validate_flutterflow_id(cls, value: str) -> bool:
        """
        التحقق من صحة معرف FlutterFlow
        
        Args:
            value: المعرف المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['flutterflow_id'], value))
    
    @classmethod
    def validate_figma_url(cls, value: str) -> bool:
        """
        التحقق من صحة رابط Figma
        
        Args:
            value: الرابط المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['figma_url'], value))
    
    @classmethod
    def validate_lovable_url(cls, value: str) -> bool:
        """
        التحقق من صحة رابط Lovable
        
        Args:
            value: الرابط المراد التحقق منه
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        return bool(re.match(cls.PATTERNS['lovable_url'], value))
    
    @classmethod
    def validate_date(cls, value: str, format_str: str = '%Y-%m-%d') -> bool:
        """
        التحقق من صحة التاريخ
        
        Args:
            value: التاريخ المراد التحقق منه
            format_str: تنسيق التاريخ
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if not value:
            return False
        
        try:
            datetime.strptime(value, format_str)
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_json(cls, value: str) -> bool:
        """
        التحقق من صحة JSON
        
        Args:
            value: النص المراد التحقق منه
        
        Returns:
            bool: True إذا كان JSON صحيحاً
        """
        if not value:
            return False
        
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False
    
    @classmethod
    def validate_number(
        cls,
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        allow_float: bool = True
    ) -> bool:
        """
        التحقق من صحة الرقم
        
        Args:
            value: الرقم المراد التحقق منه
            min_val: الحد الأدنى
            max_val: الحد الأقصى
            allow_float: السماح بالأرقام العشرية
        
        Returns:
            bool: True إذا كان صحيحاً
        """
        if value is None:
            return False
        
        try:
            num = float(value) if allow_float else int(value)
            
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_range(
        cls,
        value: Any,
        valid_values: List[Any],
        case_sensitive: bool = True
    ) -> bool:
        """
        التحقق من أن القيمة ضمن قائمة القيم الصحيحة
        
        Args:
            value: القيمة المراد التحقق منها
            valid_values: قائمة القيم الصحيحة
            case_sensitive: تمييز حالة الأحرف
        
        Returns:
            bool: True إذا كانت القيمة صحيحة
        """
        if not valid_values:
            return False
        
        if not case_sensitive and isinstance(value, str):
            value = value.lower()
            valid_values = [v.lower() if isinstance(v, str) else v for v in valid_values]
        
        return value in valid_values
    
    @classmethod
    def validate_length(
        cls,
        value: str,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None
    ) -> bool:
        """
        التحقق من طول النص
        
        Args:
            value: النص المراد التحقق منه
            min_len: الحد الأدنى للطول
            max_len: الحد الأقصى للطول
        
        Returns:
            bool: True إذا كان الطول صحيحاً
        """
        if not value:
            return False
        
        length = len(value)
        
        if min_len is not None and length < min_len:
            return False
        if max_len is not None and length > max_len:
            return False
        
        return True
    
    @classmethod
    def validate_regex(cls, value: str, pattern: str) -> bool:
        """
        التحقق من النص باستخدام Regex مخصص
        
        Args:
            value: النص المراد التحقق منه
            pattern: نمط Regex
        
        Returns:
            bool: True إذا تطابق النص
        """
        if not value or not pattern:
            return False
        return bool(re.match(pattern, value))
    
    @classmethod
    def validate_file_exists(cls, file_path: str) -> bool:
        """
        التحقق من وجود ملف
        
        Args:
            file_path: مسار الملف
        
        Returns:
            bool: True إذا كان الملف موجوداً
        """
        if not file_path:
            return False
        return Path(file_path).exists()
    
    @classmethod
    def validate_file_extension(cls, file_path: str, extensions: List[str]) -> bool:
        """
        التحقق من امتداد الملف
        
        Args:
            file_path: مسار الملف
            extensions: قائمة الامتدادات المسموحة
        
        Returns:
            bool: True إذا كان الامتداد مسموحاً
        """
        if not file_path or not extensions:
            return False
        
        file_ext = Path(file_path).suffix.lower()
        if not file_ext:
            return False
        
        return file_ext in [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    
    @classmethod
    def create_validator(cls, pattern: str) -> Callable[[str], bool]:
        """
        إنشاء دالة تحقق مخصصة باستخدام نمط Regex
        
        Args:
            pattern: نمط Regex
        
        Returns:
            Callable: دالة التحقق
        """
        def validator(value: str) -> bool:
            if not value:
                return False
            return bool(re.match(pattern, value))
        
        return validator
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, str]:
        """الحصول على جميع أنماط Regex"""
        return cls.PATTERNS.copy()
    
    @classmethod
    def get_color_names(cls) -> List[str]:
        """الحصول على قائمة أسماء الألوان"""
        return sorted(list(cls.COLOR_NAMES))


def validate_api_key(value: str) -> bool:
    """
    التحقق من صحة مفتاح API (يبدأ بـ AI)
    
    Args:
        value: مفتاح API المراد التحقق منه
    
    Returns:
        bool: True إذا كان صحيحاً
    """
    if not value:
        return False
    
    if len(value) < 20:
        return False
    
    if not value.startswith("AI"):
        return False
    
    return True


def sanitize_input(value: str, strip_html: bool = True, allow_spaces: bool = True) -> str:
    """
    تنظيف الإدخال من الأحرف الضارة
    
    Args:
        value: النص المراد تنظيفه
        strip_html: إزالة أكواد HTML
        allow_spaces: السماح بالمسافات
    
    Returns:
        str: النص المنظف
    """
    if not value:
        return ""
    
    # إزالة أكواد HTML
    if strip_html:
        import html
        value = html.escape(value)
    
    # إزالة الأحرف الخطرة
    import re
    if allow_spaces:
        value = re.sub(r'[<>/\\|:]', '', value)
    else:
        value = re.sub(r'[<>/\\|:\s]', '', value)
    
    return value.strip()


def is_interactive() -> bool:
    """التحقق مما إذا كانت الجلسة تفاعلية"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def get_validator_error_message(validator_func: Callable, value: Any) -> str:
    """
    الحصول على رسالة خطأ مخصصة لدالة التحقق
    
    Args:
        validator_func: دالة التحقق
        value: القيمة التي فشلت في التحقق
    
    Returns:
        str: رسالة الخطأ
    """
    func_name = validator_func.__name__ if hasattr(validator_func, '__name__') else str(validator_func)
    
    messages = {
        'validate_email': 'البريد الإلكتروني غير صحيح',
        'validate_url': 'الرابط غير صحيح',
        'validate_phone': 'رقم الهاتف غير صحيح',
        'validate_project_name': 'اسم المشروع غير صحيح (يجب أن يكون 2-50 حرفاً)',
        'validate_color': 'اللون غير صحيح (HEX, RGB, أو اسم لون)',
        'validate_widget_name': 'اسم الـ Widget غير صحيح (يجب أن يبدأ بحرف كبير)',
        'validate_hex_color': 'لون HEX غير صحيح',
        'validate_rgb_color': 'لون RGB غير صحيح',
        'validate_flutterflow_id': 'معرف FlutterFlow غير صحيح',
        'validate_figma_url': 'رابط Figma غير صحيح',
        'validate_lovable_url': 'رابط Lovable غير صحيح',
        'validate_json': 'نص JSON غير صحيح',
        'validate_number': 'الرقم غير صحيح',
        'validate_file_exists': 'الملف غير موجود',
        'validate_api_key': 'مفتاح API غير صحيح (يجب أن يبدأ بـ AI وطوله 20+ حرفاً)',
    }
    
    return messages.get(func_name, f'التحقق من {func_name} فشل')


__all__ = [
    "Validators",
    "validate_api_key",
    "sanitize_input",
    "is_interactive",
    "get_validator_error_message"
]