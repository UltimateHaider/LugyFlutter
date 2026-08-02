@echo off
REM ============================================================
REM LugyFlutter - سكربت الإعداد (Windows)
REM ============================================================
REM هذا السكربت يقوم بإعداد بيئة LugyFlutter وتثبيت جميع المتطلبات
REM ============================================================

setlocal enabledelayedexpansion

REM ============================================================
REM ألوان الطباعة
REM ============================================================

set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "MAGENTA=[35m"
set "CYAN=[36m"
set "WHITE=[37m"
set "NC=[0m"

REM ============================================================
REM دوال مساعدة
REM ============================================================

:print_header
echo.
echo %MAGENTA%╔═══════════════════════════════════════════════════════════════╗%NC%
echo %MAGENTA%║  ██╗     ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██╗             ║%NC%
echo %MAGENTA%║  ██║     ██║   ██║██╔════╝ ╚██╗ ██╔╝██╔════╝██║             ║%NC%
echo %MAGENTA%║  ██║     ██║   ██║██║  ███╗ ╚████╔╝ █████╗  ██║             ║%NC%
echo %MAGENTA%║  ██║     ██║   ██║██║   ██║  ╚██╔╝  ██╔══╝  ██║             ║%NC%
echo %MAGENTA%║  ███████╗╚██████╔╝╚██████╔╝   ██║   ██║     ███████╗        ║%NC%
echo %MAGENTA%║  ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚══════╝        ║%NC%
echo %MAGENTA%║                                                               ║%NC%
echo %MAGENTA%║  ███████╗██╗     ██╗   ██╗████████╗████████╗███████╗██████╗  ║%NC%
echo %MAGENTA%║  ██╔════╝██║     ██║   ██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗ ║%NC%
echo %MAGENTA%║  █████╗  ██║     ██║   ██║   ██║      ██║   █████╗  ██████╔╝ ║%NC%
echo %MAGENTA%║  ██╔══╝  ██║     ██║   ██║   ██║      ██║   ██╔══╝  ██╔══██╗ ║%NC%
echo %MAGENTA%║  ██║     ███████╗╚██████╔╝   ██║      ██║   ███████╗██║  ██║ ║%NC%
echo %MAGENTA%║  ╚═╝     ╚══════╝ ╚═════╝    ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝ ║%NC%
echo %MAGENTA%║                                                               ║%NC%
echo %MAGENTA%║     🤖 الوكيل الذكي المتخصص في FlutterFlow                   ║%NC%
echo %MAGENTA%║     📌 الإصدار 2.0.0 | 🚀 Legendary User Guide               ║%NC%
echo %MAGENTA%╚═══════════════════════════════════════════════════════════════╝%NC%
echo.
goto :eof

:print_step
echo.
echo %BLUE%▶ %~1%NC%
goto :eof

:print_success
echo %GREEN%✅ %~1%NC%
goto :eof

:print_error
echo %RED%❌ %~1%NC%
goto :eof

:print_warning
echo %YELLOW%⚠️ %~1%NC%
goto :eof

:print_info
echo %CYAN%ℹ️ %~1%NC%
goto :eof

:check_python
python --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Python غير موجود. يرجى تثبيت Python 3.8 أو أعلى."
    echo.
    echo %YELLOW%💡 قم بتحميل Python من: https://www.python.org/downloads/%NC%
    echo %YELLOW%💡 تأكد من تحديد خيار 'Add Python to PATH' أثناء التثبيت%NC%
    pause
    exit /b 1
)
goto :eof

:check_pip
pip --version >nul 2>&1
if errorlevel 1 (
    call :print_warning "pip غير موجود. جاري التثبيت..."
    python -m ensurepip --upgrade
)
goto :eof

:create_shortcut
if exist "%~1" (
    call :print_warning "%~1 موجود بالفعل"
    set /p overwrite="هل تريد استبداله؟ (y/n): "
    if /i "!overwrite!"=="y" (
        del "%~1"
        copy "%~2" "%~1" >nul
        call :print_success "تم إنشاء %~1"
    )
) else (
    copy "%~2" "%~1" >nul
    call :print_success "تم إنشاء %~1"
)
goto :eof

REM ============================================================
REM بدء السكربت
REM ============================================================

cls
call :print_header

echo %GREEN%🚀 جاري إعداد LugyFlutter v2.0.0...%NC%
echo.

REM ============================================================
REM 1. فحص Python
REM ============================================================

call :print_step "1. فحص Python..."
call :check_python
if errorlevel 1 exit /b 1

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :print_info "Python الإصدار: %PYTHON_VERSION%"

