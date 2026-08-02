#!/usr/bin/env python3
"""
LugyFlutter - نقطة الدخول الرئيسية
Main entry point for LugyFlutter application
"""

import sys
import os
import asyncio
from pathlib import Path

# إضافة مسار src إلى sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# استيراد المكونات الأساسية
from src.core.agent import LugyFlutter
from src.core.enums import InteractionMode
from src.core.config import config
from src.utils.safe_input import SafeInput
from src.utils.colors import print_colored, Colors, print_lugy_logo
from src.utils.helpers import check_required_libraries, export_logs_to_zip, check_environment, ensure_directory
from src.utils.logger import get_logger, set_log_level

# إعداد التسجيل
logger = get_logger(__name__)


# ============================================================
# دوال التشغيل
# ============================================================

def run_dashboard_only():
    """تشغيل لوحة التحكم فقط"""
    try:
        print_colored("\n🖥️ جاري تشغيل لوحة التحكم...", Colors.CYAN, bold=True)
        
        # استيراد WebDashboard
        try:
            from src.web.dashboard import main as dashboard_main
        except ImportError as e:
            print_colored(f"❌ فشل استيراد لوحة التحكم: {e}", Colors.RED)
            print_colored("💡 تأكد من تثبيت Streamlit: pip install streamlit", Colors.YELLOW)
            return
        
        # تشغيل لوحة التحكم
        dashboard_main()
        
    except Exception as e:
        print_colored(f"❌ خطأ في تشغيل لوحة التحكم: {e}", Colors.RED)
        import traceback
        traceback.print_exc()


def run_api_only():
    """تشغيل واجهة API فقط"""
    try:
        print_colored("\n🌐 جاري تشغيل واجهة API...", Colors.CYAN, bold=True)
        
        # استيراد API
        try:
            from src.web.api import run_api
        except ImportError as e:
            print_colored(f"❌ فشل استيراد واجهة API: {e}", Colors.RED)
            print_colored("💡 تأكد من تثبيت FastAPI و Uvicorn: pip install fastapi uvicorn", Colors.YELLOW)
            return
        
        # تشغيل API
        run_api()
        
    except Exception as e:
        print_colored(f"❌ خطأ في تشغيل واجهة API: {e}", Colors.RED)
        import traceback
        traceback.print_exc()


def run_tests():
    """تشغيل الاختبارات"""
    try:
        import pytest
        
        print_colored("\n🧪 جاري تشغيل الاختبارات...", Colors.CYAN, bold=True)
        print_colored("=" * 60, Colors.CYAN)
        
        # تحديد مسار الاختبارات
        test_path = Path(__file__).parent / "src" / "tests"
        
        if not test_path.exists():
            print_colored(f"⚠️ مجلد الاختبارات غير موجود: {test_path}", Colors.YELLOW)
            print_colored("💡 سيتم إنشاء مجلد الاختبارات تلقائياً", Colors.BLUE)
            test_path.mkdir(parents=True, exist_ok=True)
            
            # إنشاء ملف اختبارات بسيط
            init_file = test_path / "__init__.py"
            init_file.write_text("# LugyFlutter - اختبارات\n", encoding='utf-8')
            
            sample_test = test_path / "test_sample.py"
            sample_test.write_text("""
import pytest

def test_sample():
    \"\"\"اختبار عينة\"\"\"
    assert 1 == 1

def test_imports():
    \"\"\"اختبار استيراد المكونات\"\"\"
    try:
        from src.core.agent import LugyFlutter
        from src.core.enums import TaskType, InteractionMode
        assert True
    except ImportError as e:
        pytest.fail(f"فشل الاستيراد: {e}")
""", encoding='utf-8')
            
            print_colored("✅ تم إنشاء ملفات الاختبارات", Colors.GREEN)
        
        # تشغيل الاختبارات
        result = pytest.main([str(test_path), "-v", "--tb=short", "--color=yes"])
        
        if result == 0:
            print_colored("\n✅ جميع الاختبارات نجحت!", Colors.GREEN, bold=True)
        else:
            print_colored(f"\n❌ فشل {result} من الاختبارات", Colors.RED, bold=True)
            
    except ImportError as e:
        print_colored(f"❌ pytest غير مثبت: {e}", Colors.RED)
        print_colored("💡 قم بتثبيته: pip install pytest pytest-asyncio", Colors.YELLOW)
    except Exception as e:
        print_colored(f"❌ خطأ في تشغيل الاختبارات: {e}", Colors.RED)
        import traceback
        traceback.print_exc()


