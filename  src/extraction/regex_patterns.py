"""
LugyFlutter - أنماط Regex الموحدة
مجموعة ثابتة من الأنماط للاستخدام في جميع أنحاء التطبيق
"""

import re
from typing import Dict, List, Pattern, Optional


class RegexPatterns:
    """
    مجموعة أنماط Regex الموحدة والمحسنة
    """
    
    # ============================================================
    # أنماط عامة
    # ============================================================
    
    EMAIL: Pattern = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )
    
    PHONE: Pattern = re.compile(
        r'\+?[0-9]{1,3}[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,4}',
        re.IGNORECASE
    )
    
    URL: Pattern = re.compile(
        r'https?://[^\s]+|www\.[^\s]+',
        re.IGNORECASE
    )
    
    # ============================================================
    # أنماط FlutterFlow
    # ============================================================
    
    PROJECT_ID: Pattern = re.compile(
        r'ff_[a-zA-Z0-9]+',
        re.IGNORECASE
    )
    
    WIDGET_ID: Pattern = re.compile(
        r'w_[a-zA-Z0-9]+',
        re.IGNORECASE
    )
    
    FLUTTERFLOW_URL: Pattern = re.compile(
        r'https?://(?:app\.)?flutterflow\.io/[^\s]+',
        re.IGNORECASE
    )
    
    # ============================================================
    # أنماط الألوان
    # ============================================================
    
    HEX_COLOR: Pattern = re.compile(
        r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'
    )
    
    RGB_COLOR: Pattern = re.compile(
        r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
        re.IGNORECASE
    )
    
    RGBA_COLOR: Pattern = re.compile(
        r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)',
        re.IGNORECASE
    )
    
    COLOR_NAMES = {
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 
        'pink', 'brown', 'black', 'white', 'gray', 'grey',
        'أحمر', 'أزرق', 'أخضر', 'أصفر', 'برتقالي', 'بنفسجي',
        'وردي', 'بني', 'أسود', 'أبيض', 'رمادي'
    }
    
    # ============================================================
    # أنماط التنسيق
    # ============================================================
    
    JSON_OBJECT: Pattern = re.compile(r'\{[^{}]*\}')
    JSON_ARRAY: Pattern = re.compile(r'\[[^\[\]]*\]')
    
    DATE_ISO: Pattern = re.compile(
        r'\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?'
    )
    
    # ============================================================
    # أنماط المشاريع والتطبيقات
    # ============================================================
    
    PROJECT_NAME: Pattern = re.compile(
        r'(?:project|app|اسم المشروع|اسم التطبيق)\s*[:.]?\s*["\']?([^"\'.,\n\r]+)',
        re.IGNORECASE | re.UNICODE
    )
    
    APP_NAME: Pattern = re.compile(
        r'(?:تطبيق|app)\s+["\']?([^"\'،\s.،\n\r]+)',
        re.IGNORECASE | re.UNICODE
    )
    
    # ============================================================
    # أنماط المنصات
    # ============================================================
    
    FIGMA_URL: Pattern = re.compile(
        r'https?://(?:www\.)?figma\.com/(?:file|design)/[^\s]+',
        re.IGNORECASE
    )
    
    LOVABLE_URL: Pattern = re.compile(
        r'https?://(?:www\.)?lovable\.(?:com|ai|dev)/[^\s]+',
        re.IGNORECASE
    )
    
    GITHUB_URL: Pattern = re.compile(
        r'https?://(?:www\.)?github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+',
        re.IGNORECASE
    )
    
    # ============================================================
    # دوال مساعدة
    # ============================================================
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, Pattern]:
        """الحصول على جميع الأنماط كقاموس"""
        return {
            "email": cls.EMAIL,
            "phone": cls.PHONE,
            "url": cls.URL,
            "project_id": cls.PROJECT_ID,
            "widget_id": cls.WIDGET_ID,
            "flutterflow_url": cls.FLUTTERFLOW_URL,
            "hex_color": cls.HEX_COLOR,
            "rgb_color": cls.RGB_COLOR,
            "rgba_color": cls.RGBA_COLOR,
            "json_object": cls.JSON_OBJECT,
            "json_array": cls.JSON_ARRAY,
            "date_iso": cls.DATE_ISO,
            "project_name": cls.PROJECT_NAME,
            "app_name": cls.APP_NAME,
            "figma_url": cls.FIGMA_URL,
            "lovable_url": cls.LOVABLE_URL,
            "github_url": cls.GITHUB_URL,
        }
    
    @classmethod
    def get_patterns_by_category(cls) -> Dict[str, List[tuple]]:
        """الحصول على الأنماط مصنفة حسب الفئة"""
        return {
            "general": [
                ("البريد الإلكتروني", cls.EMAIL),
                ("رقم الهاتف", cls.PHONE),
                ("رابط", cls.URL),
            ],
            "flutterflow": [
                ("معرف المشروع", cls.PROJECT_ID),
                ("معرف الـ Widget", cls.WIDGET_ID),
                ("رابط FlutterFlow", cls.FLUTTERFLOW_URL),
            ],
            "colors": [
                ("لون HEX", cls.HEX_COLOR),
                ("لون RGB", cls.RGB_COLOR),
                ("لون RGBA", cls.RGBA_COLOR),
            ],
            "projects": [
                ("اسم المشروع", cls.PROJECT_NAME),
                ("اسم التطبيق", cls.APP_NAME),
            ],
            "platforms": [
                ("رابط Figma", cls.FIGMA_URL),
                ("رابط Lovable", cls.LOVABLE_URL),
                ("رابط GitHub", cls.GITHUB_URL),
            ],
        }
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, List[str]]:
        """
        استخراج جميع الأنماط من النص
        
        Args:
            text: النص المراد استخراج الأنماط منه
        
        Returns:
            قاموس يحتوي على جميع الأنماط المستخرجة
        """
        result = {}
        
        for name, pattern in cls.get_all_patterns().items():
            matches = pattern.findall(text)
            if matches:
                result[name] = matches
        
        return result
    
    @classmethod
    def has_pattern(cls, text: str, pattern_name: str) -> bool:
        """التحقق من وجود نمط معين في النص"""
        patterns = cls.get_all_patterns()
        if pattern_name not in patterns:
            return False
        return bool(patterns[pattern_name].search(text))
    
    @classmethod
    def get_matching_patterns(cls, text: str) -> List[str]:
        """الحصول على أسماء الأنماط الموجودة في النص"""
        matches = []
        for name, pattern in cls.get_all_patterns().items():
            if pattern.search(text):
                matches.append(name)
        return matches