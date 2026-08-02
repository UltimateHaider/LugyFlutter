# LugyFlutter API - التوثيق الكامل

## نظرة عامة

LugyFlutter API هي واجهة برمجية (REST API) تسمح بالتفاعل مع وكيل LugyFlutter الذكي عبر HTTP. تم بناء API باستخدام **FastAPI** وتوفر نقاط نهاية متكاملة لإدارة المهام والمشاريع ونقاط التفتيش.

- **الإصدار:** 2.0.0
- **التوثيق التفاعلي:** /docs (Swagger UI)
- **التوثيق البديل:** /redoc (ReDoc)
- **المضيف الافتراضي:** http://localhost:8000

---

## التوثيق التفاعلي

بعد تشغيل الخادم، يمكنك زيارة:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## المصادقة

API يستخدم **Bearer Token** للمصادقة (اختياري). يمكن تفعيل المصادقة في الإعدادات:

```
Authorization: Bearer <your_token_here>
```

حالياً، المصادقة غير مفعلة افتراضياً لتسهيل الاختبار. يمكن تفعيلها في المستقبل.

---

## نقاط النهاية

### 1. الصفحة الرئيسية

**GET /** - عرض معلومات عامة عن API

**الاستجابة:**
{
  "name": "LugyFlutter API",
  "version": "2.0.0",
  "status": "running",
  "description": "الوكيل الذكي المتخصص في FlutterFlow",
  "docs": "/docs",
  "health": "/health"
}

**رمز الحالة:** 200 OK

---

### 2. فحص الصحة

**GET /health** - التحقق من صحة الخدمة وحالة الوكيل

**الاستجابة:**
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-15T10:00:00",
  "system_info": {
    "system": "Linux",
    "python": "3.10.0",
    "cpu_count": 8,
    "memory_total": "16.0 GB"
  },
  "agent_initialized": true
}

**رمز الحالة:** 200 OK

---

### 3. حالة الوكيل

**GET /status** - الحصول على حالة LugyFlutter الحالية

**الاستجابة:**
{
  "status": "running",
  "name": "LugyFlutter",
  "version": "2.0.0",
  "context": {
    "project_name": "MyApp",
    "current_view": "builder",
    "current_step": 5
  },
  "stats": {
    "tasks_executed": 10,
    "successful_tasks": 8,
    "failed_tasks": 2
  },
  "checkpoints": 5,
  "projects": 3,
  "browser_ready": true
}

**رمز الحالة:** 200 OK

---

### 4. تنفيذ مهمة

**POST /task/execute** - تنفيذ مهمة جديدة

**طلب:**
{
  "user_input": "أنشئ مشروع جديد اسمه تطبيقي",
  "mode": "full_interactive",
  "auto_execute": false
}

**معاملات الطلب:**

| المعامل | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| user_input | string | نعم | طلب المستخدم (1-1000 حرف) |
| mode | string | لا | وضع التفاعل (auto, confirm_steps, ask_clarifications, full_interactive, debug) |
| project_name | string | لا | اسم المشروع (اختياري) |
| auto_execute | boolean | لا | تنفيذ تلقائي بدون تأكيد |

**أوضاع التفاعل:**

| الوضع | الوصف |
|-------|-------|
| auto | تنفيذ تلقائي بالكامل |
| confirm_steps | تأكيد قبل كل خطوة |
| ask_clarifications | سؤال عند الغموض فقط |
| full_interactive | تفاعل كامل |
| debug | وضع التصحيح خطوة بخطوة |

**الاستجابة:**
{
  "task_id": "task_20240115_100000",
  "status": "started",
  "result": null,
  "timestamp": "2024-01-15T10:00:00"
}

**رمز الحالة:** 200 OK

---

### 5. حالة مهمة

**GET /task/{task_id}** - الحصول على حالة مهمة محددة

**الاستجابة:**
{
  "task_id": "task_20240115_100000",
  "status": "completed",
  "result": "تم إنشاء المشروع بنجاح",
  "error": null,
  "progress": 100,
  "steps": [
    {"step": 1, "description": "فتح FlutterFlow", "status": "completed"},
    {"step": 2, "description": "إنشاء المشروع", "status": "completed"}
  ],
  "started_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:30",
  "completed_at": "2024-01-15T10:00:30"
}

**حالات المهمة:**

| الحالة | الوصف |
|--------|-------|
| pending | في انتظار التنفيذ |
| running | جاري التنفيذ |
| completed | تم التنفيذ بنجاح |
| failed | فشل التنفيذ |

**رمز الحالة:** 200 OK, 404 Not Found

---

### 6. انتظار مهمة

**GET /task/{task_id}/wait** - انتظار اكتمال مهمة

**معاملات الاستعلام:**

| المعامل | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| timeout | integer | لا | مهلة الانتظار بالثواني (افتراضي: 60) |

**الاستجابة:** نفس استجابة /task/{task_id}

**رمز الحالة:** 200 OK, 404 Not Found, 408 Request Timeout

---

### 7. قائمة المهام

**GET /tasks** - الحصول على قائمة المهام

**معاملات الاستعلام:**

| المعامل | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| limit | integer | لا | عدد المهام (1-100، افتراضي: 20) |
| status | string | لا | تصفية حسب الحالة |

**الاستجابة:**
[
  {
    "task_id": "task_20240115_100000",
    "status": "completed",
    "started_at": "2024-01-15T10:00:00"
  },
  {
    "task_id": "task_20240115_100100",
    "status": "running",
    "started_at": "2024-01-15T10:01:00"
  }
]

**رمز الحالة:** 200 OK

---

### 8. إنشاء مشروع

**POST /project/create** - إنشاء مشروع جديد في FlutterFlow

**طلب:**
{
  "name": "تطبيقي",
  "template": "blank",
  "description": "مشروع تطبيق جديد"
}

**معاملات الطلب:**

| المعامل | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| name | string | نعم | اسم المشروع (2-50 حرف) |
| template | string | لا | قالب المشروع (blank, app, game) |
| description | string | لا | وصف المشروع |

**الاستجابة:**
{
  "status": "success",
  "message": "تم إنشاء المشروع تطبيقي بنجاح",
  "project": {
    "name": "تطبيقي",
    "template": "blank",
    "description": "مشروع تطبيق جديد",
    "created_at": "2024-01-15T10:00:00"
  }
}

**رمز الحالة:** 200 OK, 422 Validation Error

---

### 9. نسخ مشروع

**POST /project/clone** - نسخ مشروع من مصدر خارجي

**طلب:**
{
  "source_url": "https://figma.com/design/abc123",
  "source_type": "figma",
  "project_name": "تطبيق المطعم"
}

**معاملات الطلب:**

| المعامل | النوع | مطلوب | الوصف |
|---------|-------|-------|-------|
| source_url | string | نعم | رابط المصدر (Figma/Lovable) |
| source_type | string | نعم | نوع المصدر (figma, lovable) |
| project_name | string | نعم | اسم المشروع الجديد (2-50 حرف) |

**الاستجابة:**
{
  "status": "success",
  "message": "تم نسخ المشروع من figma بنجاح",
  "project": {
    "name": "تطبيق المطعم",
    "source_type": "figma",
    "source_url": "https://figma.com/design/abc123",
    "created_at": "2024-01-15T10:00:00"
  }
}

**رمز الحالة:** 200 OK, 422 Validation Error

---

### 10. قائمة نقاط التفتيش

**GET /checkpoints** - الحصول على قائمة نقاط التفتيش

**الاستجابة:**
[
  {
    "checkpoint_id": "cp_20240115_100000",
    "step": 1,
    "description": "نقطة بداية المشروع",
    "timestamp": "2024-01-15T10:00:00",
    "has_screenshot": true
  },
  {
    "checkpoint_id": "cp_20240115_100100",
    "step": 2,
    "description": "بعد إضافة الـ Widgets",
    "timestamp": "2024-01-15T10:01:00",
    "has_screenshot": true
  }
]

**رمز الحالة:** 200 OK

---

### 11. إنشاء نقطة تفتيش

**POST /checkpoints** - إنشاء نقطة تفتيش جديدة

**طلب:**
{
  "description": "نقطة تفتيش بعد إنشاء المشروع",
  "metadata": {
    "project": "تطبيقي",
    "widgets": ["Column", "Text"]
  }
}

**الاستجابة:**
{
  "status": "success",
  "checkpoint_id": "cp_20240115_100200",
  "message": "تم حفظ نقطة التفتيش بنجاح"
}

**رمز الحالة:** 200 OK

---

### 12. التراجع عن نقطة تفتيش

**POST /checkpoints/undo** - التراجع عن آخر إجراء

**الاستجابة:**
{
  "status": "success",
  "checkpoint": {
    "id": "cp_20240115_100000",
    "description": "نقطة بداية المشروع",
    "step": 1
  },
  "message": "تم التراجع بنجاح"
}

**رمز الحالة:** 200 OK, 404 Not Found

---

### 13. إعادة التقدم

**POST /checkpoints/redo** - إعادة التقدم إلى نقطة تفتيش تالية

**الاستجابة:**
{
  "status": "success",
  "checkpoint": {
    "id": "cp_20240115_100100",
    "description": "بعد إضافة الـ Widgets",
    "step": 2
  },
  "message": "تم الإعادة بنجاح"
}

**رمز الحالة:** 200 OK, 404 Not Found

---

### 14. لقطة شاشة

**GET /screenshot** - الحصول على آخر لقطة شاشة

**الاستجابة:** صورة PNG

**الرؤوس:**
- Content-Type: image/png
- Content-Disposition: attachment; filename=screenshot_20240115_100000.png

**رمز الحالة:** 200 OK, 503 Service Unavailable

---

### 15. تصدير السجلات

**POST /export/logs** - تصدير السجلات إلى ملف ZIP

**الاستجابة:**
{
  "status": "success",
  "file_path": "lugy_logs_20240115_100000.zip",
  "message": "تم تصدير السجلات بنجاح"
}

**رمز الحالة:** 200 OK, 404 Not Found

---

### 16. تحميل السجلات

**GET /export/logs/download** - تحميل ملف السجلات المصدر

**الاستجابة:** ملف ZIP

**رمز الحالة:** 200 OK, 404 Not Found, 500 Internal Server Error

---

### 17. إعادة تشغيل الوكيل

**POST /agent/restart** - إعادة تشغيل LugyFlutter

**الاستجابة:**
{
  "status": "success",
  "message": "تم إعادة تشغيل الوكيل بنجاح"
}

**رمز الحالة:** 200 OK, 500 Internal Server Error

---

## أكواد الأخطاء

| الرمز | الوصف |
|-------|-------|
| 400 | طلب غير صحيح |
| 404 | المورد غير موجود |
| 408 | انتهت مهلة الانتظار |
| 422 | خطأ في التحقق من البيانات |
| 500 | خطأ في الخادم الداخلي |
| 503 | الخدمة غير متاحة |

---

## أمثلة الاستخدام

### باستخدام cURL

**1. تنفيذ مهمة:**

curl -X POST http://localhost:8000/task/execute \
  -H "Content-Type: application/json" \
  -d '{"user_input": "أنشئ مشروع جديد اسمه تطبيقي", "mode": "full_interactive"}'

**2. الحصول على حالة مهمة:**

curl http://localhost:8000/task/task_20240115_100000

**3. إنشاء مشروع:**

curl -X POST http://localhost:8000/project/create \
  -H "Content-Type: application/json" \
  -d '{"name": "تطبيقي", "template": "blank"}'

**4. الحصول على لقطة شاشة:**

curl http://localhost:8000/screenshot --output screenshot.png

---

### باستخدام Python

import requests

# تنفيذ مهمة
response = requests.post(
    "http://localhost:8000/task/execute",
    json={
        "user_input": "أنشئ مشروع جديد اسمه تطبيقي",
        "mode": "full_interactive"
    }
)
task_id = response.json()["task_id"]

# الحصول على حالة المهمة
response = requests.get(f"http://localhost:8000/task/{task_id}")
print(response.json())

# إنشاء مشروع
response = requests.post(
    "http://localhost:8000/project/create",
    json={
        "name": "تطبيقي",
        "template": "blank"
    }
)
print(response.json())

# الحصول على لقطة شاشة
response = requests.get("http://localhost:8000/screenshot")
with open("screenshot.png", "wb") as f:
    f.write(response.content)

---

### باستخدام JavaScript (Fetch API)

// تنفيذ مهمة
fetch("http://localhost:8000/task/execute", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        user_input: "أنشئ مشروع جديد اسمه تطبيقي",
        mode: "full_interactive"
    })
})
.then(response => response.json())
.then(data => {
    console.log("Task ID:", data.task_id);
    return fetch(`http://localhost:8000/task/${data.task_id}`);
})
.then(response => response.json())
.then(data => {
    console.log("Task Status:", data);
})
.catch(error => console.error("Error:", error));

// إنشاء مشروع
fetch("http://localhost:8000/project/create", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        name: "تطبيقي",
        template: "blank"
    })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error("Error:", error));

---

## نصائح الاستخدام

1. **المهلة:** استخدم /task/{task_id}/wait مع قيمة timeout مناسبة للانتظار حتى اكتمال المهام الطويلة.
2. **نقاط التفتيش:** استخدم نقاط التفتيش لحفظ حالة المشروع بشكل دوري للرجوع إليها عند الحاجة.
3. **السجلات:** قم بتصدير السجلات بشكل دوري لتحليل الأخطاء وتتبع الأداء.
4. **لقطات الشاشة:** استخدم لقطات الشاشة لمتابعة تقدم الوكيل بصرياً.
5. **الأخطاء:** تحقق من رسائل الخطأ التفصيلية في الاستجابة لتشخيص المشاكل.

---

## التحديثات والإصدارات

- **الإصدار 2.0.0:** الإصدار الحالي مع جميع الميزات المتقدمة
- **الإصدار 1.0.0:** الإصدار الأولي مع الميزات الأساسية

---

<div align="center">

**🌟 LugyFlutter API - واجهة برمجية قوية للوكيل الذكي**

صنع بـ ❤️ من فريق LugyFlutter

</div>