def show_version():
    """عرض إصدار LugyFlutter"""
    print_colored("\n" + "=" * 60, Colors.LUGY)
    print_colored("🤖 LugyFlutter", Colors.LUGY, bold=True)
    print_colored("=" * 60, Colors.LUGY)
    print_colored(f"📌 الإصدار: 2.0.0", Colors.CYAN)
    print_colored(f"📅 تاريخ الإصدار: 2024", Colors.CYAN)
    print_colored(f"🐍 Python: {sys.version}", Colors.CYAN)
    print_colored(f"📁 المسار: {Path(__file__).parent}", Colors.CYAN)
    print_colored("=" * 60, Colors.LUGY)
    
    # عرض معلومات الإعدادات
    print_colored("\n📋 الإعدادات الحالية:", Colors.YELLOW, bold=True)
    print_colored(f"   🔑 مفتاح API: {'✅ موجود' if config.GOOGLE_API_KEY else '❌ غير موجود'}", 
                 Colors.GREEN if config.GOOGLE_API_KEY else Colors.RED)
    print_colored(f"   🖥️ لوحة التحكم: {'✅ مفعلة' if config.WEB_DASHBOARD_ENABLED else '❌ معطلة'}", 
                 Colors.GREEN if config.WEB_DASHBOARD_ENABLED else Colors.RED)
    print_colored(f"   🌐 API: {'✅ مفعلة' if config.API_ENABLED else '❌ معطلة'}", 
                 Colors.GREEN if config.API_ENABLED else Colors.RED)
    print_colored(f"   🔧 الشفاء الذاتي: {'✅ مفعل' if config.AUTO_HEALING_ENABLED else '❌ معطل'}", 
                 Colors.GREEN if config.AUTO_HEALING_ENABLED else Colors.RED)
    print_colored(f"   📝 مستوى التسجيل: {config.LOG_LEVEL}", Colors.CYAN)
    print_colored(f"   💾 نقاط التفتيش: {config.MAX_CHECKPOINTS}", Colors.CYAN)


def show_help():
    """عرض المساعدة العامة"""
    print_colored("\n" + "=" * 70, Colors.LUGY)
    print_colored("📖 LugyFlutter - دليل الأوامر", Colors.LUGY, bold=True)
    print_colored("=" * 70, Colors.LUGY)
    
    print_colored("\n🔹 الأوامر الأساسية:", Colors.GREEN, bold=True)
    print_colored("   python main.py              تشغيل LugyFlutter في الوضع التفاعلي", Colors.BLUE)
    print_colored("   python main.py dashboard    تشغيل لوحة التحكم فقط", Colors.BLUE)
    print_colored("   python main.py api          تشغيل واجهة API فقط", Colors.BLUE)
    print_colored("   python main.py test         تشغيل الاختبارات", Colors.BLUE)
    print_colored("   python main.py version      عرض الإصدار والمعلومات", Colors.BLUE)
    print_colored("   python main.py help         عرض هذه المساعدة", Colors.BLUE)
    print_colored("   python main.py export       تصدير السجلات إلى ZIP", Colors.BLUE)
    print_colored("   python main.py clean        تنظيف الملفات المؤقتة والسجلات القديمة", Colors.BLUE)
    
    print_colored("\n🔹 الأوامر التفاعلية (داخل البرنامج):", Colors.GREEN, bold=True)
    print_colored("   /help     عرض المساعدة التفاعلية", Colors.BLUE)
    print_colored("   /undo     التراجع عن آخر إجراء", Colors.BLUE)
    print_colored("   /status   عرض الحالة الحالية", Colors.BLUE)
    print_colored("   /checkpoints عرض نقاط التفتيش", Colors.BLUE)
    print_colored("   /export   تصدير السجلات إلى ZIP", Colors.BLUE)
    print_colored("   /exit     إنهاء البرنامج", Colors.BLUE)
    
    print_colored("\n🔹 أمثلة على الطلبات:", Colors.GREEN, bold=True)
    print_colored("   'أنشئ مشروع جديد اسمه تطبيقي'", Colors.BLUE)
    print_colored("   'عدل مشروع التسوق وأضف زر في الصفحة الرئيسية'", Colors.BLUE)
    print_colored("   'انسخ هذا التصميم من Figma https://figma.com/design/abc123'", Colors.BLUE)
    print_colored("   'حلل تصميم المشروع الحالي وقدم تقريراً'", Colors.BLUE)
    
    print_colored("\n" + "=" * 70, Colors.LUGY)


