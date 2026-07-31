# 🤖 LugyFlutter - الوكيل الذكي المتخصص في FlutterFlow

<div align="center">

![LugyFlutter Logo](https://via.placeholder.com/800x200/6200EE/FFFFFF?text=LugyFlutter+AI+Agent)

**الوكيل الذكي الذي يغير طريقة تطوير تطبيقات FlutterFlow**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-purple.svg)]()

</div>

---

## 📖 نبذة

**LugyFlutter** هو وكيل ذكي متخصص في أتمتة وتطوير تطبيقات **FlutterFlow** باستخدام الذكاء الاصطناعي. يمكنه:

- ✅ إنشاء مشاريع جديدة تلقائياً
- ✅ تعديل مشاريع موجودة
- ✅ نسخ تصاميم من **Figma** و **Lovable**
- ✅ تحليل وتصميم واجهات المستخدم
- ✅ إدارة نقاط التفتيش والتراجع عن التغييرات
- ✅ التفاعل مع المستخدم عبر واجهات متعددة

---

## 🚀 الميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| 🧠 **ذكاء اصطناعي** | استخدام Google Gemini API لفهم وتنفيذ الأوامر |
| 🔧 **الشفاء الذاتي** | نظام متقدم لإصلاح محددات العناصر تلقائياً |
| 🖥️ **لوحة تحكم ويب** | واجهة رسومية باستخدام Streamlit |
| 🌐 **واجهة API** | دعم FastAPI للتكامل مع الأنظمة الأخرى |
| 💾 **نقاط تفتيش** | حفظ واستعادة الحالة مع Undo/Redo |
| 📝 **سجل المحادثات** | حفظ وتصدير جميع المحادثات |
| 🔒 **تفاعل آمن** | معالجة متقدمة للأخطاء والإدخالات |
| 🎨 **دعم متعدد اللغات** | العربية والإنجليزية |
| 📊 **تحليلات الأداء** | رسوم بيانية وإحصائيات متقدمة |
| 🔍 **رؤية حاسوبية** | كشف العناصر باستخدام OpenCV و Tesseract |

---

## 📦 المتطلبات

- **Python 3.8+**
- **Google Gemini API Key**
- **Chrome Browser** (للأتمتة)
- **اتصال بالإنترنت** (لتحميل المكتبات)

---

## 🛠️ التثبيت

**1. استنساخ المشروع**

git clone https://github.com/yourusername/lugyflutter.git
cd lugyflutter

**2. تشغيل سكربت الإعداد**

على Linux/Mac:
chmod +x scripts/setup.sh
./scripts/setup.sh

على Windows:
scripts\setup.bat

**3. تثبيت المتطلبات يدوياً (اختياري)**

إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  أو venv\Scripts\activate على Windows

تثبيت المتطلبات
pip install -r requirements.txt
playwright install

**4. إعداد ملف .env**

انسخ .env.example إلى .env وأضف مفتاح API الخاص بك:

GOOGLE_API_KEY=your_api_key_here
BROWSER_HEADLESS=false
LOG_LEVEL=INFO
WEB_DASHBOARD_ENABLED=true
WEB_DASHBOARD_PORT=8501
API_ENABLED=false
API_PORT=8000

---

## 🚀 التشغيل

**1. تشغيل الوكيل الرئيسي**

python main.py

**2. تشغيل لوحة التحكم**

باستخدام سكربت التشغيل:
./run_dashboard.sh  # Linux/Mac
run_dashboard.bat   # Windows

أو مباشرة:
streamlit run src/web/dashboard.py --server.port=8501

**3. تشغيل واجهة API**

باستخدام سكربت التشغيل:
./run_api.sh  # Linux/Mac
run_api.bat   # Windows

أو مباشرة:
uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --reload

**4. تشغيل الاختبارات**

باستخدام سكربت التشغيل:
./run_tests.sh  # Linux/Mac
run_tests.bat   # Windows

أو مباشرة:
pytest src/tests -v

---

## 📁 هيكلية المشروع

lugyflutter/
├── src/
│   ├── core/                 # المكونات الأساسية
│   │   ├── agent.py          # الوكيل الرئيسي LugyFlutter
│   │   ├── config.py         # إدارة الإعدادات
│   │   ├── enums.py          # الأنواع العامة
│   │   └── exceptions.py     # الاستثناءات المخصصة
│   │
│   ├── extraction/           # نظام استخراج المعلومات
│   │   ├── extractor.py      # مستخرج المعلومات
│   │   ├── regex_patterns.py # أنماط Regex
│   │   └── llm_fallback.py   # خيار LLM البديل
│   │
│   ├── browser/              # إدارة المتصفح
│   │   ├── browser_manager.py   # مدير المتصفح
│   │   ├── self_healing.py      # نظام الشفاء الذاتي
│   │   ├── vision_fallback.py   # الرؤية الحاسوبية
│   │   └── selectors.py         # محددات العناصر
│   │
│   ├── checkpoint/           # نظام نقاط التفتيش
│   │   ├── checkpoint_manager.py
│   │   ├── checkpoint_storage.py
│   │   └── state_sync.py
│   │
│   ├── context/              # إدارة السياق
│   │   ├── context_manager.py
│   │   ├── project_registry.py
│   │   └── conversation_logger.py
│   │
│   ├── utils/                # أدوات مساعدة
│   │   ├── colors.py
│   │   ├── logger.py
│   │   ├── safe_input.py
│   │   ├── validators.py
│   │   └── helpers.py
│   │
│   ├── web/                  # واجهات الويب
│   │   ├── dashboard.py      # لوحة التحكم Streamlit
│   │   ├── api.py            # واجهة FastAPI
│   │   ├── models.py         # نماذج البيانات
│   │   └── static/           # الملفات الثابتة
│   │       ├── css/
│   │       └── js/
│   │
│   └── tests/                # الاختبارات
│       ├── test_extractor.py
│       ├── test_checkpoints.py
│       ├── test_agent.py
│       ├── test_self_healing.py
│       ├── test_api.py
│       ├── test_utils.py
│       └── conftest.py
│
├── scripts/                  # سكربتات مساعدة
│   ├── setup.sh
│   ├── setup.bat
│   ├── run_dashboard.py
│   ├── run_api.py
│   └── run_tests.py
│
├── logs/                     # سجلات التشغيل
├── .env                      # ملف الإعدادات
├── requirements.txt          # متطلبات المشروع
├── main.py                   # نقطة الدخول الرئيسية
└── README.md                 # هذا الملف

