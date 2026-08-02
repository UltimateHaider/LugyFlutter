#!/usr/bin/env python3
"""
LugyFlutter - سكربت تشغيل واجهة API (Run API)
يقوم بتشغيل واجهة API باستخدام FastAPI و Uvicorn
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path
from typing import Optional

# إضافة المسار الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.colors import Colors, print_colored, print_success, print_error, print_warning, print_info
from src.core.config import config


# ============================================================
# الإعدادات
# ============================================================

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_RELOAD = True
DEFAULT_LOG_LEVEL = "info"
DEFAULT_OPEN_BROWSER = False
DEFAULT_OPEN_DOCS = True


# ============================================================
# دوال مساعدة
# ============================================================

def print_header():
    """طباعة رأس السكربت"""
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🌐 LugyFlutter - واجهة API", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    print_colored(f"📌 الإصدار: 2.0.0", Colors.CYAN)
    print_colored(f"🌐 المنفذ: {DEFAULT_PORT}", Colors.CYAN)
    print_colored("=" * 70, Colors.LUGY)
    print()


def check_uvicorn() -> bool:
    """التحقق من تثبيت Uvicorn"""
    try:
        import uvicorn
        print_success(f"✅ Uvicorn مثبت (الإصدار: {uvicorn.__version__})")
        return True
    except ImportError:
        print_error("❌ Uvicorn غير مثبت")
        print_info("💡 قم بتثبيته باستخدام:")
        print_colored("   pip install uvicorn", Colors.BLUE)
        print_colored("   python install_dependencies.py", Colors.BLUE)
        return False


def get_api_path() -> Optional[Path]:
    """الحصول على مسار ملف API"""
    # المسار النسبي
    api_path = Path(__file__).parent.parent / "src" / "web" / "api.py"
    
    if api_path.exists():
        return api_path
    
    # محاولة مسارات أخرى
    alt_paths = [
        Path("src/web/api.py"),
        Path("../src/web/api.py"),
        Path("../../src/web/api.py"),
    ]
    
    for path in alt_paths:
        if path.exists():
            return path
    
    return None


def open_browser(url: str, delay: float = 2.0):
    """فتح المتصفح بعد تأخير"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print_info(f"🌐 تم فتح المتصفح: {url}")
        except Exception as e:
            print_warning(f"⚠️ فشل فتح المتصفح: {e}")
            print_info(f"💡 افتح الرابط يدوياً: {url}")
    
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def run_uvicorn(api_path: Path, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = DEFAULT_RELOAD, log_level: str = DEFAULT_LOG_LEVEL):
    """
    تشغيل Uvicorn
    
    Args:
        api_path: مسار ملف API
        host: اسم المضيف
        port: رقم المنفذ
        reload: إعادة التحميل التلقائي
        log_level: مستوى التسجيل
    """
    url = f"http://{host}:{port}"
    docs_url = f"{url}/docs"
    redoc_url = f"{url}/redoc"
    
    print_info(f"🚀 جاري تشغيل واجهة API على: {url}")
    print_info(f"📁 المسار: {api_path}")
    print_info(f"📖 التوثيق: {docs_url}")
    print_info(f"📚 ReDoc: {redoc_url}")
    print()
    
    # فتح التوثيق في المتصفح
    if DEFAULT_OPEN_DOCS:
        open_browser(docs_url)
    
    # إعداد أمر Uvicorn
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "src.web.api:app",
        "--host", host,
        "--port", str(port),
        "--log-level", log_level
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        # تشغيل Uvicorn
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print()
        print_info("👋 تم إيقاف واجهة API بواسطة المستخدم")
    except subprocess.CalledProcessError as e:
        print_error(f"❌ فشل تشغيل Uvicorn: {e}")
    except Exception as e:
        print_error(f"❌ خطأ غير متوقع: {e}")