def clean_project():
    """تنظيف الملفات المؤقتة والسجلات القديمة"""
    print_colored("\n🧹 جاري تنظيف المشروع...", Colors.CYAN, bold=True)
    
    # المجلدات المراد تنظيفها
    dirs_to_clean = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        ".coverage"
    ]
    
    # الملفات المراد حذفها
    files_to_clean = [
        ".coverage",
        "coverage.xml",
        ".pytest_cache"
    ]
    
    count = 0
    
    # حذف المجلدات
    for dir_name in dirs_to_clean:
        dir_path = Path(__file__).parent / dir_name
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print_colored(f"   ✅ حذف: {dir_path}", Colors.GREEN)
            count += 1
    
    # حذف الملفات
    for file_name in files_to_clean:
        file_path = Path(__file__).parent / file_name
        if file_path.exists():
            file_path.unlink()
            print_colored(f"   ✅ حذف: {file_path}", Colors.GREEN)
            count += 1
    
    # تنظيف السجلات القديمة (أكثر من 30 يوم)
    from src.utils.helpers import cleanup_old_files
    log_dir = Path("logs")
    if log_dir.exists():
        cleaned = cleanup_old_files(log_dir, days_old=30)
        if cleaned > 0:
            print_colored(f"   ✅ حذف {cleaned} ملف سجل قديم", Colors.GREEN)
            count += cleaned
    
    if count == 0:
        print_colored("   ℹ️ لا توجد ملفات للتنظيف", Colors.YELLOW)
    else:
        print_colored(f"\n✅ تم تنظيف {count} عنصر بنجاح!", Colors.GREEN, bold=True)


def check_environment_and_ready():
    """فحص البيئة والتأكد من جاهزية النظام"""
    print_colored("\n🔍 جاري فحص البيئة...", Colors.CYAN)
    
    # فحص المكتبات
    missing = check_required_libraries()
    
    if missing:
        print_colored(f"\n⚠️ المكتبات التالية غير مثبتة: {', '.join(missing)}", Colors.YELLOW)
        response = SafeInput.get_input("💬 هل تريد تثبيتها تلقائياً؟ (نعم/لا): ", default="نعم")
        if response.lower() in ["نعم", "yes", "y"]:
            import subprocess
            for package in missing:
                print_colored(f"📦 جاري تثبيت {package}...", Colors.BLUE)
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print_colored("✅ تم تثبيت جميع المكتبات!", Colors.GREEN)
        else:
            print_colored("⚠️ سيتم الاستمرار مع المكتبات الموجودة", Colors.YELLOW)
    
    # فحص البيئة
    env_check = check_environment()
    
    if env_check["issues"]:
        print_colored("\n❌ مشاكل في البيئة:", Colors.RED, bold=True)
        for issue in env_check["issues"]:
            print_colored(f"   • {issue}", Colors.RED)
        return False
    
    if env_check["warnings"]:
        print_colored("\n⚠️ تحذيرات:", Colors.YELLOW, bold=True)
        for warning in env_check["warnings"]:
            print_colored(f"   • {warning}", Colors.YELLOW)
    
    # التأكد من وجود المجلدات
    required_dirs = ["logs", "logs/screenshots", "logs/checkpoints", "logs/context"]
    for dir_path in required_dirs:
        ensure_directory(dir_path)
    
    print_colored("✅ فحص البيئة اكتمل بنجاح", Colors.GREEN)
    return True


