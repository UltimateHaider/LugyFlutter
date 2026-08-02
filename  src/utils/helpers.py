"""
LugyFlutter - الدوال المساعدة (Helpers)
مجموعة من الدوال المساعدة للاستخدام العام في جميع أنحاء التطبيق
"""

import os
import sys
import re
import json
import time
import shutil
import hashlib
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Callable, Tuple
from collections import defaultdict

from .colors import Colors, print_colored, print_success, print_error, print_warning, print_info
from .logger import debug, info, warning, error, get_logger

logger = get_logger(__name__)


# ============================================================
# 1. دوال فحص المكتبات والبيئة
# ============================================================

def check_required_libraries() -> List[str]:
    """
    فحص المكتبات المطلوبة وتثبيتها تلقائياً
    
    Returns:
        List[str]: قائمة المكتبات المفقودة
    """
    required = {
        "browser_use": "browser-use",
        "langchain_google_genai": "langchain-google-genai",
        "google.generativeai": "google-generativeai",
        "PIL": "pillow",
        "bs4": "beautifulsoup4",
        "dotenv": "python-dotenv",
        "streamlit": "streamlit",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "pytest": "pytest",
        "cv2": "opencv-python",
        "pytesseract": "pytesseract",
        "playwright": "playwright"
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print_warning(f"المكتبات التالية غير مثبتة: {', '.join(missing)}")
        print_info("💡 هل تريد تثبيتها تلقائياً؟")
        
        choice = input("تثبيت؟ (نعم/لا): ").strip().lower()
        if choice in ["نعم", "yes", "y"]:
            for package in missing:
                print_info(f"📦 جاري تثبيت {package}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                except Exception as e:
                    print_error(f"فشل تثبيت {package}: {e}")
            
            # تثبيت Playwright
            if "playwright" in missing:
                print_info("📦 جاري تثبيت Playwright...")
                try:
                    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
                    print_success("تم تثبيت Playwright بنجاح!")
                except Exception as e:
                    print_error(f"فشل تثبيت Playwright: {e}")
            
            print_success("تم تثبيت جميع المكتبات بنجاح!")
        else:
            print_warning("سيتم الاستمرار مع المكتبات الموجودة. قد تفشل بعض الوظائف.")
    
    return missing


def check_environment() -> Dict[str, Any]:
    """
    فحص البيئة والإعدادات
    
    Returns:
        Dict: نتائج الفحص
    """
    issues = []
    warnings_list = []
    
    # فحص Python
    if sys.version_info < (3, 8):
        issues.append(f"Python {sys.version} - يجب أن يكون 3.8 أو أعلى")
    
    # فحص Playwright
    try:
        import playwright
    except ImportError:
        warnings_list.append("Playwright غير مثبت. سيتم تثبيته تلقائياً عند الحاجة")
    
    # فحص المجلدات
    required_dirs = ["logs", "logs/screenshots", "logs/checkpoints", "logs/context"]
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            info(f"تم إنشاء المجلد: {dir_path}")
    
    return {
        "issues": issues,
        "warnings": warnings_list,
        "is_ready": len(issues) == 0
    }


# ============================================================
# 2. دوال تصدير السجلات والمجلدات
# ============================================================

def export_logs_to_zip(
    log_dir: Union[str, Path],
    output_name: Optional[str] = None,
    include_screenshots: bool = True
) -> Optional[Path]:
    """
    تصدير مجلد السجلات إلى ملف ZIP
    
    Args:
        log_dir: مسار مجلد السجلات
        output_name: اسم ملف التصدير
        include_screenshots: تضمين لقطات الشاشة
    
    Returns:
        Optional[Path]: مسار ملف ZIP أو None
    """
    import zipfile
    
    log_path = Path(log_dir)
    if not log_path.exists():
        print_warning(f"مجلد السجلات غير موجود: {log_dir}")
        return None
    
    if not output_name:
        output_name = f"lugy_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    output_path = Path(output_name)
    
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(log_path):
                # تخطي مجلد الصور إذا لم يكن مطلوباً
                if not include_screenshots and "screenshots" in root:
                    continue
                
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # تحديد المسار النسبي
                        arcname = file_path.relative_to(log_path.parent)
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        print_warning(f"فشل إضافة {file}: {e}")
        
        print_success(f"تم تصدير السجلات إلى: {output_path}")
        print_info(f"📦 حجم الملف: {get_file_size(output_path)}")
        return output_path
        
    except Exception as e:
        print_error(f"فشل تصدير السجلات: {e}")
        return None


def export_logs_to_zip_async(
    log_dir: Union[str, Path],
    output_name: Optional[str] = None,
    include_screenshots: bool = True
) -> asyncio.Future:
    """
    تصدير السجلات بشكل غير متزامن
    
    Args:
        log_dir: مسار مجلد السجلات
        output_name: اسم ملف التصدير
        include_screenshots: تضمين لقطات الشاشة
    
    Returns:
        asyncio.Future: مستقبل النتيجة
    """
    future = asyncio.Future()
    
    def run_export():
        try:
            result = export_logs_to_zip(log_dir, output_name, include_screenshots)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
    
    # تشغيل في ThreadPoolExecutor
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor()
    executor.submit(run_export)
    
    return future


# ============================================================
# 3. دوال الملفات والمجلدات
# ============================================================

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    التأكد من وجود مجلد وإنشائه إذا لزم الأمر
    
    Args:
        path: مسار المجلد
    
    Returns:
        Path: مسار المجلد
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> str:
    """
    الحصول على حجم الملف بتنسيق مقروء
    
    Args:
        file_path: مسار الملف
    
    Returns:
        str: حجم الملف (مثل 1.5 MB)
    """
    path = Path(file_path)
    if not path.exists():
        return "0 B"
    
    size = path.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def safe_filename(text: str, max_length: int = 50) -> str:
    """
    تحويل النص إلى اسم ملف آمن
    
    Args:
        text: النص المراد تحويله
        max_length: الحد الأقصى للطول
    
    Returns:
        str: اسم ملف آمن
    """
    # إزالة الأحرف غير المسموحة
    safe = re.sub(r'[^a-zA-Z0-9\s\-_\u0600-\u06FF]', '', text)
    # استبدال المسافات بشرطات
    safe = safe.replace(' ', '_')
    # تقليل الطول
    if len(safe) > max_length:
        safe = safe[:max_length]
    # إزالة الشرطات الزائدة
    safe = safe.strip('_-')
    return safe


def read_json_file(file_path: Union[str, Path]) -> Optional[Dict]:
    """
    قراءة ملف JSON
    
    Args:
        file_path: مسار الملف
    
    Returns:
        Optional[Dict]: محتوى الملف أو None في حالة الخطأ
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        error(f"فشل قراءة ملف JSON: {e}")
        return None


def write_json_file(file_path: Union[str, Path], data: Dict, indent: int = 2) -> bool:
    """
    كتابة ملف JSON
    
    Args:
        file_path: مسار الملف
        data: البيانات المراد كتابتها
        indent: عدد المسافات للتباعد
    
    Returns:
        bool: نجاح الكتابة
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=indent),
            encoding='utf-8'
        )
        return True
    except Exception as e:
        error(f"فشل كتابة ملف JSON: {e}")
        return False


