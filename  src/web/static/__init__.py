"""
LugyFlutter - الملفات الثابتة للواجهة
"""

# هذا الملف اختياري للمجلدات الفارغة
# يمكنك حذفه إذا لم يكن هناك حاجة له

from pathlib import Path

STATIC_DIR = Path(__file__).parent

__all__ = ["STATIC_DIR"]