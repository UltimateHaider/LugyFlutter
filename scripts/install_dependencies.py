#!/usr/bin/env python3
"""
LugyFlutter - سكربت تثبيت المتطلبات (Dependencies Installer)
يقوم بتثبيت جميع المكتبات المطلوبة لتشغيل LugyFlutter
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional

# إضافة المسار الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.colors import Colors, print_colored, print_success, print_error, print_warning, print_info


# ============================================================
# قائمة المتطلبات
# ============================================================

REQUIREMENTS = {
    "browser_use": "browser-use>=0.1.0",
    "langchain_google_genai": "langchain-google-genai>=1.0.0",
    "google.generativeai": "google-generativeai>=0.3.0",
    "PIL": "pillow>=10.0.0",
    "bs4": "beautifulsoup4>=4.12.0",
    "dotenv": "python-dotenv>=1.0.0",
    "streamlit": "streamlit>=1.28.0",
    "fastapi": "fastapi>=0.104.0",
    "uvicorn": "uvicorn>=0.24.0",
    "pytest": "pytest>=7.4.0",
    "pytest_asyncio": "pytest-asyncio>=0.21.0",
    "pytest_cov": "pytest-cov>=4.1.0",
    "cv2": "opencv-python>=4.8.0",
    "pytesseract": "pytesseract>=0.3.10",
    "playwright": "playwright>=1.40.0",
    "pandas": "pandas>=2.0.0",
    "plotly": "plotly>=5.17.0",
    "typing_extensions": "typing-extensions>=4.7.0",
    "dataclasses_json": "dataclasses-json>=0.5.0",
    "requests": "requests>=2.28.0",
    "psutil": "psutil>=5.9.0"
}

# متطلبات التطوير الإضافية
DEV_REQUIREMENTS = {
    "black": "black>=23.0.0",
    "flake8": "flake8>=6.0.0",
    "mypy": "mypy>=1.0.0",
    "isort": "isort>=5.12.0",
    "pytest_xdist": "pytest-xdist>=3.0.0",
    "pytest_html": "pytest-html>=3.2.0"
}


# ============================================================
# دوال مساعدة
# ============================================================

def print_header():
    """طباعة رأس السكربت"""
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("📦 LugyFlutter - تثبيت المتطلبات", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    print_colored(f"🐍 Python: {sys.version}", Colors.CYAN)
    print_colored(f"💻 النظام: {platform.system()} {platform.release()}", Colors.CYAN)
    print_colored("=" * 70, Colors.LUGY)
    print()


def get_pip_command() -> str:
    """الحصول على أمر pip المناسب"""
    if sys.platform == 'win32':
        return 'pip'
    else:
        return 'pip3'


def run_command(command: List[str], description: str = "") -> Tuple[bool, str]:
    """
    تشغيل أمر في المحطة
    
    Args:
        command: قائمة بأجزاء الأمر
        description: وصف الأمر
    
    Returns:
        Tuple[bool, str]: (نجاح, مخرجات)
    """
    if description:
        print_info(f"▶ {description}...")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout + result.stderr
        
        if result.returncode == 0:
            if description:
                print_success(f"✅ {description} - تم بنجاح")
            return True, output
        else:
            if description:
                print_error(f"❌ {description} - فشل")
            print_error(f"⚠️ رمز الخطأ: {result.returncode}")
            if result.stderr:
                print_error(f"⚠️ التفاصيل: {result.stderr[:500]}")
            return False, output
            
    except Exception as e:
        if description:
            print_error(f"❌ {description} - استثناء: {e}")
        return False, str(e)


def install_package(package: str, upgrade: bool = False) -> bool:
    """
    تثبيت حزمة باستخدام pip
    
    Args:
        package: اسم الحزمة مع الإصدار
        upgrade: تحديث الحزمة
    
    Returns:
        bool: نجاح التثبيت
    """
    pip_cmd = get_pip_command()
    cmd = [pip_cmd, "install"]
    
    if upgrade:
        cmd.append("--upgrade")
    
    cmd.append(package)
    
    # إضافة خيارات إضافية
    if platform.system() == "Windows":
        cmd.append("--no-warn-script-location")
    
    success, _ = run_command(cmd, f"تثبيت {package}")
    return success


def install_requirements(requirements: dict, upgrade: bool = False) -> List[str]:
    """
    تثبيت قائمة من المتطلبات
    
    Args:
        requirements: قاموس المتطلبات
        upgrade: تحديث الحزم
    
    Returns:
        List[str]: قائمة الحزم التي فشل تثبيتها
    """
    failed = []
    total = len(requirements)
    current = 0
    
    for name, package in requirements.items():
        current += 1
        print_colored(f"\n[{current}/{total}]", Colors.CYAN)
        
        if install_package(package, upgrade):
            print_success(f"✅ {name} - تم التثبيت")
        else:
            print_error(f"❌ {name} - فشل التثبيت")
            failed.append(name)
    
    return failed


# ============================================================
# دوال التثبيت الخاصة
# ============================================================

def install_playwright() -> bool:
    """تثبيت Playwright والمتصفحات"""
    print_info("📦 تثبيت Playwright والمتصفحات...")
    
    # تثبيت Playwright
    pip_cmd = get_pip_command()
    success, _ = run_command(
        [pip_cmd, "install", "playwright"],
        "تثبيت Playwright"
    )
    
    if not success:
        print_error("❌ فشل تثبيت Playwright")
        return False
    
    # تثبيت المتصفحات
    try:
        print_info("🌐 تثبيت متصفحات Playwright...")
        subprocess.run(
            [sys.executable, "-m", "playwright", "install"],
            check=True
        )
        print_success("✅ تم تثبيت متصفحات Playwright")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"❌ فشل تثبيت متصفحات Playwright: {e}")
        return False


def install_tesseract() -> bool:
    """تثبيت Tesseract OCR (لـ Windows)"""
    if platform.system() != "Windows":
        return True
    
    print_info("🔍 التحقق من تثبيت Tesseract OCR...")
    
    # التحقق من وجود Tesseract
    try:
        subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            check=False
        )
        print_success("✅ Tesseract OCR مثبت")
        return True
    except FileNotFoundError:
        print_warning("⚠️ Tesseract OCR غير مثبت")
        print_info("💡 يمكنك تحميله من: https://github.com/UB-Mannheim/tesseract/wiki")
        print_info("💡 تأكد من إضافة مسار التثبيت إلى PATH")
        
        response = input("هل تريد متابعة التثبيت بدون Tesseract؟ (y/n): ")
        if response.lower() != 'y':
            return False
        return True


# ============================================================
# الدوال الرئيسية
# ============================================================

def main():
    """الوظيفة الرئيسية"""
    print_header()
    
    # عرض عدد المتطلبات
    print_info(f"📦 عدد المتطلبات الأساسية: {len(REQUIREMENTS)}")
    print_info(f"📦 عدد متطلبات التطوير: {len(DEV_REQUIREMENTS)}")
    print()
    
    # اختيار نوع التثبيت
    print_colored("📌 اختر نوع التثبيت:", Colors.CYAN)
    print_colored("  1. تثبيت المتطلبات الأساسية فقط", Colors.BLUE)
    print_colored("  2. تثبيت المتطلبات الأساسية + التطوير", Colors.BLUE)
    print_colored("  3. تثبيت كل شيء (مع Playwright)", Colors.BLUE)
    print_colored("  4. تحديث جميع المتطلبات", Colors.BLUE)
    print_colored("  5. الخروج", Colors.BLUE)
    print()
    
    choice = input("اختر (1-5): ").strip()
    print()
    
    if choice == "5":
        print_info("👋 مع السلامة!")
        return
    
    upgrade = choice == "4"
    
    # تثبيت المتطلبات
    failed = []
    
    if choice in ["1", "2", "3", "4"]:
        # تثبيت المتطلبات الأساسية
        print_colored("\n📦 تثبيت المتطلبات الأساسية...", Colors.LUGY, bold=True)
        failed = install_requirements(REQUIREMENTS, upgrade)
        
        # تثبيت متطلبات التطوير
        if choice in ["2", "3", "4"]:
            print_colored("\n📦 تثبيت متطلبات التطوير...", Colors.LUGY, bold=True)
            dev_failed = install_requirements(DEV_REQUIREMENTS, upgrade)
            failed.extend(dev_failed)
        
        # تثبيت Playwright
        if choice in ["3", "4"]:
            print_colored("\n🌐 تثبيت Playwright...", Colors.LUGY, bold=True)
            if not install_playwright():
                failed.append("playwright")
        
        # تثبيت Tesseract
        if platform.system() == "Windows" and choice in ["3", "4"]:
            install_tesseract()
    
    # عرض النتائج
    print_colored("\n" + "=" * 70, Colors.LUGY)
    
    if failed:
        print_error(f"❌ فشل تثبيت {len(failed)} حزمة/حزم:")
        for name in failed:
            print_colored(f"   • {name}", Colors.RED)
        print()
        print_info("💡 حاول تثبيتها يدوياً باستخدام:")
        for name, package in REQUIREMENTS.items():
            if name in failed:
                print_info(f"   pip install {package}")
        print()
    else:
        print_success("✅ تم تثبيت جميع المتطلبات بنجاح!")
    
    # عرض معلومات إضافية
    print()
    print_info("📌 للتحقق من التثبيت:")
    print_colored("   python -c \"import browser_use; print('✅ browser_use مثبت')\"", Colors.BLUE)
    print_colored("   python -c \"import langchain_google_genai; print('✅ langchain_google_genai مثبت')\"", Colors.BLUE)
    print()
    
    print_info("📌 لتشغيل LugyFlutter:")
    print_colored("   python main.py", Colors.BLUE)
    print()
    
    print_info("📌 لتشغيل لوحة التحكم:")
    print_colored("   streamlit run src/web/dashboard.py", Colors.BLUE)
    print()
    
    print_info("📌 لتشغيل الاختبارات:")
    print_colored("   pytest src/tests -v", Colors.BLUE)
    
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🌟 LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    print()


# ============================================================
# دوال مساعدة للتشغيل من سطر الأوامر
# ============================================================

def install_all():
    """تثبيت جميع المتطلبات"""
    print_info("📦 تثبيت جميع المتطلبات...")
    
    # تثبيت المتطلبات الأساسية
    failed = install_requirements(REQUIREMENTS)
    
    # تثبيت متطلبات التطوير
    dev_failed = install_requirements(DEV_REQUIREMENTS)
    failed.extend(dev_failed)
    
    # تثبيت Playwright
    if not install_playwright():
        failed.append("playwright")
    
    if failed:
        print_error(f"❌ فشل تثبيت {len(failed)} حزمة")
        return False
    else:
        print_success("✅ تم تثبيت جميع المتطلبات بنجاح!")
        return True


def install_minimal():
    """تثبيت المتطلبات الأساسية فقط"""
    print_info("📦 تثبيت المتطلبات الأساسية...")
    
    failed = install_requirements(REQUIREMENTS)
    
    if failed:
        print_error(f"❌ فشل تثبيت {len(failed)} حزمة")
        return False
    else:
        print_success("✅ تم تثبيت المتطلبات الأساسية بنجاح!")
        return True


def upgrade_all():
    """تحديث جميع المتطلبات"""
    print_info("🔄 تحديث جميع المتطلبات...")
    
    # تحديث pip
    pip_cmd = get_pip_command()
    run_command([pip_cmd, "install", "--upgrade", "pip"], "تحديث pip")
    
    # تحديث المتطلبات
    failed = install_requirements(REQUIREMENTS, upgrade=True)
    dev_failed = install_requirements(DEV_REQUIREMENTS, upgrade=True)
    failed.extend(dev_failed)
    
    if failed:
        print_warning(f"⚠️ فشل تحديث {len(failed)} حزمة")
        return False
    else:
        print_success("✅ تم تحديث جميع المتطلبات بنجاح!")
        return True


# ============================================================
# نقاط الدخول
# ============================================================

if __name__ == "__main__":
    # دعم أوامر سطر الأوامر
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "all":
            install_all()
        elif command == "minimal":
            install_minimal()
        elif command == "upgrade":
            upgrade_all()
        elif command == "help":
            print("الأوامر المتاحة:")
            print("  python install_dependencies.py        - تشغيل الواجهة التفاعلية")
            print("  python install_dependencies.py all    - تثبيت جميع المتطلبات")
            print("  python install_dependencies.py minimal - تثبيت المتطلبات الأساسية")
            print("  python install_dependencies.py upgrade - تحديث جميع المتطلبات")
        else:
            print(f"⚠️ أمر غير معروف: {command}")
            print("استخدم 'help' لعرض الأوامر المتاحة")
    else:
        main()