"""
LugyFlutter - اختبارات الوحدة
"""

# هذا الملف يجعل مجلد الاختبارات حزمة Python
# يمكن استخدامه لاستيراد دوال مساعدة للاختبارات

from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent / "fixtures"

def get_test_data(filename: str) -> Path:
    """الحصول على مسار ملف بيانات الاختبار"""
    return TEST_DATA_DIR / filename

__all__ = [
    "TEST_DATA_DIR",
    "get_test_data",
]