---

## 🔧 الأوامر الخاصة

| الأمر | الوصف |
|-------|-------|
| /help | عرض المساعدة |
| /undo | التراجع عن آخر إجراء |
| /status | عرض الحالة الحالية |
| /checkpoints | عرض نقاط التفتيش |
| /export | تصدير السجلات إلى ZIP |
| /exit | إنهاء البرنامج |

---

## 📝 أمثلة الاستخدام

**1. إنشاء مشروع جديد**

المستخدم: أنشئ مشروع جديد اسمه تطبيقي

الوكيل:
تحليل الطلب: create_new
خطة التنفيذ المقترحة:
  1. فتح FlutterFlow
  2. النقر على 'New Project'
  3. تسمية المشروع بـ 'تطبيقي'
  4. اختيار قالب 'Blank App'
  5. بناء الـ UI حسب طلبك
  6. حفظ المشروع

✅ تم التنفيذ بنجاح!

**2. تعديل مشروع موجود**

المستخدم: عدل مشروع التسوق وأضف زر في الصفحة الرئيسية

الوكيل:
تحليل الطلب: edit_existing
خطة التنفيذ المقترحة:
  1. فتح FlutterFlow
  2. فتح مشروع 'التسوق'
  3. تحديد الصفحة الرئيسية
  4. إضافة زر جديد
  5. حفظ المشروع

✅ تم التنفيذ بنجاح!

**3. نسخ من Figma**

المستخدم: انسخ هذا التصميم من Figma https://figma.com/design/abc123

الوكيل:
تحليل الطلب: clone_from_figma
خطة التنفيذ المقترحة:
  1. فتح FlutterFlow
  2. فتح Figma في تبويب آخر
  3. تحليل التصميم
  4. إنشاء مشروع جديد
  5. إعادة بناء التصميم قطعة قطعة
  6. حفظ المشروع

✅ تم التنفيذ بنجاح!

---

## 🌐 واجهات الويب

**لوحة التحكم (Streamlit)**

الوصول: http://localhost:8501

الميزات:
- 📊 مقاييس فورية
- 📈 رسوم بيانية للأداء
- 💾 إدارة نقاط التفتيش
- 📁 عرض المشاريع المسجلة
- 📝 عرض السجلات في الوقت الفعلي
- ⚙️ إعدادات متقدمة

**واجهة API (FastAPI)**

الوصول: http://localhost:8000

نقاط النهاية:

| الطريقة | المسار | الوصف |
|---------|--------|-------|
| GET | / | الصفحة الرئيسية |
| GET | /health | فحص الصحة |
| GET | /status | حالة الوكيل |
| POST | /task/execute | تنفيذ مهمة |
| GET | /task/{task_id} | حالة مهمة |
| POST | /project/create | إنشاء مشروع |
| POST | /project/clone | نسخ مشروع |
| GET | /checkpoints | قائمة نقاط التفتيش |
| POST | /checkpoints | إنشاء نقطة تفتيش |
| POST | /checkpoints/undo | التراجع |
| POST | /checkpoints/redo | إعادة |
| GET | /screenshot | لقطة شاشة |
| POST | /export/logs | تصدير السجلات |

التوثيق التفاعلي: http://localhost:8000/docs

---

## 🧪 الاختبارات

تشغيل جميع الاختبارات
pytest src/tests -v

تشغيل مع تغطية الكود
pytest src/tests --cov=src --cov-report=html

تشغيل اختبار محدد
pytest src/tests/test_agent.py -v

---

## 🤝 المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات:

1. Fork المشروع
2. إنشاء فرع جديد (git checkout -b feature/amazing-feature)
3. Commit التغييرات (git commit -m 'Add amazing feature')
4. Push إلى الفرع (git push origin feature/amazing-feature)
5. فتح Pull Request

**معايير المساهمة**

- ✅ اتباع نمط الكود (PEP 8)
- ✅ كتابة اختبارات للكود الجديد
- ✅ تحديث التوثيق
- ✅ التأكد من اجتياز جميع الاختبارات

---

## 📄 الرخصة

MIT License - انظر ملف LICENSE

---

## 📞 التواصل والدعم

- 📧 البريد الإلكتروني: support@lugyflutter.com
- 🌐 الموقع: lugyflutter.com
- 🐙 GitHub: github.com/lugyflutter
- 🐦 تويتر: @lugyflutter

---

## 🙏 شكر وتقدير

- Google - Gemini API
- Streamlit - لوحة التحكم
- FastAPI - واجهة API
- OpenAI - الإلهام
- FlutterFlow - المنصة المستهدفة

---

<div align="center">

**🌟 LugyFlutter - الوكيل الذكي الذي يغير طريقة تطوير تطبيقات FlutterFlow**

صنع بـ ❤️ من فريق LugyFlutter

</div>