async def main_async():
    """الوظيفة الرئيسية غير المتزامنة"""
    try:
        # فحص البيئة
        if not check_environment_and_ready():
            response = SafeInput.get_input("\n💬 هل تريد المتابعة رغم التحذيرات؟ (نعم/لا): ", default="لا")
            if response.lower() not in ["نعم", "yes", "y"]:
                print_colored("👋 تم الإلغاء.", Colors.YELLOW)
                return
        
        # طباعة الشعار
        print_lugy_logo()
        
        # اختيار وضع التشغيل
        mode_choice = SafeInput.get_choice(
            "\n🚀 اختر وضع التشغيل:",
            [
                "تشغيل عادي (محادثة تفاعلية)",
                "لوحة تحكم ويب فقط",
                "تنفيذ مهمة محددة",
                "تشغيل الاختبارات",
                "عرض المساعدة"
            ]
        )
        
        if mode_choice == "تشغيل الاختبارات":
            run_tests()
            return
        
        if mode_choice == "لوحة تحكم ويب فقط":
            run_dashboard_only()
            return
        
        if mode_choice == "عرض المساعدة":
            show_help()
            return
        
        if mode_choice == "تنفيذ مهمة محددة":
            # اختيار وضع التفاعل للمهمة المحددة
            interaction_choice = SafeInput.get_choice(
                "\n🤖 اختر وضع التفاعل:",
                [
                    "تفاعلي كامل (يسأل قبل كل شيء)",
                    "تأكيد الخطوات فقط",
                    "توضيحات فقط (يسأل عند الغموض)",
                    "تلقائي بالكامل",
                    "وضع التصحيح (خطوة بخطوة)"
                ]
            )
            
            mode_map = {
                "تفاعلي كامل (يسأل قبل كل شيء)": InteractionMode.FULL_INTERACTIVE,
                "تأكيد الخطوات فقط": InteractionMode.CONFIRM_STEPS,
                "توضيحات فقط (يسأل عند الغموض)": InteractionMode.ASK_CLARIFICATIONS,
                "تلقائي بالكامل": InteractionMode.AUTO,
                "وضع التصحيح (خطوة بخطوة)": InteractionMode.DEBUG
            }
            
            mode = mode_map.get(interaction_choice, InteractionMode.FULL_INTERACTIVE)
            
            # إنشاء الوكيل
            print_colored("\n🔧 جاري تهيئة LugyFlutter...", Colors.CYAN)
            lugy = LugyFlutter(mode=mode)
            
            # طلب المهمة
            task = SafeInput.get_input("\n💬 أدخل مهمتك: ", allow_empty=False)
            
            # تنفيذ المهمة
            await lugy.process_user_request(task)
            
            # حفظ السجلات
            export_logs_to_zip(Path("logs"))
            return
        
        # تشغيل عادي (محادثة تفاعلية)
        # اختيار وضع التفاعل
        interaction_choice = SafeInput.get_choice(
            "\n🤖 اختر وضع التفاعل:",
            [
                "تفاعلي كامل (يسأل قبل كل شيء)",
                "تأكيد الخطوات فقط",
                "توضيحات فقط (يسأل عند الغموض)",
                "تلقائي بالكامل",
                "وضع التصحيح (خطوة بخطوة)"
            ]
        )
        
        mode_map = {
            "تفاعلي كامل (يسأل قبل كل شيء)": InteractionMode.FULL_INTERACTIVE,
            "تأكيد الخطوات فقط": InteractionMode.CONFIRM_STEPS,
            "توضيحات فقط (يسأل عند الغموض)": InteractionMode.ASK_CLARIFICATIONS,
            "تلقائي بالكامل": InteractionMode.AUTO,
            "وضع التصحيح (خطوة بخطوة)": InteractionMode.DEBUG
        }
        
        mode = mode_map.get(interaction_choice, InteractionMode.FULL_INTERACTIVE)
        
        # إنشاء وتشغيل الوكيل
        print_colored("\n🔧 جاري تهيئة LugyFlutter...", Colors.CYAN)
        lugy = LugyFlutter(mode=mode)
        
        # تشغيل لوحة التحكم في الخلفية (إذا كانت مفعلة)
        if config.WEB_DASHBOARD_ENABLED:
            try:
                import threading
                from src.web.dashboard import main as dashboard_main
                
                dashboard_thread = threading.Thread(
                    target=dashboard_main,
                    daemon=True
                )
                dashboard_thread.start()
                print_colored(f"\n🖥️ لوحة التحكم تعمل على: http://localhost:{config.WEB_DASHBOARD_PORT}", 
                             Colors.GREEN)
                print_colored("💡 افتح الرابط في متصفحك لمتابعة التنفيذ", Colors.CYAN)
            except Exception as e:
                print_colored(f"⚠️ فشل تشغيل لوحة التحكم: {e}", Colors.YELLOW)
                print_colored("💡 يمكنك تشغيلها لاحقاً باستخدام: python main.py dashboard", Colors.BLUE)
        
        # بدء المحادثة
        await lugy.start_conversation()
        
    except KeyboardInterrupt:
        print_colored("\n\n👋 تم إيقاف LugyFlutter بواسطة المستخدم.", Colors.YELLOW)
        export_logs_to_zip(Path("logs"))
    except Exception as e:
        print_colored(f"\n❌ خطأ فادح: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        print_colored("\n💡 تم حفظ السجلات في مجلد logs/", Colors.CYAN)
        export_logs_to_zip(Path("logs"))


def main():
    """الوظيفة الرئيسية"""
    # معالجة أوامر سطر الأوامر
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "dashboard":
            run_dashboard_only()
        elif command == "api":
            run_api_only()
        elif command == "test":
            run_tests()
        elif command == "version":
            show_version()
        elif command == "help" or command == "--help" or command == "-h":
            show_help()
        elif command == "export":
            # تصدير السجلات
            export_logs_to_zip(Path("logs"))
        elif command == "clean":
            clean_project()
        elif command == "setup":
            # تشغيل سكربت الإعداد
            import subprocess
            if sys.platform == "win32":
                subprocess.call(["scripts\\setup.bat"])
            else:
                subprocess.call(["chmod", "+x", "scripts/setup.sh"])
                subprocess.call(["./scripts/setup.sh"])
        else:
            print_colored(f"⚠️ أمر غير معروف: {command}", Colors.YELLOW)
            show_help()
        return
    
    # تشغيل الوضع الرئيسي
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print_colored("\n\n👋 تم إيقاف LugyFlutter بواسطة المستخدم.", Colors.YELLOW)
    except Exception as e:
        print_colored(f"\n❌ خطأ فادح: {e}", Colors.RED)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()