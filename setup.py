"""
LugyFlutter - إعدادات التثبيت (Setup)
ملف setup.py لتثبيت LugyFlutter كحزمة Python
"""

import os
import re
import sys
from pathlib import Path
from setuptools import setup, find_packages

# ============================================================
# قراءة الإصدار من ملف agent.py
# ============================================================

def get_version():
    """استخراج الإصدار من ملف agent.py"""
    version_file = Path("src/core/agent.py")
    if not version_file.exists():
        return "2.0.0"
    
    content = version_file.read_text(encoding='utf-8')
    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    
    if match:
        return match.group(1)
    
    return "2.0.0"


# ============================================================
# قراءة README.md للمحتوى الطويل
# ============================================================

def get_long_description():
    """قراءة محتوى README.md للوصف الطويل"""
    readme_file = Path("README.md")
    
    if readme_file.exists():
        return readme_file.read_text(encoding='utf-8')
    
    return "LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow"


# ============================================================
# قراءة المتطلبات من requirements.txt
# ============================================================

def get_requirements():
    """قراءة المتطلبات من requirements.txt"""
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        return []
    
    requirements = []
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # تجاهل متطلبات التطوير
                if not any(x in line.lower() for x in ['pytest', 'black', 'flake8', 'mypy', 'isort']):
                    requirements.append(line)
    
    return requirements


# ============================================================
# قراءة متطلبات التطوير
# ============================================================

def get_dev_requirements():
    """قراءة متطلبات التطوير"""
    req_file = Path("requirements-dev.txt")
    
    if not req_file.exists():
        return []
    
    requirements = []
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    
    return requirements


# ============================================================
# إعدادات الحزمة
# ============================================================

setup(
    # معلومات الحزمة
    name="lugyflutter",
    version=get_version(),
    description="LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    
    # المؤلف
    author="LugyFlutter Team",
    author_email="support@lugyflutter.com",
    
    # الرابط
    url="https://github.com/lugyflutter/lugyflutter",
    project_urls={
        "Documentation": "https://lugyflutter.com/docs",
        "Source": "https://github.com/lugyflutter/lugyflutter",
        "Tracker": "https://github.com/lugyflutter/lugyflutter/issues",
    },
    
    # الترخيص
    license="MIT",
    
    # التصنيفات
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: Arabic",
        "Natural Language :: English",
    ],
    
    # الكلمات المفتاحية
    keywords=[
        "flutterflow",
        "ai-agent",
        "automation",
        "testing",
        "flutter",
        "gemini",
        "browser-automation",
        "self-healing",
        "checkpoint",
        "lugyflutter"
    ],
    
    # الحزم
    packages=find_packages(
        where="src",
        exclude=["tests", "tests.*", "*.tests", "*.tests.*"]
    ),
    package_dir={"": "src"},
    
    # تضمين الملفات الثابتة
    include_package_data=True,
    package_data={
        "lugyflutter": [
            "web/static/css/*.css",
            "web/static/js/*.js",
            "web/static/images/*.*",
        ],
    },
    
    # المتطلبات الأساسية
    install_requires=get_requirements(),
    
    # متطلبات التطوير
    extras_require={
        "dev": get_dev_requirements(),
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.0.0",
            "pytest-html>=3.2.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=2.0.0",
            "myst-parser>=1.0.0",
        ],
        "dashboard": [
            "streamlit>=1.28.0",
            "plotly>=5.17.0",
            "pandas>=2.0.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "python-multipart>=0.0.6",
        ],
        "vision": [
            "opencv-python>=4.8.0",
            "pytesseract>=0.3.10",
            "Pillow>=10.0.0",
        ],
        "all": [
            "streamlit>=1.28.0",
            "plotly>=5.17.0",
            "pandas>=2.0.0",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "python-multipart>=0.0.6",
            "opencv-python>=4.8.0",
            "pytesseract>=0.3.10",
            "Pillow>=10.0.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ],
    },
    
    # نقاط الدخول
    entry_points={
        "console_scripts": [
            "lugyflutter=main:main",
            "lugy-dashboard=src.web.dashboard:main",
            "lugy-api=src.web.api:run_api",
        ],
        "gui_scripts": [
            "lugy-gui=src.web.dashboard:main",
        ],
    },
    
    # متطلبات Python
    python_requires=">=3.8",
    
    # خيارات إضافية
    zip_safe=False,
    test_suite="pytest",
    tests_require=get_dev_requirements(),
    
    # معلومات إضافية
    setup_requires=[
        "setuptools>=45.0.0",
        "wheel>=0.37.0",
    ],
)

# ============================================================
# رسالة التثبيت الناجح
# ============================================================

print()
print("=" * 70)
print("🌟 LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow")
print("=" * 70)
print(f"📌 الإصدار: {get_version()}")
print("📦 الحزم المثبتة:", len(find_packages(where="src")))
print("=" * 70)
print()

# ============================================================
# تعليمات الاستخدام بعد التثبيت
# ============================================================

print("📌 بعد التثبيت، يمكنك:")
print("  • تشغيل LugyFlutter:          lugyflutter")
print("  • تشغيل لوحة التحكم:          lugy-dashboard")
print("  • تشغيل واجهة API:            lugy-api")
print("  • استيراد الوكيل في الكود:    from lugyflutter import LugyFlutter")
print()
print("📖 للتوثيق الكامل: https://lugyflutter.com/docs")
print("🐙 المصدر: https://github.com/lugyflutter/lugyflutter")
print()
print("=" * 70)
print("🌟 LugyFlutter - جاهز للاستخدام!")
print("=" * 70)
print()