def create_backup(file_path: Union[str, Path]) -> Optional[Path]:
    """
    إنشاء نسخة احتياطية من ملف
    
    Args:
        file_path: مسار الملف
    
    Returns:
        Optional[Path]: مسار النسخة الاحتياطية
    """
    path = Path(file_path)
    if not path.exists():
        return None
    
    backup_path = path.parent / f"{path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
    
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as e:
        error(f"فشل إنشاء نسخة احتياطية: {e}")
        return None


def get_files_in_directory(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    الحصول على قائمة الملفات في مجلد
    
    Args:
        directory: مسار المجلد
        pattern: نمط البحث
        recursive: البحث بشكل متكرر
    
    Returns:
        List[Path]: قائمة الملفات
    """
    path = Path(directory)
    if not path.exists():
        return []
    
    if recursive:
        return list(path.rglob(pattern))
    else:
        return list(path.glob(pattern))


def cleanup_old_files(
    directory: Union[str, Path],
    pattern: str = "*",
    days_old: int = 30,
    recursive: bool = True
) -> int:
    """
    حذف الملفات القديمة في مجلد
    
    Args:
        directory: مسار المجلد
        pattern: نمط الملفات
        days_old: عدد الأيام للاحتفاظ بالملفات
        recursive: البحث بشكل متكرر
    
    Returns:
        int: عدد الملفات المحذوفة
    """
    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    count = 0
    
    files = get_files_in_directory(directory, pattern, recursive)
    
    for file_path in files:
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                count += 1
            except Exception as e:
                error(f"فشل حذف {file_path}: {e}")
    
    return count


# ============================================================
# 4. دوال الوقت والتاريخ
# ============================================================

def format_duration(seconds: float) -> str:
    """
    تنسيق المدة الزمنية
    
    Args:
        seconds: عدد الثواني
    
    Returns:
        str: المدة المنسقة
    """
    if seconds < 0:
        seconds = 0
    
    if seconds < 60:
        return f"{seconds:.1f} ثانية"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes} دقيقة {secs} ثانية"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} ساعة {minutes} دقيقة"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days} يوم {hours} ساعة"


def get_timestamp(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    الحصول على طابع زمني
    
    Args:
        format_str: تنسيق الوقت
    
    Returns:
        str: الطابع الزمني
    """
    return datetime.now().strftime(format_str)


def get_timestamp_filename() -> str:
    """
    الحصول على اسم ملف مع طابع زمني
    
    Returns:
        str: اسم الملف
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def time_function(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    قياس وقت تنفيذ دالة
    
    Args:
        func: الدالة المراد قياس وقتها
        *args, **kwargs: معاملات الدالة
    
    Returns:
        Tuple[Any, float]: (نتيجة الدالة, الوقت المستغرق بالثواني)
    """
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


async def time_async_function(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    قياس وقت تنفيذ دالة غير متزامنة
    
    Args:
        func: الدالة المراد قياس وقتها
        *args, **kwargs: معاملات الدالة
    
    Returns:
        Tuple[Any, float]: (نتيجة الدالة, الوقت المستغرق بالثواني)
    """
    start = time.time()
    result = await func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


# ============================================================
# 5. دوال النصوص والتحويلات
# ============================================================

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    تقليل طول النص
    
    Args:
        text: النص المراد تقليله
        max_length: الحد الأقصى للطول
        suffix: النهاية المضافة عند التقليل
    
    Returns:
        str: النص المختصر
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def convert_to_slug(text: str) -> str:
    """
    تحويل النص إلى Slug (للروابط)
    
    Args:
        text: النص المراد تحويله
    
    Returns:
        str: Slug
    """
    # تحويل إلى حروف صغيرة
    slug = text.lower()
    # إزالة الأحرف غير المسموحة
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # استبدال المسافات بشرطات
    slug = re.sub(r'\s+', '-', slug)
    # إزالة الشرطات المتتالية
    slug = re.sub(r'-+', '-', slug)
    # إزالة الشرطات من البداية والنهاية
    slug = slug.strip('-')
    return slug


def extract_hashtags(text: str) -> List[str]:
    """
    استخراج الهاشتاجات من النص
    
    Args:
        text: النص المراد استخراج الهاشتاجات منه
    
    Returns:
        List[str]: قائمة الهاشتاجات
    """
    return re.findall(r'#([a-zA-Z0-9_]+)', text)


def extract_mentions(text: str) -> List[str]:
    """
    استخراج الإشارات (@) من النص
    
    Args:
        text: النص المراد استخراج الإشارات منه
    
    Returns:
        List[str]: قائمة الإشارات
    """
    return re.findall(r'@([a-zA-Z0-9_]+)', text)


def extract_emojis(text: str) -> List[str]:
    """
    استخراج الإيموجي من النص
    
    Args:
        text: النص المراد استخراج الإيموجي منه
    
    Returns:
        List[str]: قائمة الإيموجي
    """
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.findall(text)


# ============================================================
# 6. دوال التجزئة والتشفير
# ============================================================

def hash_string(text: str, algorithm: str = 'md5') -> str:
    """
    حساب هاش لنص
    
    Args:
        text: النص المراد حساب هاشه
        algorithm: خوارزمية التجزئة (md5, sha1, sha256)
    
    Returns:
        str: الهاش
    """
    text_bytes = text.encode('utf-8')
    
    if algorithm == 'md5':
        return hashlib.md5(text_bytes).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text_bytes).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(text_bytes).hexdigest()
    else:
        return hashlib.md5(text_bytes).hexdigest()


def hash_file(file_path: Union[str, Path], algorithm: str = 'md5') -> Optional[str]:
    """
    حساب هاش لملف
    
    Args:
        file_path: مسار الملف
        algorithm: خوارزمية التجزئة (md5, sha1, sha256)
    
    Returns:
        Optional[str]: الهاش أو None في حالة الخطأ
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        hasher = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        error(f"فشل حساب هاش الملف: {e}")
        return None


# ============================================================
# 7. دوال النظام والبيئة
# ============================================================

def get_system_info() -> Dict[str, Any]:
    """
    الحصول على معلومات النظام
    
    Returns:
        Dict: معلومات النظام
    """
    import platform
    import psutil
    
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "python_path": sys.executable,
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
        "memory_available": f"{psutil.virtual_memory().available / (1024**3):.1f} GB",
        "disk_usage": f"{psutil.disk_usage('/').percent}%",
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }
    return info


def is_admin() -> bool:
    """التحقق مما إذا كان البرنامج يعمل بصلاحيات مدير"""
    try:
        return os.geteuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def get_terminal_size() -> Tuple[int, int]:
    """
    الحصول على حجم المحطة الطرفية
    
    Returns:
        Tuple[int, int]: (العرض, الارتفاع)
    """
    try:
        import shutil
        columns, rows = shutil.get_terminal_size()
        return columns, rows
    except:
        return 80, 24


def open_url(url: str) -> bool:
    """
    فتح رابط في المتصفح الافتراضي
    
    Args:
        url: الرابط المراد فتحه
    
    Returns:
        bool: نجاح الفتح
    """
    try:
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception as e:
        error(f"فشل فتح الرابط: {e}")
        return False


def is_interactive() -> bool:
    """التحقق مما إذا كانت الجلسة تفاعلية"""
    return sys.stdin.isatty() and sys.stdout.isatty()


# ============================================================
# 8. دوال التقدم والشريط
# ============================================================

def print_progress_bar(
    iteration: int,
    total: int,
    prefix: str = '',
    suffix: str = '',
    length: int = 50,
    fill: str = '█',
    empty: str = '░',
    color: str = Colors.CYAN
):
    """
    طباعة شريط تقدم
    
    Args:
        iteration: التكرار الحالي
        total: إجمالي التكرارات
        prefix: نص البداية
        suffix: نص النهاية
        length: طول الشريط
        fill: حرف التعبئة
        empty: حرف الفارغ
        color: لون الشريط
    """
    if total == 0:
        return
    
    percent = 100 * (iteration / float(total))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + empty * (length - filled_length)
    
    # تحديد اللون حسب النسبة
    if percent < 30:
        bar_color = Colors.RED
    elif percent < 70:
        bar_color = Colors.YELLOW
    else:
        bar_color = Colors.GREEN
    
    # طباعة الشريط
    print(
        f'\r{prefix} {bar_color}|{bar}|{Colors.END} {percent:.1f}% {suffix}',
        end='',
        flush=True
    )
    
    if iteration == total:
        print()  # سطر جديد عند الانتهاء


async def print_progress_bar_async(
    iteration: int,
    total: int,
    prefix: str = '',
    suffix: str = '',
    length: int = 50,
    fill: str = '█',
    empty: str = '░'
):
    """
    طباعة شريط تقدم بشكل غير متزامن
    
    Args:
        iteration: التكرار الحالي
        total: إجمالي التكرارات
        prefix: نص البداية
        suffix: نص النهاية
        length: طول الشريط
        fill: حرف التعبئة
        empty: حرف الفارغ
    """
    # تشغيل في خيط منفصل
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        print_progress_bar,
        iteration,
        total,
        prefix,
        suffix,
        length,
        fill,
        empty
    )