REM فحص الإصدار
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    call :print_error "Python 3.8 أو أعلى مطلوب. الإصدار الحالي: %PYTHON_VERSION%"
    pause
    exit /b 1
)
if %PYTHON_MINOR% LSS 8 (
    call :print_error "Python 3.8 أو أعلى مطلوب. الإصدار الحالي: %PYTHON_VERSION%"
    pause
    exit /b 1
)

call :print_success "Python %PYTHON_VERSION% جاهز"

REM ============================================================
REM 2. فحص pip
REM ============================================================

call :print_step "2. فحص pip..."
call :check_pip

for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
call :print_info "pip الإصدار: %PIP_VERSION%"
call :print_success "pip جاهز"

REM ============================================================
REM 3. إنشاء البيئة الافتراضية
REM ============================================================

call :print_step "3. إنشاء البيئة الافتراضية (Virtual Environment)..."

if exist "venv" (
    call :print_warning "البيئة الافتراضية موجودة بالفعل"
    set /p recreate="هل تريد إعادة إنشائها؟ (y/n): "
    if /i "!recreate!"=="y" (
        rmdir /s /q venv
        python -m venv venv
        call :print_success "تم إعادة إنشاء البيئة الافتراضية"
    )
) else (
    python -m venv venv
    call :print_success "تم إنشاء البيئة الافتراضية"
)

REM تنشيط البيئة الافتراضية
call venv\Scripts\activate.bat
call :print_success "تم تنشيط البيئة الافتراضية"

REM ============================================================
REM 4. تحديث pip
REM ============================================================

call :print_step "4. تحديث pip..."

python -m pip install --upgrade pip
call :print_success "تم تحديث pip"

REM ============================================================
REM 5. تثبيت المتطلبات
REM ============================================================

call :print_step "5. تثبيت المتطلبات..."

if exist "requirements.txt" (
    call :print_info "جاري تثبيت المتطلبات من requirements.txt..."
    pip install -r requirements.txt
    call :print_success "تم تثبيت جميع المتطلبات"
) else (
    call :print_warning "ملف requirements.txt غير موجود"
)

REM ============================================================
REM 6. تثبيت المتطلبات الإضافية للتطوير
REM ============================================================

call :print_step "6. تثبيت متطلبات التطوير..."

if exist "requirements-dev.txt" (
    set /p install_dev="هل تريد تثبيت متطلبات التطوير (pytest, etc.)؟ (y/n): "
    if /i "!install_dev!"=="y" (
        pip install -r requirements-dev.txt
        call :print_success "تم تثبيت متطلبات التطوير"
    )
) else (
    call :print_info "ملف requirements-dev.txt غير موجود"
)

REM ============================================================
REM 7. تثبيت Playwright
REM ============================================================

call :print_step "7. تثبيت Playwright..."

pip install playwright
playwright install
call :print_success "تم تثبيت Playwright"

REM ============================================================
REM 8. إنشاء المجلدات
REM ============================================================

call :print_step "8. إنشاء المجلدات..."

if not exist "logs" mkdir logs
if not exist "logs\screenshots" mkdir logs\screenshots
if not exist "logs\checkpoints" mkdir logs\checkpoints
if not exist "logs\context" mkdir logs\context
if not exist "logs\sessions" mkdir logs\sessions

call :print_success "تم إنشاء المجلدات"

REM ============================================================
REM 9. إنشاء ملف .env
REM ============================================================

call :print_step "9. إعداد ملف .env..."

if exist ".env" (
    call :print_warning "ملف .env موجود بالفعل"
    set /p recreate_env="هل تريد إعادة إنشائه؟ (y/n): "
    if /i "!recreate_env!"=="y" (
        if exist ".env.example" (
            copy .env.example .env >nul
        ) else (
            call :create_default_env
        )
        call :print_success "تم إعادة إنشاء ملف .env"
    )
) else (
    if exist ".env.example" (
        copy .env.example .env >nul
        call :print_success "تم إنشاء ملف .env من .env.example"
    ) else (
        call :create_default_env
        call :print_success "تم إنشاء ملف .env"
    )
)

call :print_warning "⚠️ يرجى تعديل ملف .env وإضافة مفتاح Google Gemini API الخاص بك"

goto :skip_env_creation

