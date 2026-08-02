#!/usr/bin/env python3
"""
LugyFlutter - سكربت تشغيل الاختبارات (Run Tests)
يقوم بتشغيل جميع اختبارات LugyFlutter وعرض النتائج
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

# إضافة المسار الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.colors import Colors, print_colored, print_success, print_error, print_warning, print_info


# ============================================================
# الإعدادات
# ============================================================

DEFAULT_TEST_PATH = "src/tests"
DEFAULT_VERBOSITY = 2
DEFAULT_TIMEOUT = 300
DEFAULT_COVERAGE = True
DEFAULT_COVERAGE_THRESHOLD = 70


# ============================================================
# دوال مساعدة
# ============================================================

def print_header():
    """طباعة رأس السكربت"""
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🧪 LugyFlutter - تشغيل الاختبارات", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    print_colored(f"📌 الإصدار: 2.0.0", Colors.CYAN)
    print_colored(f"📁 مسار الاختبارات: {DEFAULT_TEST_PATH}", Colors.CYAN)
    print_colored(f"📊 تغطية الكود: {'مفعلة' if DEFAULT_COVERAGE else 'معطلة'}", Colors.CYAN)
    print_colored("=" * 70, Colors.LUGY)
    print()


def check_pytest() -> bool:
    """التحقق من تثبيت pytest"""
    try:
        import pytest
        print_success(f"✅ pytest مثبت (الإصدار: {pytest.__version__})")
        return True
    except ImportError:
        print_error("❌ pytest غير مثبت")
        print_info("💡 قم بتثبيته باستخدام:")
        print_colored("   pip install pytest pytest-asyncio pytest-cov", Colors.BLUE)
        print_colored("   python install_dependencies.py", Colors.BLUE)
        return False


def get_tests_path() -> Optional[Path]:
    """الحصول على مسار مجلد الاختبارات"""
    # المسار النسبي
    tests_path = Path(__file__).parent.parent / DEFAULT_TEST_PATH
    
    if tests_path.exists():
        return tests_path
    
    # محاولة مسارات أخرى
    alt_paths = [
        Path(DEFAULT_TEST_PATH),
        Path("../" + DEFAULT_TEST_PATH),
        Path("../../" + DEFAULT_TEST_PATH),
    ]
    
    for path in alt_paths:
        if path.exists():
            return path
    
    return None


def run_pytest(
    tests_path: Path,
    verbosity: int = DEFAULT_VERBOSITY,
    timeout: int = DEFAULT_TIMEOUT,
    coverage: bool = DEFAULT_COVERAGE,
    coverage_threshold: int = DEFAULT_COVERAGE_THRESHOLD,
    specific_test: Optional[str] = None
) -> Tuple[bool, str]:
    """
    تشغيل pytest
    
    Args:
        tests_path: مسار مجلد الاختبارات
        verbosity: مستوى التفصيل
        timeout: مهلة التشغيل بالثواني
        coverage: تفعيل تغطية الكود
        coverage_threshold: الحد الأدنى للتغطية
        specific_test: اختبار محدد للتشغيل
    
    Returns:
        Tuple[bool, str]: (نجاح, مخرجات)
    """
    # إعداد أمر pytest
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_path),
        "-v" * min(verbosity, 3),  # -v, -vv, -vvv
        "--tb=short",
        "--color=yes",
        "--maxfail=5",
        f"--timeout={timeout}"
    ]
    
    # إضافة اختبار محدد إذا تم تحديده
    if specific_test:
        cmd.append(specific_test)
    
    # إضافة تغطية الكود
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            f"--cov-fail-under={coverage_threshold}"
        ])
    
    # إضافة خيارات إضافية
    if sys.platform == "win32":
        cmd.append("--no-cov-on-fail")
    
    print_info(f"📝 الأمر: {' '.join(cmd)}")
    print()
    
    start_time = time.time()
    
    try:
        # تشغيل pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 10
        )
        
        elapsed = time.time() - start_time
        
        # عرض المخرجات
        print_colored("\n" + "=" * 70, Colors.LUGY)
        
        if result.stdout:
            print_colored("📤 مخرجات الاختبارات:", Colors.CYAN)
            print(result.stdout)
        
        if result.stderr:
            print_colored("⚠️ أخطاء:", Colors.YELLOW)
            print(result.stderr)
        
        print_colored("=" * 70, Colors.LUGY)
        print()
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        # عرض النتيجة
        if success:
            print_success(f"✅ جميع الاختبارات نجحت! (الوقت: {elapsed:.2f} ثانية)")
        else:
            print_error(f"❌ فشلت بعض الاختبارات (رمز الخروج: {result.returncode})")
            print_info(f"⏱️ الوقت المستغرق: {elapsed:.2f} ثانية")
        
        return success, output
        
    except subprocess.TimeoutExpired:
        print_error(f"❌ انتهت مهلة تشغيل الاختبارات ({timeout} ثانية)")
        return False, "Timeout"
    except Exception as e:
        print_error(f"❌ خطأ في تشغيل الاختبارات: {e}")
        return False, str(e)


def run_specific_test(tests_path: Path, test_name: str):
    """تشغيل اختبار محدد"""
    print_info(f"🧪 جاري تشغيل الاختبار: {test_name}")
    print()
    
    success, _ = run_pytest(tests_path, specific_test=test_name)
    
    if success:
        print_success(f"✅ الاختبار {test_name} نجح!")
    else:
        print_error(f"❌ الاختبار {test_name} فشل!")


def get_available_tests(tests_path: Path) -> List[str]:
    """الحصول على قائمة الاختبارات المتاحة"""
    test_files = []
    
    for pattern in ["test_*.py", "*_test.py"]:
        for file_path in tests_path.glob(pattern):
            test_files.append(file_path.stem)
    
    return sorted(test_files)


# ============================================================
# دوال الاختبارات المختلفة
# ============================================================

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    tests_path = get_tests_path()
    if not tests_path:
        print_error("❌ لم يتم العثور على مجلد الاختبارات")
        return
    
    print_info("🧪 تشغيل جميع الاختبارات...")
    print()
    
    success, _ = run_pytest(tests_path)
    
    if success:
        print_success("🎉 جميع الاختبارات نجحت!")
    else:
        print_error("❌ بعض الاختبارات فشلت!")


def run_tests_with_coverage():
    """تشغيل الاختبارات مع تغطية الكود"""
    tests_path = get_tests_path()
    if not tests_path:
        print_error("❌ لم يتم العثور على مجلد الاختبارات")
        return
    
    print_info("🧪 تشغيل الاختبارات مع تغطية الكود...")
    print()
    
    success, _ = run_pytest(tests_path, coverage=True)
    
    if success:
        print_success("🎉 جميع الاختبارات نجحت مع تغطية كاملة!")
        print_info("📊 تقرير التغطية موجود في: htmlcov/index.html")
    else:
        print_error("❌ بعض الاختبارات فشلت أو التغطية أقل من الحد المطلوب!")


def run_quick_tests():
    """تشغيل اختبارات سريعة (بدون تغطية)"""
    tests_path = get_tests_path()
    if not tests_path:
        print_error("❌ لم يتم العثور على مجلد الاختبارات")
        return
    
    print_info("⚡ تشغيل اختبارات سريعة...")
    print()
    
    success, _ = run_pytest(tests_path, coverage=False, verbosity=1)
    
    if success:
        print_success("🎉 جميع الاختبارات السريعة نجحت!")
    else:
        print_error("❌ بعض الاختبارات السريعة فشلت!")


def run_failed_tests():
    """تشغيل الاختبارات الفاشلة فقط"""
    tests_path = get_tests_path()
    if not tests_path:
        print_error("❌ لم يتم العثور على مجلد الاختبارات")
        return
    
    # تشغيل الاختبارات الفاشلة من الجلسة السابقة
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_path),
        "--lf",  # last failed
        "--tb=short",
        "--color=yes",
        "-v"
    ]
    
    print_info("🔁 تشغيل الاختبارات الفاشلة فقط...")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print_success("✅ جميع الاختبارات الفاشلة نجحت هذه المرة!")
        else:
            print_error("❌ لا تزال بعض الاختبارات فاشلة!")
            
    except Exception as e:
        print_error(f"❌ خطأ في تشغيل الاختبارات الفاشلة: {e}")


# ============================================================
# الواجهة الرئيسية
# ============================================================

def run_tests():
    """الوظيفة الرئيسية لتشغيل الاختبارات"""
    print_header()
    
    # التحقق من pytest
    if not check_pytest():
        return
    
    # الحصول على مسار الاختبارات
    tests_path = get_tests_path()
    
    if not tests_path:
        print_error("❌ لم يتم العثور على مجلد الاختبارات")
        print_info("💡 تأكد من وجود المجلد في: src/tests/")
        return
    
    print_success(f"✅ تم العثور على مجلد الاختبارات: {tests_path}")
    print()
    
    # الحصول على قائمة الاختبارات المتاحة
    available_tests = get_available_tests(tests_path)
    
    # اختيار طريقة التشغيل
    print_colored("📌 اختر طريقة التشغيل:", Colors.CYAN)
    print_colored("  1. تشغيل جميع الاختبارات", Colors.BLUE)
    print_colored("  2. تشغيل جميع الاختبارات مع تغطية الكود", Colors.BLUE)
    print_colored("  3. تشغيل اختبارات سريعة (بدون تغطية)", Colors.BLUE)
    print_colored("  4. تشغيل اختبارات فاشلة فقط", Colors.BLUE)
    
    if available_tests:
        print_colored("  5. تشغيل اختبار محدد", Colors.BLUE)
    
    print_colored("  6. عرض معلومات المساعدة", Colors.BLUE)
    print_colored("  7. الخروج", Colors.BLUE)
    print()
    
    choice = input("اختر (1-7): ").strip()
    print()
    
    if choice == "7":
        print_info("👋 مع السلامة!")
        return
    
    if choice == "6":
        show_tests_info(tests_path, available_tests)
        return
    
    if choice == "5" and available_tests:
        # عرض قائمة الاختبارات المتاحة
        print_colored("📋 الاختبارات المتاحة:", Colors.CYAN)
        for i, test in enumerate(available_tests, 1):
            print_colored(f"  {i}. {test}", Colors.BLUE)
        print()
        
        test_choice = input("اختر رقم الاختبار: ").strip()
        
        try:
            idx = int(test_choice) - 1
            if 0 <= idx < len(available_tests):
                run_specific_test(tests_path, available_tests[idx])
            else:
                print_error("❌ رقم غير صحيح")
        except ValueError:
            print_error("❌ الرجاء إدخال رقم صحيح")
        
        return
    
    if choice == "4":
        run_failed_tests()
        return
    
    if choice == "3":
        run_quick_tests()
        return
    
    if choice == "2":
        run_tests_with_coverage()
        return
    
    if choice == "1":
        run_all_tests()
        return
    
    print_error("❌ اختيار غير صحيح")


def show_tests_info(tests_path: Path, available_tests: List[str]):
    """عرض معلومات الاختبارات"""
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("🧪 معلومات اختبارات LugyFlutter", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    
    print_success(f"✅ مسار الاختبارات: {tests_path}")
    print()
    
    print_info("📋 قائمة ملفات الاختبارات:")
    for test in available_tests:
        print_colored(f"   • {test}", Colors.BLUE)
    print()
    
    print_info("📌 الأوامر المتاحة:")
    print_colored("   python run_tests.py              - تشغيل الواجهة التفاعلية", Colors.BLUE)
    print_colored("   python run_tests.py all          - تشغيل جميع الاختبارات", Colors.BLUE)
    print_colored("   python run_tests.py coverage     - تشغيل مع تغطية الكود", Colors.BLUE)
    print_colored("   python run_tests.py quick        - تشغيل اختبارات سريعة", Colors.BLUE)
    print_colored("   python run_tests.py failed       - تشغيل الاختبارات الفاشلة", Colors.BLUE)
    print_colored("   python run_tests.py test_name    - تشغيل اختبار محدد", Colors.BLUE)
    print_colored("   python run_tests.py info         - عرض معلومات", Colors.BLUE)
    print()
    
    print_info("📊 خيارات إضافية:")
    print_colored("   --no-cov      - تعطيل تغطية الكود", Colors.BLUE)
    print_colored("   --verbose     - عرض تفصيلي", Colors.BLUE)
    print_colored("   --quiet       - عرض مختصر", Colors.BLUE)
    print()
    
    print_colored("=" * 70, Colors.LUGY)


# ============================================================
# نقاط الدخول من سطر الأوامر
# ============================================================

def parse_args():
    """تحليل معلمات سطر الأوامر"""
    args = sys.argv[1:]
    
    if not args:
        return "interactive"
    
    # الأوامر الرئيسية
    commands = {
        "all": "all",
        "coverage": "coverage",
        "quick": "quick",
        "failed": "failed",
        "info": "info",
        "help": "info",
        "--help": "info",
        "-h": "info"
    }
    
    if args[0] in commands:
        return commands[args[0]]
    
    # اختبار محدد
    return args[0]


if __name__ == "__main__":
    command = parse_args()
    
    if command == "interactive":
        run_tests()
    elif command == "all":
        run_all_tests()
    elif command == "coverage":
        run_tests_with_coverage()
    elif command == "quick":
        run_quick_tests()
    elif command == "failed":
        run_failed_tests()
    elif command == "info":
        tests_path = get_tests_path()
        available_tests = get_available_tests(tests_path) if tests_path else []
        show_tests_info(tests_path, available_tests)
    else:
        # تشغيل اختبار محدد
        tests_path = get_tests_path()
        if tests_path:
            print_header()
            run_specific_test(tests_path, command)
        else:
            print_error("❌ لم يتم العثور على مجلد الاختبارات")