def print_spinner(message: str = "جاري العمل...", delay: float = 0.1):
    """
    طباعة مؤشر تقدم متحرك
    
    Args:
        message: الرسالة المعروضة
        delay: التأخير بين الحركات
    """
    import itertools
    spinner = itertools.cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
    
    try:
        while True:
            sys.stdout.write(f'\r{next(spinner)} {message}')
            sys.stdout.flush()
            time.sleep(delay)
    except KeyboardInterrupt:
        sys.stdout.write('\r✅ تم الإنهاء\n')
        sys.stdout.flush()


# ============================================================
# 9. دوال القوائم والمجموعات
# ============================================================

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    تقسيم قائمة إلى أجزاء
    
    Args:
        items: القائمة المراد تقسيمها
        chunk_size: حجم كل جزء
    
    Returns:
        List[List[Any]]: قائمة الأجزاء
    """
    if chunk_size <= 0:
        return [items]
    
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    تسوية قائمة متداخلة إلى قائمة مسطحة
    
    Args:
        nested_list: القائمة المتداخلة
    
    Returns:
        List[Any]: القائمة المسطحة
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def unique_items(items: List[Any], preserve_order: bool = True) -> List[Any]:
    """
    إزالة المكررات من القائمة
    
    Args:
        items: القائمة المراد تنظيفها
        preserve_order: الحفاظ على الترتيب الأصلي
    
    Returns:
        List[Any]: القائمة بدون مكررات
    """
    if preserve_order:
        seen = set()
        return [x for x in items if not (x in seen or seen.add(x))]
    else:
        return list(set(items))


def merge_dicts(dict1: Dict, dict2: Dict, deep: bool = True) -> Dict:
    """
    دمج قاموسين
    
    Args:
        dict1: القاموس الأول
        dict2: القاموس الثاني
        deep: دمج عميق للمفاتيح المتداخلة
    
    Returns:
        Dict: القاموس المدمج
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def find_in_list(items: List[Dict], key: str, value: Any) -> Optional[Dict]:
    """
    البحث في قائمة من القواميس
    
    Args:
        items: قائمة القواميس
        key: مفتاح البحث
        value: القيمة المطلوبة
    
    Returns:
        Optional[Dict]: العنصر الموجود أو None
    """
    for item in items:
        if item.get(key) == value:
            return item
    return None