:create_default_env
(
echo # LugyFlutter - ملف الإعدادات
echo # =============================
echo.
echo # إعدادات Google Gemini API
echo GOOGLE_API_KEY=your_api_key_here
echo.
echo # إعدادات المتصفح
echo CHROME_USER_DATA_DIR=
echo BROWSER_HEADLESS=false
echo BROWSER_TIMEOUT=30
echo.
echo # إعدادات LugyFlutter
echo LOG_LEVEL=INFO
echo MAX_STEPS=30
echo RETRY_DELAY=3
echo SAVE_SCREENSHOTS=true
echo LUGY_MODE=interactive
echo.
echo # إعدادات الويب
echo WEB_DASHBOARD_ENABLED=true
echo WEB_DASHBOARD_PORT=8501
echo API_ENABLED=false
echo API_PORT=8000
echo.
echo # إعدادات متقدمة
echo AUTO_HEALING_ENABLED=true
echo VISION_FALLBACK_ENABLED=true
echo CONTEXT_MEMORY_SIZE=100
echo MAX_CHECKPOINTS=20
) > .env
goto :eof

:skip_env_creation

REM ============================================================
REM 10. إنشاء سكربتات التشغيل
REM ============================================================

call :print_step "10. إنشاء سكربتات التشغيل..."

REM سكربت تشغيل لوحة التحكم
(
echo @echo off
echo call venv\Scripts\activate.bat
echo streamlit run src/web/dashboard.py --server.port=8501
echo pause
) > run_dashboard.bat

REM سكربت تشغيل API
(
echo @echo off
echo call venv\Scripts\activate.bat
echo python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --reload
echo pause
) > run_api.bat

REM سكربت تشغيل الاختبارات
(
echo @echo off
echo call venv\Scripts\activate.bat
echo pytest src/tests -v --tb=short --color=yes
echo pause
) > run_tests.bat

call :print_success "تم إنشاء سكربتات التشغيل:"
call :print_info "  • run_dashboard.bat - تشغيل لوحة التحكم"
call :print_info "  • run_api.bat - تشغيل واجهة API"
call :print_info "  • run_tests.bat - تشغيل الاختبارات"

REM ============================================================
REM 11. إنشاء سكربت الإلغاء
REM ============================================================

call :print_step "11. إنشاء سكربت الإلغاء..."

(
echo @echo off
echo REM ============================================================
echo REM LugyFlutter - سكربت إلغاء التثبيت
echo REM ============================================================
echo.
echo echo %YELLOW%⚠️ هذا السكربت سيحذف كل شيء متعلق بـ LugyFlutter%NC%
echo set /p confirm="هل أنت متأكد؟ (y/n): "
echo if /i "!confirm!"=="y" (
echo     echo %RED%🗑️ جاري الحذف...%NC%
echo     rmdir /s /q venv 2>nul
echo     rmdir /s /q logs 2>nul
echo     rmdir /s /q __pycache__ 2>nul
echo     rmdir /s /q .pytest_cache 2>nul
echo     del /f /q .env 2>nul
echo     del /f /q lugy_logs_*.zip 2>nul
echo     del /f /q run_dashboard.bat 2>nul
echo     del /f /q run_api.bat 2>nul
echo     del /f /q run_tests.bat 2>nul
echo     echo %GREEN%✅ تم إلغاء تثبيت LugyFlutter%NC%
echo ^) else (
echo     echo %GREEN%❌ تم الإلغاء%NC%
echo ^)
echo pause
) > uninstall.bat

call :print_success "تم إنشاء سكربت الإلغاء: uninstall.bat"

REM ============================================================
REM 12. عرض الملخص النهائي
REM ============================================================

echo.
echo %GREEN%════════════════════════════════════════════════════════════════%NC%
echo %GREEN%✅ تم إعداد LugyFlutter بنجاح!%NC%
echo %GREEN%════════════════════════════════════════════════════════════════%NC%
echo.

call :print_info "📁 البيئة الافتراضية: venv/"
call :print_info "📁 مجلد السجلات: logs/"
call :print_info "📁 مجلد الاختبارات: src/tests/"
call :print_info "📄 ملف الإعدادات: .env"

echo.
call :print_info "🚀 لتشغيل LugyFlutter:"
echo    %BLUE%venv\Scripts\activate.bat%NC%
echo    %BLUE%python main.py%NC%

echo.
call :print_info "🖥️ لتشغيل لوحة التحكم:"
echo    %BLUE%run_dashboard.bat%NC%

echo.
call :print_info "🌐 لتشغيل واجهة API:"
echo    %BLUE%run_api.bat%NC%

echo.
call :print_info "🧪 لتشغيل الاختبارات:"
echo    %BLUE%run_tests.bat%NC%

echo.
call :print_warning "⚠️ تذكر تعديل ملف .env وإضافة مفتاح Google Gemini API الخاص بك"

echo.
echo %GREEN%════════════════════════════════════════════════════════════════%NC%
echo %MAGENTA%🌟 LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow%NC%
echo %GREEN%════════════════════════════════════════════════════════════════%NC%
echo.

pause

REM ============================================================
REM نهاية السكربت
REM ============================================================