def run_with_custom_settings():
    """تشغيل مع إعدادات مخصصة"""
    print_info("🔧 إعدادات مخصصة")
    
    # المنفذ
    port_input = input(f"أدخل رقم المنفذ (افتراضي: {DEFAULT_PORT}): ").strip()
    port = int(port_input) if port_input.isdigit() else DEFAULT_PORT
    
    # المضيف
    host_input = input(f"أدخل اسم المضيف (افتراضي: {DEFAULT_HOST}): ").strip()
    host = host_input if host_input else DEFAULT_HOST
    
    # إعادة التحميل
    reload_input = input("تفعيل إعادة التحميل التلقائي؟ (y/n, افتراضي: y): ").strip().lower()
    reload = reload_input != 'n'
    
    # مستوى التسجيل
    print_colored("\n📌 اختر مستوى التسجيل:", Colors.CYAN)
    print_colored("  1. debug", Colors.BLUE)
    print_colored("  2. info", Colors.BLUE)
    print_colored("  3. warning", Colors.BLUE)
    print_colored("  4. error", Colors.BLUE)
    
    log_choice = input("\nاختر (1-4, افتراضي: 2): ").strip()
    
    log_levels = {
        "1": "debug",
        "2": "info",
        "3": "warning",
        "4": "error"
    }
    log_level = log_levels.get(log_choice, "info")
    
    return host, port, reload, log_level


def run_api():
    """الوظيفة الرئيسية لتشغيل واجهة API"""
    print_header()
    
    # التحقق من Uvicorn
    if not check_uvicorn():
        return
    
    # الحصول على مسار API
    api_path = get_api_path()
    
    if not api_path:
        print_error("❌ لم يتم العثور على ملف API")
        print_info("💡 تأكد من وجود الملف في: src/web/api.py")
        return
    
    print_success(f"✅ تم العثور على ملف API: {api_path}")
    print()
    
    # اختيار طريقة التشغيل
    print_colored("📌 اختر طريقة التشغيل:", Colors.CYAN)
    print_colored("  1. تشغيل عادي (مع إعادة تحميل تلقائي)", Colors.BLUE)
    print_colored("  2. تشغيل بدون إعادة تحميل (للسيرفرات)", Colors.BLUE)
    print_colored("  3. تشغيل مع إعدادات مخصصة", Colors.BLUE)
    print_colored("  4. عرض معلومات المساعدة", Colors.BLUE)
    print_colored("  5. الخروج", Colors.BLUE)
    print()
    
    choice = input("اختر (1-5): ").strip()
    print()
    
    if choice == "5":
        print_info("👋 مع السلامة!")
        return
    
    if choice == "4":
        show_api_info()
        return
    
    if choice == "3":
        host, port, reload, log_level = run_with_custom_settings()
    elif choice == "2":
        host, port, reload, log_level = DEFAULT_HOST, DEFAULT_PORT, False, DEFAULT_LOG_LEVEL
    else:
        host, port, reload, log_level = DEFAULT_HOST, DEFAULT_PORT, True, DEFAULT_LOG_LEVEL
    
    # تشغيل واجهة API
    run_uvicorn(api_path, host, port, reload, log_level)


# ============================================================
# دوال مساعدة للتشغيل من سطر الأوامر
# ============================================================

def run_api_headless():
    """تشغيل واجهة API بدون واجهة (للخوادم)"""
    api_path = get_api_path()
    if not api_path:
        print_error("❌ لم يتم العثور على ملف API")
        return
    
    print_info("🚀 تشغيل واجهة API في وضع بدون واجهة...")
    run_uvicorn(api_path, "0.0.0.0", DEFAULT_PORT, False, "warning")


def run_api_production():
    """تشغيل واجهة API للإنتاج"""
    api_path = get_api_path()
    if not api_path:
        print_error("❌ لم يتم العثور على ملف API")
        return
    
    print_info("🚀 تشغيل واجهة API للإنتاج...")
    print_warning("⚠️ تأكد من تعيين متغيرات البيئة المناسبة للإنتاج")
    run_uvicorn(api_path, "0.0.0.0", DEFAULT_PORT, False, "warning")


def run_api_custom(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = DEFAULT_RELOAD, log_level: str = DEFAULT_LOG_LEVEL):
    """تشغيل واجهة API بإعدادات مخصصة"""
    api_path = get_api_path()
    if not api_path:
        print_error("❌ لم يتم العثور على ملف API")
        return
    
    run_uvicorn(api_path, host, port, reload, log_level)