def group_by(items: List[Dict], key: str) -> Dict[Any, List[Dict]]:
    """
    تجميع قائمة من القواميس حسب مفتاح
    
    Args:
        items: قائمة القواميس
        key: مفتاح التجميع
    
    Returns:
        Dict[Any, List[Dict]]: القائمة المجمعة
    """
    result = defaultdict(list)
    for item in items:
        result[item.get(key)].append(item)
    return dict(result)


# ============================================================
# 10. دوال المحاولة والتكرار
# ============================================================

def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    زخرفة لإعادة محاولة دالة في حالة الخطأ
    
    Args:
        max_attempts: عدد المحاولات القصوى
        delay: التأخير بين المحاولات
        backoff: مضاعفة التأخير
        exceptions: أنواع الاستثناءات التي تستدعي إعادة المحاولة
        on_retry: دالة تستدعى عند كل محاولة (اختياري)
    
    Returns:
        Callable: الدالة المزينة
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    if on_retry:
                        on_retry(attempt, e, current_delay)
                    else:
                        print_warning(f"محاولة {attempt} فشلت: {e}. إعادة المحاولة خلال {current_delay}ث")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            return None
        
        return wrapper
    return decorator


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    زخرفة لإعادة محاولة دالة غير متزامنة في حالة الخطأ
    
    Args:
        max_attempts: عدد المحاولات القصوى
        delay: التأخير بين المحاولات
        backoff: مضاعفة التأخير
        exceptions: أنواع الاستثناءات التي تستدعي إعادة المحاولة
        on_retry: دالة تستدعى عند كل محاولة (اختياري)
    
    Returns:
        Callable: الدالة المزينة
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    if on_retry:
                        on_retry(attempt, e, current_delay)
                    else:
                        print_warning(f"محاولة {attempt} فشلت: {e}. إعادة المحاولة خلال {current_delay}ث")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            return None
        
        return wrapper
    return decorator


