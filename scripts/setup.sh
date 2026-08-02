#!/bin/bash
# ============================================================
# LugyFlutter - سكربت الإعداد (Linux/Mac)
# ============================================================
# هذا السكربت يقوم بإعداد بيئة LugyFlutter وتثبيت جميع المتطلبات
# ============================================================

# ألوان الطباعة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================
# دوال مساعدة
# ============================================================

print_header() {
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ██╗     ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██╗             ║"
    echo "║  ██║     ██║   ██║██╔════╝ ╚██╗ ██╔╝██╔════╝██║             ║"
    echo "║  ██║     ██║   ██║██║  ███╗ ╚████╔╝ █████╗  ██║             ║"
    echo "║  ██║     ██║   ██║██║   ██║  ╚██╔╝  ██╔══╝  ██║             ║"
    echo "║  ███████╗╚██████╔╝╚██████╔╝   ██║   ██║     ███████╗        ║"
    echo "║  ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚══════╝        ║"
    echo "║                                                               ║"
    echo "║  ███████╗██╗     ██╗   ██╗████████╗████████╗███████╗██████╗  ║"
    echo "║  ██╔════╝██║     ██║   ██║╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗ ║"
    echo "║  █████╗  ██║     ██║   ██║   ██║      ██║   █████╗  ██████╔╝ ║"
    echo "║  ██╔══╝  ██║     ██║   ██║   ██║      ██║   ██╔══╝  ██╔══██╗ ║"
    echo "║  ██║     ███████╗╚██████╔╝   ██║      ██║   ███████╗██║  ██║ ║"
    echo "║  ╚═╝     ╚══════╝ ╚═════╝    ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝ ║"
    echo "║                                                               ║"
    echo "║     🤖 الوكيل الذكي المتخصص في FlutterFlow                   ║"
    echo "║     📌 الإصدار 2.0.0 | 🚀 Legendary User Guide               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 غير موجود. يرجى تثبيته أولاً."
        return 1
    else
        print_info "$1 موجود: $(command -v $1)"
        return 0
    fi
}

# ============================================================
# بدء السكربت
# ============================================================

clear
print_header

echo -e "${GREEN}🚀 جاري إعداد LugyFlutter v2.0.0...${NC}"
echo ""

# ============================================================
# 1. فحص Python
# ============================================================

print_step "1. فحص Python..."

if ! check_command python3; then
    print_error "Python 3 غير موجود. يرجى تثبيت Python 3.8 أو أعلى."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_info "Python الإصدار: $PYTHON_VERSION"

# فحص الإصدار
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 8 ]; then
    print_error "Python 3.8 أو أعلى مطلوب. الإصدار الحالي: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION جاهز"

# ============================================================
# 2. فحص pip
# ============================================================

print_step "2. فحص pip..."

if ! check_command pip3; then
    print_warning "pip غير موجود. جاري التثبيت..."
    python3 -m ensurepip --upgrade
fi

PIP_VERSION=$(pip3 --version 2>&1 | cut -d' ' -f2)
print_info "pip الإصدار: $PIP_VERSION"
print_success "pip جاهز"

# ============================================================
# 3. إنشاء البيئة الافتراضية
# ============================================================

print_step "3. إنشاء البيئة الافتراضية (Virtual Environment)..."

if [ -d "venv" ]; then
    print_warning "البيئة الافتراضية موجودة بالفعل"
    read -p "هل تريد إعادة إنشائها؟ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "تم إعادة إنشاء البيئة الافتراضية"
    fi
else
    python3 -m venv venv
    print_success "تم إنشاء البيئة الافتراضية"
fi

# تنشيط البيئة الافتراضية
source venv/bin/activate
print_success "تم تنشيط البيئة الافتراضية"

# ============================================================
# 4. تحديث pip
# ============================================================

print_step "4. تحديث pip..."

pip install --upgrade pip
print_success "تم تحديث pip"

# ============================================================
# 5. تثبيت المتطلبات
# ============================================================

print_step "5. تثبيت المتطلبات..."

if [ -f "requirements.txt" ]; then
    print_info "جاري تثبيت المتطلبات من requirements.txt..."
    pip install -r requirements.txt
    print_success "تم تثبيت جميع المتطلبات"
else
    print_warning "ملف requirements.txt غير موجود"
fi

# ============================================================
# 6. تثبيت المتطلبات الإضافية للتطوير
# ============================================================

print_step "6. تثبيت متطلبات التطوير..."

if [ -f "requirements-dev.txt" ]; then
    read -p "هل تريد تثبيت متطلبات التطوير (pytest, etc.)؟ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install -r requirements-dev.txt
        print_success "تم تثبيت متطلبات التطوير"
    fi
else
    print_info "ملف requirements-dev.txt غير موجود"
fi

# ============================================================
# 7. تثبيت Playwright
# ============================================================

print_step "7. تثبيت Playwright..."

pip install playwright
playwright install
print_success "تم تثبيت Playwright"

# ============================================================
# 8. إنشاء المجلدات
# ============================================================

print_step "8. إنشاء المجلدات..."

mkdir -p logs/screenshots
mkdir -p logs/checkpoints
mkdir -p logs/context
mkdir -p logs/sessions

