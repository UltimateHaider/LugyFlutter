"""
LugyFlutter - ألوان الطباعة (Colors)
نظام متقدم للألوان في المحطة الطرفية مع دعم المنصات المختلفة
"""

import sys
import platform
from typing import Optional, Dict, Tuple


class Colors:
    """
    ألوان للطباعة في المحطة الطرفية
    يدعم:
    - الألوان الأساسية
    - الألوان المخصصة (256 لون)
    - الأنماط (غامق، مائل، مسطر)
    - الكشف التلقائي عن دعم الألوان
    """
    
    # الألوان الأساسية
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    LIGHT_BLACK = '\033[90m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'
    LIGHT_WHITE = '\033[97m'
    
    # خلفيات
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_LIGHT_BLACK = '\033[100m'
    BG_LIGHT_RED = '\033[101m'
    BG_LIGHT_GREEN = '\033[102m'
    BG_LIGHT_YELLOW = '\033[103m'
    BG_LIGHT_BLUE = '\033[104m'
    BG_LIGHT_MAGENTA = '\033[105m'
    BG_LIGHT_CYAN = '\033[106m'
    BG_LIGHT_WHITE = '\033[107m'
    
    # الأنماط
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    STRIKE = '\033[9m'
    
    # إعادة التعيين
    END = '\033[0m'
    RESET = END
    
    # ألوان خاصة بـ LugyFlutter
    LUGY = '\033[38;5;99m'  # لون بنفسجي غامق
    LUGY_LIGHT = '\033[38;5;141m'  # لون بنفسجي فاتح
    LUGY_BG = '\033[48;5;99m'  # خلفية بنفسجية
    LUGY_BG_LIGHT = '\033[48;5;141m'  # خلفية بنفسجية فاتحة
    
    # ألوان مخصصة للواجهة
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = CYAN
    DEBUG = MAGENTA
    
    # مجموعة كاملة من الألوان (للاستخدام مع 256 لون)
    COLOR_256 = {
        i: f'\033[38;5;{i}m' for i in range(256)
    }
    
    BG_256 = {
        i: f'\033[48;5;{i}m' for i in range(256)
    }
    
    # اسماء الألوان الشائعة
    COLOR_NAMES = {
        'black': BLACK,
        'red': RED,
        'green': GREEN,
        'yellow': YELLOW,
        'blue': BLUE,
        'magenta': MAGENTA,
        'cyan': CYAN,
        'white': WHITE,
        'light_black': LIGHT_BLACK,
        'light_red': LIGHT_RED,
        'light_green': LIGHT_GREEN,
        'light_yellow': LIGHT_YELLOW,
        'light_blue': LIGHT_BLUE,
        'light_magenta': LIGHT_MAGENTA,
        'light_cyan': LIGHT_CYAN,
        'light_white': LIGHT_WHITE,
        'lugy': LUGY,
        'lugy_light': LUGY_LIGHT,
    }
    
    # الكشف عن دعم الألوان
    _supports_color: Optional[bool] = None
    
    @classmethod
    def supports_color(cls) -> bool:
        """التحقق مما إذا كانت المحطة تدعم الألوان"""
        if cls._supports_color is not None:
            return cls._supports_color
        
        # Windows
        if platform.system() == 'Windows':
            try:
                import colorama
                colorama.init()
                cls._supports_color = True
                return True
            except ImportError:
                # محاولة استخدام ANSI في Windows 10+
                import os
                if 'ANSICON' in os.environ:
                    cls._supports_color = True
                    return True
                if 'WT_SESSION' in os.environ:  # Windows Terminal
                    cls._supports_color = True
                    return True
                cls._supports_color = False
                return False
        
        # Unix/Linux/Mac
        if not sys.stdout.isatty():
            cls._supports_color = False
            return False
        
        # التحقق من متغير البيئة
        import os
        term = os.environ.get('TERM', '')
        if term in ('dumb', 'unknown'):
            cls._supports_color = False
            return False
        
        cls._supports_color = True
        return True
    
    @classmethod
    def get_color(cls, color_name: str, default: str = WHITE) -> str:
        """الحصول على لون باسمه"""
        return cls.COLOR_NAMES.get(color_name, default)
    
    @classmethod
    def get_256_color(cls, code: int) -> str:
        """الحصول على لون من لوحة 256 لون"""
        if 0 <= code <= 255:
            return cls.COLOR_256[code]
        return cls.WHITE
    
    @classmethod
    def get_256_bg(cls, code: int) -> str:
        """الحصول على خلفية من لوحة 256 لون"""
        if 0 <= code <= 255:
            return cls.BG_256[code]
        return cls.BG_WHITE
    
    @classmethod
    def get_rgb_color(cls, r: int, g: int, b: int) -> str:
        """
        الحصول على لون RGB باستخدام الألوان الممتدة
        ملاحظة: يعمل فقط في المحطات التي تدعم الألوان الحقيقية
        """
        return f'\033[38;2;{r};{g};{b}m'
    
    @classmethod
    def get_rgb_bg(cls, r: int, g: int, b: int) -> str:
        """الحصول على خلفية RGB"""
        return f'\033[48;2;{r};{g};{b}m'
    
    @classmethod
    def strip_colors(cls, text: str) -> str:
        """إزالة جميع أكواد الألوان من النص"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    @classmethod
    def get_color_codes(cls) -> Dict[str, str]:
        """الحصول على جميع أكواد الألوان المتاحة"""
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if not name.startswith('_') and
               isinstance(getattr(cls, name), str) and
               getattr(cls, name).startswith('\033[')
        }


# دوال مساعدة للطباعة

def print_colored(
    message: str,
    color: str = Colors.BLUE,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    bg_color: str = "",
    end: str = '\n',
    flush: bool = True
):
    """
    طباعة نص ملون في المحطة
    
    Args:
        message: النص المراد طباعته
        color: لون النص
        bold: جعل النص غامقاً
        italic: جعل النص مائلاً
        underline: تسطير النص
        bg_color: لون الخلفية
        end: نهاية السطر
        flush: تحديث فوري
    """
    if not Colors.supports_color():
        print(message, end=end)
        return
    
    prefix = ""
    if bold:
        prefix += Colors.BOLD
    if italic:
        prefix += Colors.ITALIC
    if underline:
        prefix += Colors.UNDERLINE
    
    suffix = Colors.END
    
    print(f"{prefix}{color}{bg_color}{message}{suffix}", end=end, flush=flush)


def print_success(message: str, **kwargs):
    """طباعة رسالة نجاح"""
    print_colored(f"✅ {message}", Colors.SUCCESS, **kwargs)


def print_error(message: str, **kwargs):
    """طباعة رسالة خطأ"""
    print_colored(f"❌ {message}", Colors.ERROR, **kwargs)


def print_warning(message: str, **kwargs):
    """طباعة رسالة تحذير"""
    print_colored(f"⚠️ {message}", Colors.WARNING, **kwargs)


def print_info(message: str, **kwargs):
    """طباعة رسالة معلومات"""
    print_colored(f"ℹ️ {message}", Colors.INFO, **kwargs)


def print_debug(message: str, **kwargs):
    """طباعة رسالة تصحيح"""
    print_colored(f"🔍 {message}", Colors.DEBUG, **kwargs)


def print_lugy_logo():
    """طباعة شعار LugyFlutter"""
    logo = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║  ██╗     ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██╗             ║
    ║  ██║     ██║   ██║██╔════╝ ╚██╗ ██╔╝██╔════╝██║             ║
    ║  ██║     ██║   ██║██║  ███╗ ╚████╔╝ █████╗  ██║             ║
    ║  ██║     ██║   ██║██║   ██║  ╚██╔╝  ██╔══╝  ██║             ║
    ║  ███████╗╚██████╔╝╚██████╔╝   ██║   ██║     ███████╗        ║
    ║  ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚══════╝        ║
    ║                                                               ║
    ║  ███████╗██╗     ██╗   ██╗████████╗████████╗███████╗██████╗  ║
    ║  ██╔════╝██║     ██║   ██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗ ║
    ║  █████╗  ██║     ██║   ██║   ██║      ██║   █████╗  ██████╔╝ ║
    ║  ██╔══╝  ██║     ██║   ██║   ██║      ██║   ██╔══╝  ██╔══██╗ ║
    ║  ██║     ███████╗╚██████╔╝   ██║      ██║   ███████╗██║  ██║ ║
    ║  ╚═╝     ╚══════╝ ╚═════╝    ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝ ║
    ║                                                               ║
    ║     🤖 الوكيل الذكي المتخصص في FlutterFlow                   ║
    ║     📌 الإصدار 2.0.0 | 🚀 Legendary User Guide               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print_colored(logo, Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)


def print_header(text: str, color: str = Colors.LUGY, width: int = 70):
    """طباعة رأس مع إطار"""
    print_colored("=" * width, color)
    print_colored(f"  {text}", color, bold=True)
    print_colored("=" * width, color)


def print_section(text: str, color: str = Colors.CYAN):
    """طباعة قسم"""
    print_colored(f"\n📌 {text}", color, bold=True)
    print_colored("-" * 50, color)


def print_table(headers: List[str], rows: List[List[str]], color: str = Colors.BLUE):
    """طباعة جدول بتنسيق جميل"""
    if not rows:
        return
    
    # حساب عرض الأعمدة
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # إنشاء خط فاصل
    separator = "+".join("-" * (w + 2) for w in col_widths)
    separator = "+" + separator + "+"
    
    # طباعة الرأس
    print_colored(separator, color)
    header_row = "| " + " | ".join(
        headers[i].ljust(col_widths[i]) for i in range(len(headers))
    ) + " |"
    print_colored(header_row, color, bold=True)
    print_colored(separator, color)
    
    # طباعة الصفوف
    for row in rows:
        row_str = "| " + " | ".join(
            str(row[i]).ljust(col_widths[i]) for i in range(len(row))
        ) + " |"
        print_colored(row_str, color)
    
    print_colored(separator, color)


__all__ = [
    "Colors",
    "print_colored",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_debug",
    "print_lugy_logo",
    "print_header",
    "print_section",
    "print_table"
]