def safe_execute(func: Callable, default: Any = None, *args, **kwargs) -> Any:
    """
    تنفيذ دالة بشكل آمن مع التقاط الاستثناءات
    
    Args:
        func: الدالة المراد تنفيذها
        default: القيمة الافتراضية في حالة الخطأ
        *args, **kwargs: معاملات الدالة
    
    Returns:
        Any: نتيجة الدالة أو القيمة الافتراضية
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error(f"خطأ في تنفيذ {func.__name__}: {e}")
        return default


async def safe_execute_async(func: Callable, default: Any = None, *args, **kwargs) -> Any:
    """
    تنفيذ دالة غير متزامنة بشكل آمن مع التقاط الاستثناءات
    
    Args:
        func: الدالة المراد تنفيذها
        default: القيمة الافتراضية في حالة الخطأ
        *args, **kwargs: معاملات الدالة
    
    Returns:
        Any: نتيجة الدالة أو القيمة الافتراضية
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error(f"خطأ في تنفيذ {func.__name__}: {e}")
        return default


# ============================================================
# 11. دوال مساعدة أخرى
# ============================================================

def get_nested_value(data: Dict, path: str, default: Any = None) -> Any:
    """
    الحصول على قيمة من قاموس متداخل باستخدام مسار مفصول بالنقاط
    
    Args:
        data: القاموس
        path: المسار (مثل "user.profile.name")
        default: القيمة الافتراضية
    
    Returns:
        Any: القيمة أو القيمة الافتراضية
    """
    keys = path.split('.')
    
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return default
        data = data[key]
    
    return data


