#!/usr/bin/env python3
"""
LugyFlutter - سكربت تشغيل لوحة التحكم (Run Dashboard)
يقوم بتشغيل لوحة التحكم التفاعلية باستخدام Streamlit
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

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8501
DEFAULT_BROWSER_OPEN = True


# ============================================================
# دوال مساعدة
# ============================================================

def print_header():
    """طباعة رأس السكربت"""
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🖥️ LugyFlutter - لوحة التحكم", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    print_colored(f"📌 الإصدار: 2.0.0", Colors.CYAN)
    print_colored(f"🌐 المنفذ: {DEFAULT_PORT}", Colors.CYAN)
    print_colored("=" * 70, Colors.LUGY)
    print()


def check_streamlit() -> bool:
    """التحقق من تثبيت Streamlit"""
    try:
        import streamlit
        print_success(f"✅ Streamlit مثبت (الإصدار: {streamlit.__version__})")
        return True
    except ImportError:
        print_error("❌ Streamlit غير مثبت")
        print_info("💡 قم بتثبيته باستخدام:")
        print_colored("   pip install streamlit", Colors.BLUE)
        print_colored("   python install_dependencies.py", Colors.BLUE)
        return False


def get_dashboard_path() -> Optional[Path]:
    """الحصول على مسار ملف لوحة التحكم"""
    # المسار النسبي
    dashboard_path = Path(__file__).parent.parent / "src" / "web" / "dashboard.py"
    
    if dashboard_path.exists():
        return dashboard_path
    
    # محاولة مسارات أخرى
    alt_paths = [
        Path("src/web/dashboard.py"),
        Path("../src/web/dashboard.py"),
        Path("../../src/web/dashboard.py"),
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


def run_streamlit(dashboard_path: Path, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, open_browser_flag: bool = DEFAULT_BROWSER_OPEN):
    """
    تشغيل Streamlit
    
    Args:
        dashboard_path: مسار ملف لوحة التحكم
        host: اسم المضيف
        port: رقم المنفذ
        open_browser_flag: فتح المتصفح تلقائياً
    """
    url = f"http://{host}:{port}"
    
    print_info(f"🚀 جاري تشغيل لوحة التحكم على: {url}")
    print_info(f"📁 المسار: {dashboard_path}")
    print()
    
    # فتح المتصفح في خلفية
    if open_browser_flag:
        open_browser(url)
    
    # إعداد أمر Streamlit
    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(dashboard_path),
        "--server.address", host,
        "--server.port", str(port),
        "--server.headless", "true" if config.BROWSER_HEADLESS else "false",
        "--browser.gatherUsageStats", "false",
        "--logger.level", "info",
        "--theme.base", "dark",
        "--theme.primaryColor", "#6200EE",
        "--theme.backgroundColor", "#1A1A2E",
        "--theme.secondaryBackgroundColor", "#1E1E2E",
        "--theme.textColor", "#FFFFFF"
    ]
    
    try:
        # تشغيل Streamlit
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print()
        print_info("👋 تم إيقاف لوحة التحكم بواسطة المستخدم")
    except subprocess.CalledProcessError as e:
        print_error(f"❌ فشل تشغيل Streamlit: {e}")
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
    
    # فتح المتصفح
    open_input = input("فتح المتصفح تلقائياً؟ (y/n, افتراضي: y): ").strip().lower()
    open_browser_flag = open_input != 'n'
    
    return host, port, open_browser_flag


def run_dashboard():
    """الوظيفة الرئيسية لتشغيل لوحة التحكم"""
    print_header()
    
    # التحقق من Streamlit
    if not check_streamlit():
        return
    
    # الحصول على مسار لوحة التحكم
    dashboard_path = get_dashboard_path()
    
    if not dashboard_path:
        print_error("❌ لم يتم العثور على ملف لوحة التحكم")
        print_info("💡 تأكد من وجود الملف في: src/web/dashboard.py")
        return
    
    print_success(f"✅ تم العثور على لوحة التحكم: {dashboard_path}")
    print()
    
    # اختيار طريقة التشغيل
    print_colored("📌 اختر طريقة التشغيل:", Colors.CYAN)
    print_colored("  1. تشغيل عادي (مع فتح المتصفح)", Colors.BLUE)
    print_colored("  2. تشغيل بدون فتح المتصفح", Colors.BLUE)
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
        print_info("📖 معلومات المساعدة:")
        print_colored("   🌐 لوحة التحكم تعمل على: http://localhost:8501", Colors.CYAN)
        print_colored("   📁 مسار الملف: src/web/dashboard.py", Colors.CYAN)
        print_colored("   ⚙️ يمكن تغيير المنفذ في ملف .env", Colors.CYAN)
        print_colored("   🎨 يمكن تخصيص المظهر في إعدادات Streamlit", Colors.CYAN)
        return
    
    if choice == "3":
        host, port, open_browser_flag = run_with_custom_settings()
    elif choice == "2":
        host, port, open_browser_flag = DEFAULT_HOST, DEFAULT_PORT, False
    else:
        host, port, open_browser_flag = DEFAULT_HOST, DEFAULT_PORT, True
    
    # تشغيل لوحة التحكم
    run_streamlit(dashboard_path, host, port, open_browser_flag)


# ============================================================
# دوال مساعدة للتشغيل من سطر الأوامر
# ============================================================

def run_dashboard_headless():
    """تشغيل لوحة التحكم بدون واجهة (للخوادم)"""
    dashboard_path = get_dashboard_path()
    if not dashboard_path:
        print_error("❌ لم يتم العثور على ملف لوحة التحكم")
        return
    
    print_info("🚀 تشغيل لوحة التحكم في وضع بدون واجهة...")
    run_streamlit(dashboard_path, "0.0.0.0", DEFAULT_PORT, False)


def run_dashboard_custom(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, open_browser: bool = DEFAULT_BROWSER_OPEN):
    """تشغيل لوحة التحكم بإعدادات مخصصة"""
    dashboard_path = get_dashboard_path()
    if not dashboard_path:
        print_error("❌ لم يتم العثور على ملف لوحة التحكم")
        return
    
    run_streamlit(dashboard_path, host, port, open_browser)


def show_dashboard_info():
    """عرض معلومات لوحة التحكم"""
    dashboard_path = get_dashboard_path()
    
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🖥️ معلومات لوحة تحكم LugyFlutter", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    
    if dashboard_path:
        print_success(f"✅ المسار: {dashboard_path}")
        print_info(f"📦 الحجم: {dashboard_path.stat().st_size:,} bytes")
        print_info(f"🔄 آخر تعديل: {time.ctime(dashboard_path.stat().st_mtime)}")
    else:
        print_error("❌ لم يتم العثور على ملف لوحة التحكم")
    
    print()
    print_info("📌 الروابط:")
    print_colored(f"   🌐 http://localhost:{DEFAULT_PORT}", Colors.BLUE)
    print_colored(f"   📖 وثائق Streamlit: https://docs.streamlit.io", Colors.BLUE)
    print()
    
    print_info("📌 الأوامر المتاحة:")
    print_colored("   python run_dashboard.py          - تشغيل الواجهة التفاعلية", Colors.BLUE)
    print_colored("   python run_dashboard.py headless - تشغيل بدون واجهة (للسيرفرات)", Colors.BLUE)
    print_colored("   python run_dashboard.py info     - عرض معلومات", Colors.BLUE)
    print_colored("   python run_dashboard.py --port 8501 --host 0.0.0.0 - إعدادات مخصصة", Colors.BLUE)
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
            run_dashboard_headless()
        elif command == "info":
            show_dashboard_info()
        elif command == "help" or command == "--help" or command == "-h":
            show_dashboard_info()
        elif command == "--port" and len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
                host = DEFAULT_HOST
                open_browser = True
                
                # التحقق من وجود host
                if len(sys.argv) > 3 and sys.argv[3] != "--no-browser":
                    host = sys.argv[3]
                
                # التحقق من عدم فتح المتصفح
                if "--no-browser" in sys.argv:
                    open_browser = False
                
                run_dashboard_custom(host, port, open_browser)
            except ValueError:
                print_error("❌ المنفذ يجب أن يكون رقماً")
        else:
            print_warning(f"⚠️ أمر غير معروف: {command}")
            show_dashboard_info()
    else:
        run_dashboard()