def show_api_info():
    """عرض معلومات واجهة API"""
    api_path = get_api_path()
    
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🌐 معلومات واجهة API - LugyFlutter", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    
    if api_path:
        print_success(f"✅ المسار: {api_path}")
        print_info(f"📦 الحجم: {api_path.stat().st_size:,} bytes")
        print_info(f"🔄 آخر تعديل: {time.ctime(api_path.stat().st_mtime)}")
    else:
        print_error("❌ لم يتم العثور على ملف API")
    
    print()
    print_info("📌 الروابط:")
    print_colored(f"   🌐 http://localhost:{DEFAULT_PORT}", Colors.BLUE)
    print_colored(f"   📖 توثيق Swagger: http://localhost:{DEFAULT_PORT}/docs", Colors.BLUE)
    print_colored(f"   📚 توثيق ReDoc: http://localhost:{DEFAULT_PORT}/redoc", Colors.BLUE)
    print_colored(f"   💚 فحص الصحة: http://localhost:{DEFAULT_PORT}/health", Colors.BLUE)
    print_colored(f"   📊 الحالة: http://localhost:{DEFAULT_PORT}/status", Colors.BLUE)
    print()
    
    print_info("📌 نقاط النهاية المتاحة:")
    print_colored("   GET  /                    - الصفحة الرئيسية", Colors.BLUE)
    print_colored("   GET  /health              - فحص الصحة", Colors.BLUE)
    print_colored("   GET  /status              - حالة الوكيل", Colors.BLUE)
    print_colored("   POST /task/execute        - تنفيذ مهمة", Colors.BLUE)
    print_colored("   GET  /task/{task_id}      - حالة مهمة", Colors.BLUE)
    print_colored("   POST /project/create      - إنشاء مشروع", Colors.BLUE)
    print_colored("   POST /project/clone       - نسخ مشروع", Colors.BLUE)
    print_colored("   GET  /checkpoints         - قائمة نقاط التفتيش", Colors.BLUE)
    print_colored("   POST /checkpoints         - إنشاء نقطة تفتيش", Colors.BLUE)
    print_colored("   POST /checkpoints/undo    - التراجع", Colors.BLUE)
    print_colored("   POST /checkpoints/redo    - إعادة", Colors.BLUE)
    print_colored("   GET  /screenshot          - لقطة شاشة", Colors.BLUE)
    print_colored("   POST /export/logs         - تصدير السجلات", Colors.BLUE)
    print_colored("   POST /agent/restart       - إعادة تشغيل الوكيل", Colors.BLUE)
    print()
    
    print_info("📌 الأوامر المتاحة:")
    print_colored("   python run_api.py              - تشغيل الواجهة التفاعلية", Colors.BLUE)
    print_colored("   python run_api.py headless     - تشغيل بدون واجهة (للسيرفرات)", Colors.BLUE)
    print_colored("   python run_api.py production   - تشغيل للإنتاج", Colors.BLUE)
    print_colored("   python run_api.py info         - عرض معلومات", Colors.BLUE)
    print_colored("   python run_api.py --port 8000 --host 0.0.0.0 - إعدادات مخصصة", Colors.BLUE)
    print()
    
    print_info("📌 أمثلة استخدام API:")
    print_colored("   curl http://localhost:8000/health", Colors.CYAN)
    print_colored('   curl -X POST http://localhost:8000/task/execute -H "Content-Type: application/json" -d \'{"user_input": "أنشئ مشروع جديد"}\'', Colors.CYAN)
    print()
    
    print_colored("=" * 70, Colors.LUGY)


# ============================================================
# نقاط الدخول
# ============================================================

if __name__ == "__main__":
    # دعم أوامر سطر الأوامر
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "headless":
            run_api_headless()
        elif command == "production":
            run_api_production()
        elif command == "info":
            show_api_info()
        elif command == "help" or command == "--help" or command == "-h":
            show_api_info()
        elif command == "--port" and len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
                host = DEFAULT_HOST
                reload = DEFAULT_RELOAD
                log_level = DEFAULT_LOG_LEVEL
                
                # التحقق من وجود host
                if len(sys.argv) > 3:
                    # التحقق من معلمات إضافية
                    for i, arg in enumerate(sys.argv[3:], start=3):
                        if arg == "--no-reload":
                            reload = False
                        elif arg == "--debug":
                            log_level = "debug"
                        elif arg == "--quiet":
                            log_level = "warning"
                        elif not arg.startswith("--"):
                            host = arg
                
                run_api_custom(host, port, reload, log_level)
            except ValueError:
                print_error("❌ المنفذ يجب أن يكون رقماً")
        else:
            print_warning(f"⚠️ أمر غير معروف: {command}")
            show_api_info()
    else:
        run_api()