def set_nested_value(data: Dict, path: str, value: Any) -> Dict:
    """
    تعيين قيمة في قاموس متداخل باستخدام مسار مفصول بالنقاط
    
    Args:
        data: القاموس
        path: المسار (مثل "user.profile.name")
        value: القيمة المراد تعيينها
    
    Returns:
        Dict: القاموس المحدث
    """
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return data


def import_module(module_name: str) -> Optional[Any]:
    """
    استيراد وحدة برمجية ديناميكياً
    
    Args:
        module_name: اسم الوحدة
    
    Returns:
        Optional[Any]: الوحدة المستوردة أو None
    """
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError as e:
        error(f"فشل استيراد الوحدة {module_name}: {e}")
        return None


def get_function_from_module(module_name: str, function_name: str) -> Optional[Callable]:
    """
    الحصول على دالة من وحدة برمجية ديناميكياً
    
    Args:
        module_name: اسم الوحدة
        function_name: اسم الدالة
    
    Returns:
        Optional[Callable]: الدالة أو None
    """
    module = import_module(module_name)
    if module and hasattr(module, function_name):
        return getattr(module, function_name)
    return None


def download_file(url: str, destination: Union[str, Path], timeout: int = 30) -> bool:
    """
    تحميل ملف من الإنترنت
    
    Args:
        url: رابط الملف
        destination: مسار الحفظ
        timeout: مهلة الاتصال
    
    Returns:
        bool: نجاح التحميل
    """
    try:
        import requests
        
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        print_progress_bar(downloaded, total_size, "تحميل: ")
        
        print()
        return True
    except Exception as e:
        error(f"فشل تحميل الملف: {e}")
        return False


def get_ip_address() -> Optional[str]:
    """
    الحصول على عنوان IP العام
    
    Returns:
        Optional[str]: عنوان IP أو None
    """
    try:
        import requests
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except Exception as e:
        error(f"فشل الحصول على IP: {e}")
        return None