print_success "تم إنشاء المجلدات"

# ============================================================
# 9. إنشاء ملف .env
# ============================================================

print_step "9. إعداد ملف .env..."

if [ -f ".env" ]; then
    print_warning "ملف .env موجود بالفعل"
    read -p "هل تريد إعادة إنشائه؟ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env 2>/dev/null || echo "# LugyFlutter - ملف الإعدادات" > .env
        print_success "تم إعادة إنشاء ملف .env"
    fi
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "تم إنشاء ملف .env من .env.example"
    else
        cat > .env << 'EOF'
# LugyFlutter - ملف الإعدادات
# =============================

# إعدادات Google Gemini API
GOOGLE_API_KEY=your_api_key_here

# إعدادات المتصفح
CHROME_USER_DATA_DIR=
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30

# إعدادات LugyFlutter
LOG_LEVEL=INFO
MAX_STEPS=30
RETRY_DELAY=3
SAVE_SCREENSHOTS=true
LUGY_MODE=interactive

# إعدادات الويب
WEB_DASHBOARD_ENABLED=true
WEB_DASHBOARD_PORT=8501
API_ENABLED=false
API_PORT=8000

# إعدادات متقدمة
AUTO_HEALING_ENABLED=true
VISION_FALLBACK_ENABLED=true
CONTEXT_MEMORY_SIZE=100
MAX_CHECKPOINTS=20
EOF
        print_success "تم إنشاء ملف .env"
    fi
fi

print_warning "⚠️ يرجى تعديل ملف .env وإضافة مفتاح Google Gemini API الخاص بك"

# ============================================================
# 10. إنشاء ملفات الاختبارات
# ============================================================

print_step "10. إعداد ملفات الاختبارات..."

if [ ! -d "src/tests" ]; then
    mkdir -p src/tests
    cat > src/tests/__init__.py << 'EOF'
"""
LugyFlutter - اختبارات الوحدة
"""
EOF
    print_success "تم إنشاء مجلد الاختبارات"
fi

# ============================================================
# 11. إنشاء سكربتات التشغيل
# ============================================================

print_step "11. إنشاء سكربتات التشغيل..."

# سكربت تشغيل لوحة التحكم
cat > run_dashboard.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run src/web/dashboard.py --server.port=8501
EOF
chmod +x run_dashboard.sh

# سكربت تشغيل API
cat > run_api.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --reload
EOF
chmod +x run_api.sh

# سكربت تشغيل الاختبارات
cat > run_tests.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
pytest src/tests -v --tb=short --color=yes
EOF
chmod +x run_tests.sh

print_success "تم إنشاء سكربتات التشغيل:"
print_info "  • ./run_dashboard.sh - تشغيل لوحة التحكم"
print_info "  • ./run_api.sh - تشغيل واجهة API"
print_info "  • ./run_tests.sh - تشغيل الاختبارات"

# ============================================================
# 12. إنشاء سكربت الإلغاء
# ============================================================

print_step "12. إنشاء سكربت الإلغاء..."

cat > uninstall.sh << 'EOF'
#!/bin/bash
# ============================================================
# LugyFlutter - سكربت إلغاء التثبيت
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}⚠️ هذا السكربت سيحذف كل شيء متعلق بـ LugyFlutter${NC}"
read -p "هل أنت متأكد؟ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}🗑️ جاري الحذف...${NC}"
    
    # حذف البيئة الافتراضية
    rm -rf venv
    
    # حذف المجلدات
    rm -rf logs
    rm -rf __pycache__
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    
    # حذف الملفات
    rm -f .env
    rm -f lugy_logs_*.zip
    
    # حذف السكربتات
    rm -f run_dashboard.sh
    rm -f run_api.sh
    rm -f run_tests.sh
    
    echo -e "${GREEN}✅ تم إلغاء تثبيت LugyFlutter${NC}"
else
    echo -e "${GREEN}❌ تم الإلغاء${NC}"
fi
EOF
chmod +x uninstall.sh

print_success "تم إنشاء سكربت الإلغاء: ./uninstall.sh"

# ============================================================
# 13. عرض الملخص النهائي
# ============================================================

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ تم إعداد LugyFlutter بنجاح!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""

print_info "📁 البيئة الافتراضية: venv/"
print_info "📁 مجلد السجلات: logs/"
print_info "📁 مجلد الاختبارات: src/tests/"
print_info "📄 ملف الإعدادات: .env"

echo ""
print_info "🚀 لتشغيل LugyFlutter:"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo -e "   ${BLUE}python main.py${NC}"

echo ""
print_info "🖥️ لتشغيل لوحة التحكم:"
echo -e "   ${BLUE}./run_dashboard.sh${NC}"

echo ""
print_info "🌐 لتشغيل واجهة API:"
echo -e "   ${BLUE}./run_api.sh${NC}"

echo ""
print_info "🧪 لتشغيل الاختبارات:"
echo -e "   ${BLUE}./run_tests.sh${NC}"

echo ""
print_warning "⚠️ تذكر تعديل ملف .env وإضافة مفتاح Google Gemini API الخاص بك"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}🌟 LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================
# نهاية السكربت
# ============================================================