def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    إنشاء معرف فريد
    
    Args:
        prefix: بادئة المعرف
        length: طول المعرف
    
    Returns:
        str: المعرف
    """
    import secrets
    import string
    
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def get_current_directory() -> Path:
    """
    الحصول على المسار الحالي للتطبيق
    
    Returns:
        Path: المسار الحالي
    """
    return Path(__file__).parent.parent.parent


def ensure_utf8_environment():
    """
    التأكد من أن البيئة تدعم UTF-8
    """
    if sys.platform == 'win32':
        import sys
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)


# ============================================================
# 12. دوال السجلات والإحصائيات
# ============================================================

def get_logs_summary(
    log_dir: Union[str, Path] = "logs",
    days_back: int = 7
) -> Dict[str, Any]:
    """
    الحصول على ملخص السجلات
    
    Args:
        log_dir: مسار مجلد السجلات
        days_back: عدد الأيام للرجوع
    
    Returns:
        Dict: ملخص السجلات
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return {"error": "مجلد السجلات غير موجود"}
    
    summary = {
        "total_files": 0,
        "total_size": "0 B",
        "files": [],
        "errors": 0,
        "warnings": 0
    }
    
    cutoff_time = time.time() - (days_back * 24 * 60 * 60)
    
    for file_path in log_path.glob("*.log*"):
        if not file_path.is_file():
            continue
        
        summary["total_files"] += 1
        
        file_info = {
            "name": file_path.name,
            "size": get_file_size(file_path),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        summary["files"].append(file_info)
        
        # تحليل الملف للبحث عن أخطاء
        if file_path.suffix == '.log':
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                summary["errors"] += content.count("ERROR")
                summary["warnings"] += content.count("WARNING")
            except:
                pass
    
    # حساب الحجم الكلي
    total_bytes = 0
    for f in log_path.glob("*.log*"):
        if f.is_file():
            total_bytes += f.stat().st_size
    
    summary["total_size"] = format_file_size(total_bytes)
    
    return summary


def format_file_size(size_bytes: int) -> str:
    """تنسيق حجم الملف"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


__all__ = [
    # فحص المكتبات والبيئة
    "check_required_libraries",
    "check_environment",
    
    # تصدير السجلات
    "export_logs_to_zip",
    "export_logs_to_zip_async",
    
    # دوال الملفات والمجلدات
    "ensure_directory",
    "get_file_size",
    "safe_filename",
    "read_json_file",
    "write_json_file",
    "create_backup",
    "get_files_in_directory",
    "cleanup_old_files",
    
    # دوال الوقت والتاريخ
    "format_duration",
    "get_timestamp",
    "get_timestamp_filename",
    "time_function",
    "time_async_function",
    
    # دوال النصوص والتحويلات
    "truncate_text",
    "convert_to_slug",
    "extract_hashtags",
    "extract_mentions",
    "extract_emojis",
    
    # دوال التجزئة والتشفير
    "hash_string",
    "hash_file",
    
    # دوال النظام والبيئة
    "get_system_info",
    "is_admin",
    "get_terminal_size",
    "open_url",
    "is_interactive",
    
    # دوال التقدم والشريط
    "print_progress_bar",
    "print_progress_bar_async",
    "print_spinner",
    
    # دوال القوائم والمجموعات
    "chunk_list",
    "flatten_list",
    "unique_items",
    "merge_dicts",
    "find_in_list",
    "group_by",
    
    # دوال المحاولة والتكرار
    "retry_on_error",
    "retry_async",
    "safe_execute",
    "safe_execute_async",
    
    # دوال مساعدة أخرى
    "get_nested_value",
    "set_nested_value",
    "import_module",
    "get_function_from_module",
    "download_file",
    "get_ip_address",
    "generate_id",
    "get_current_directory",
    "ensure_utf8_environment",
    
    # دوال السجلات والإحصائيات
    "get_logs_summary",
    "format_file_size"
]