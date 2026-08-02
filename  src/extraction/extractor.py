"""
LugyFlutter - نظام استخراج المعلومات المتقدم (Information Extractor)
يجمع بين Regex و LLM مع نظام ذاكرة سياقية وتخزين مؤقت ذكي
"""

import re
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pathlib import Path
from collections import OrderedDict

from ..core.config import config
from ..core.exceptions import (
    ExtractionError,
    RegexExtractionError,
    LLMExtractionError,
    ValidationError
)
from ..utils.colors import print_colored, Colors
from ..utils.logger import get_logger

logger = get_logger(__name__)


class InformationExtractor:
    """
    مستخرج المعلومات المتقدم لـ LugyFlutter
    الميزات:
    - استخراج باستخدام Regex مع أنماط متعددة
    - خيار LLM Fallback عند فشل Regex
    - ذاكرة سياقية لتذكر المعلومات السابقة
    - تخزين مؤقت (Cache) لتحسين الأداء
    - التحقق من صحة البيانات المستخرجة
    - دعم متعدد اللغات (عربي/إنجليزي)
    """
    
    def __init__(self, llm_model=None):
        """
        تهيئة مستخرج المعلومات
        
        Args:
            llm_model: نموذج LLM للاستخدام كخيار بديل (اختياري)
        """
        self.llm_model = llm_model
        self._cache = OrderedDict()
        self._cache_max_size = config.CONTEXT_MEMORY_SIZE or 100
        self._context_memory = []
        self._memory_max_size = config.CONTEXT_MEMORY_SIZE or 100
        
        # إحصائيات الاستخراج
        self.stats = {
            "regex_attempts": 0,
            "regex_success": 0,
            "llm_attempts": 0,
            "llm_success": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_extractions": 0
        }
        
        # تعريف أنماط Regex المحسنة
        self._init_regex_patterns()
        
        logger.info("تم تهيئة InformationExtractor")
    
    def _init_regex_patterns(self):
        """تهيئة أنماط Regex المتعددة للاستخراج"""
        
        # أنماط استخراج اسم المشروع
        self.project_name_patterns = [
            # العربية
            r'(?:اسمه|اسم المشروع|المشروع اسمه|project name)\s*[:.]?\s*["\']?([^"\'.,\n\r]+?)(?:["\']|\s|$)',
            r'مشروع\s+["\']?([^"\'،\s.،\n\r]+)',
            r'عنوانه\s+["\']?([^"\'،\s.،\n\r]+)',
            r'سميته\s+["\']?([^"\'،\s.،\n\r]+)',
            r'اسم المشروع\s*[:.]?\s*([^\s،.]+)',
            
            # الإنجليزية
            r'(?:project|app|app name|name)\s+["\']?([^"\'.,\s]+)',
            r'(?:called|named|titled)\s+["\']?([^"\'.,\s]+)',
            r'project\s+["\']?([^"\'.,\s]+)',
            r'app\s+["\']?([^"\'.,\s]+)',
            
            # أنماط إضافية
            r'["\']([^"\']{2,30})["\']\s*(?:project|app)',
            r'\(([^)]{2,30})\)\s*(?:project|app)',
            r'[🐍📱]\s*([^\s]{2,30})',  # إيموجي + اسم
        ]
        
        # أنماط استخراج الروابط
        self.url_patterns = {
            "figma": [
                r'https?://(?:www\.)?figma\.com/(?:file|design)/[^\s]+',
                r'figma\.com/(?:file|design)/[^\s]+',
                r'https?://(?:www\.)?figma\.com/[^\s]+',
            ],
            "lovable": [
                r'https?://(?:www\.)?lovable\.com/[^\s]+',
                r'lovable\.com/[^\s]+',
                r'https?://(?:www\.)?lovable\.(?:ai|dev)/[^\s]+',
            ],
            "generic": [
                r'https?://[^\s]+',
                r'www\.[^\s]+',
                r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/[^\s]*',
            ]
        }
        
        # أنماط استخراج الـ Widgets
        self.widget_patterns = {
            "Column": ["عمود", "column", "vertical", "عمودي"],
            "Row": ["صف", "row", "horizontal", "أفقي"],
            "Container": ["حاوية", "container", "box", "صندوق"],
            "Text": ["نص", "text", "label", "تسمية", "كلمة"],
            "Button": ["زر", "button", "click", "نقرة", "press"],
            "Image": ["صورة", "image", "picture", "photo", "img"],
            "Stack": ["مكدس", "stack", "layer", "طبقة"],
            "Card": ["بطاقة", "card"],
            "ListTile": ["قائمة", "list", "listtile"],
            "AppBar": ["شريط", "appbar", "header", "رأس"],
            "BottomNavigationBar": ["شريط سفلي", "bottom", "footer", "تذييل"],
            "TextField": ["حقل نص", "textfield", "input", "إدخال"],
            "Dropdown": ["قائمة منسدلة", "dropdown", "select", "اختيار"],
            "Checkbox": ["مربع اختيار", "checkbox", "check"],
            "Switch": ["مفتاح", "switch", "toggle", "تبديل"],
            "Slider": ["منزلق", "slider", "range", "نطاق"],
            "ProgressBar": ["شريط تقدم", "progress", "loading", "تحميل"],
            "Icon": ["أيقونة", "icon", "symbol", "رمز"],
        }
        
        # أنماط استخراج التعديلات
        self.modification_patterns = [
            r'(?:أضف|add|insert|أدرج)\s+([^،.]+)',
            r'(?:احذف|delete|remove|احذف)\s+([^،.]+)',
            r'(?:غير|change|modify|update|غيّر)\s+([^،.]+)',
            r'(?:عدل|تعديل|edit)\s+([^،.]+)',
            r'(?:غيّر لون|change color)\s+([^،.]+)',
            r'(?:غيّر حجم|change size)\s+([^،.]+)',
            r'(?:أزل|remove)\s+([^،.]+)',
        ]
        
        # أنماط استخراج الألوان
        self.color_patterns = [
            r'#([A-Fa-f0-9]{6})',
            r'#([A-Fa-f0-9]{3})',
            r'(?:لون|color)\s+["\']?([^\s"\']+)["\']?',
            r'(?:أحمر|أزرق|أخضر|أصفر|برتقالي|بنفسجي|وردي|أسود|أبيض|رمادي)',
            r'(?:red|blue|green|yellow|orange|purple|pink|black|white|gray)',
        ]
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """الحصول على قيمة من التخزين المؤقت"""
        if key in self._cache:
            self.stats["cache_hits"] += 1
            # نقل إلى نهاية OrderedDict (تحديث الأولوية)
            self._cache.move_to_end(key)
            return self._cache[key]
        self.stats["cache_misses"] += 1
        return None
    
    def _set_in_cache(self, key: str, value: Any):
        """تخزين قيمة في التخزين المؤقت"""
        if len(self._cache) >= self._cache_max_size:
            # إزالة أقدم عنصر
            self._cache.popitem(last=False)
        self._cache[key] = value
    
    def _add_to_memory(self, key: str, value: Any):
        """إضافة معلومات إلى الذاكرة السياقية"""
        self._context_memory.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "context": self._get_current_context()
        })
        
        if len(self._context_memory) > self._memory_max_size:
            self._context_memory = self._context_memory[-self._memory_max_size:]
    
    def _get_current_context(self) -> str:
        """الحصول على السياق الحالي"""
        if self._context_memory:
            last = self._context_memory[-1]
            return f"Last: {last['key']} = {last['value']}"
        return "بداية المحادثة"
    
    def extract_project_name(self, text: str) -> Optional[str]:
        """
        استخراج اسم المشروع من النص
        
        Args:
            text: النص المراد استخراج الاسم منه
        
        Returns:
            اسم المشروع أو None
        """
        self.stats["total_extractions"] += 1
        self.stats["regex_attempts"] += 1
        
        if not text or not text.strip():
            return None
        
        # محاولة من التخزين المؤقت
        cache_key = f"project_name_{text[:50]}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # محاولة الاستخراج باستخدام Regex
        for pattern in self.project_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if match:
                name = match.group(1).strip()
                # تنظيف الاسم
                name = self._clean_project_name(name)
                if self._validate_project_name(name):
                    self.stats["regex_success"] += 1
                    self._set_in_cache(cache_key, name)
                    self._add_to_memory("project_name", name)
                    logger.debug(f"استخراج اسم المشروع: {name}")
                    return name
        
        # محاولة استخدام LLM كخيار بديل
        if self.llm_model:
            try:
                name = self._extract_with_llm(text, "اسم المشروع")
                if name and self._validate_project_name(name):
                    self.stats["llm_success"] += 1
                    self._set_in_cache(cache_key, name)
                    self._add_to_memory("project_name", name)
                    logger.debug(f"استخراج اسم المشروع باستخدام LLM: {name}")
                    return name
            except Exception as e:
                logger.warning(f"فشل استخراج الاسم باستخدام LLM: {e}")
        
        logger.debug(f"فشل استخراج اسم المشروع من: {text[:50]}...")
        return None
    
    def _clean_project_name(self, name: str) -> str:
        """تنظيف اسم المشروع من الأحرف غير المرغوب فيها"""
        # إزالة الأحرف الخاصة
        name = re.sub(r'[^\w\s\-_أ-ي]', '', name)
        # إزالة المسافات الزائدة
        name = ' '.join(name.split())
        return name.strip()
    
    def _validate_project_name(self, name: str) -> bool:
        """التحقق من صحة اسم المشروع"""
        if not name or len(name) < 2:
            return False
        if len(name) > 50:
            return False
        # التحقق من عدم وجود أحرف خطيرة
        if re.search(r'[<>/\\|:]', name):
            return False
        return True
    
    def extract_url(self, text: str, platform_name: str = "generic") -> Optional[str]:
        """
        استخراج رابط من النص
        
        Args:
            text: النص المراد استخراج الرابط منه
            platform_name: نوع المنصة (figma, lovable, generic)
        
        Returns:
            الرابط المستخرج أو None
        """
        self.stats["total_extractions"] += 1
        self.stats["regex_attempts"] += 1
        
        if not text or not text.strip():
            return None
        
        # محاولة من التخزين المؤقت
        cache_key = f"url_{platform_name}_{text[:50]}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # اختيار الأنماط المناسبة
        patterns = self.url_patterns.get(platform_name, self.url_patterns["generic"])
        
        # محاولة الاستخراج باستخدام Regex
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(0).strip()
                if self._validate_url(url):
                    self.stats["regex_success"] += 1
                    self._set_in_cache(cache_key, url)
                    self._add_to_memory("url", url)
                    logger.debug(f"استخراج رابط {platform_name}: {url}")
                    return url
        
        # محاولة استخدام LLM كخيار بديل
        if self.llm_model:
            try:
                url = self._extract_with_llm(text, f"رابط {platform_name}")
                if url and self._validate_url(url):
                    self.stats["llm_success"] += 1
                    self._set_in_cache(cache_key, url)
                    self._add_to_memory("url", url)
                    logger.debug(f"استخراج رابط باستخدام LLM: {url}")
                    return url
            except Exception as e:
                logger.warning(f"فشل استخراج الرابط باستخدام LLM: {e}")
        
        logger.debug(f"فشل استخراج رابط {platform_name} من: {text[:50]}...")
        return None
    
    def _validate_url(self, url: str) -> bool:
        """التحقق من صحة الرابط"""
        if not url:
            return False
        if not url.startswith(('http://', 'https://', 'www.')):
            return False
        if len(url) < 10:
            return False
        return True
    
    def extract_widgets(self, text: str) -> List[str]:
        """
        استخراج أسماء الـ Widgets المطلوبة من النص
        
        Args:
            text: النص المراد استخراج الـ Widgets منه
        
        Returns:
            قائمة بأسماء الـ Widgets
        """
        self.stats["total_extractions"] += 1
        self.stats["regex_attempts"] += 1
        
        if not text or not text.strip():
            return []
        
        # محاولة من التخزين المؤقت
        cache_key = f"widgets_{text[:50]}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached.copy()
        
        found_widgets = []
        text_lower = text.lower()
        
        # البحث عن الـ Widgets باستخدام المرادفات
        for widget, synonyms in self.widget_patterns.items():
            for synonym in synonyms:
                if synonym.lower() in text_lower:
                    found_widgets.append(widget)
                    break
        
        # إزالة المكررات مع الحفاظ على الترتيب
        seen = set()
        unique_widgets = []
        for w in found_widgets:
            if w not in seen:
                seen.add(w)
                unique_widgets.append(w)
        
        self.stats["regex_success"] += 1 if unique_widgets else 0
        
        if unique_widgets:
            self._set_in_cache(cache_key, unique_widgets)
            self._add_to_memory("widgets", unique_widgets)
            logger.debug(f"استخراج الـ Widgets: {unique_widgets}")
        
        return unique_widgets
    
    def extract_modifications(self, text: str) -> List[str]:
        """
        استخراج التعديلات المطلوبة من النص
        
        Args:
            text: النص المراد استخراج التعديلات منه
        
        Returns:
            قائمة بالتعديلات المطلوبة
        """
        self.stats["total_extractions"] += 1
        self.stats["regex_attempts"] += 1
        
        if not text or not text.strip():
            return []
        
        # محاولة من التخزين المؤقت
        cache_key = f"mods_{text[:50]}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached.copy()
        
        modifications = []
        
        # استخراج التعديلات باستخدام الأنماط
        for pattern in self.modification_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
            for match in matches:
                mod = match.strip()
                if mod and len(mod) > 2:
                    modifications.append(mod)
        
        # إزالة المكررات
        unique_mods = list(dict.fromkeys(modifications))
        
        self.stats["regex_success"] += 1 if unique_mods else 0
        
        if unique_mods:
            self._set_in_cache(cache_key, unique_mods)
            self._add_to_memory("modifications", unique_mods)
            logger.debug(f"استخراج التعديلات: {unique_mods}")
        
        return unique_mods
    
    def extract_colors(self, text: str) -> List[str]:
        """
        استخراج الألوان المطلوبة من النص
        
        Args:
            text: النص المراد استخراج الألوان منه
        
        Returns:
            قائمة بالألوان المطلوبة
        """
        self.stats["total_extractions"] += 1
        self.stats["regex_attempts"] += 1
        
        if not text or not text.strip():
            return []
        
        # محاولة من التخزين المؤقت
        cache_key = f"colors_{text[:50]}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached.copy()
        
        colors = []
        
        # استخراج الألوان باستخدام الأنماط
        for pattern in self.color_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
            for match in matches:
                if isinstance(match, tuple):
                    color = match[0]
                else:
                    color = match
                if color and len(color) > 1:
                    colors.append(color.strip())
        
        # إزالة المكررات
        unique_colors = list(dict.fromkeys(colors))
        
        self.stats["regex_success"] += 1 if unique_colors else 0
        
        if unique_colors:
            self._set_in_cache(cache_key, unique_colors)
            self._add_to_memory("colors", unique_colors)
            logger.debug(f"استخراج الألوان: {unique_colors}")
        
        return unique_colors
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        استخراج جميع المعلومات الممكنة من النص دفعة واحدة
        
        Args:
            text: النص المراد استخراج المعلومات منه
        
        Returns:
            قاموس يحتوي على جميع المعلومات المستخرجة
        """
        result = {
            "project_name": self.extract_project_name(text),
            "urls": {
                "figma": self.extract_url(text, "figma"),
                "lovable": self.extract_url(text, "lovable"),
                "generic": self.extract_url(text, "generic")
            },
            "widgets": self.extract_widgets(text),
            "modifications": self.extract_modifications(text),
            "colors": self.extract_colors(text),
            "raw_text": text,
            "extraction_time": datetime.now().isoformat()
        }
        
        # إضافة معلومات إضافية
        result["has_project_name"] = bool(result["project_name"])
        result["has_url"] = any(result["urls"].values())
        result["has_widgets"] = bool(result["widgets"])
        result["has_modifications"] = bool(result["modifications"])
        result["has_colors"] = bool(result["colors"])
        
        logger.info(f"استخراج شامل: {result['has_project_name']} | {result['has_url']} | {result['has_widgets']}")
        
        return result
    
    def _extract_with_llm(self, text: str, field: str) -> Optional[str]:
        """
        استخراج معلومات باستخدام LLM
        
        Args:
            text: النص المراد استخراج المعلومات منه
            field: نوع المعلومة المراد استخراجها
        
        Returns:
            المعلومة المستخرجة أو None
        """
        self.stats["llm_attempts"] += 1
        
        if not self.llm_model:
            logger.warning("نموذج LLM غير متاح")
            return None
        
        try:
            from langchain_core.prompts import PromptTemplate
            
            # بناء الـ Prompt حسب نوع المعلومة
            prompts = {
                "اسم المشروع": """
                    استخرج اسم المشروع من النص التالي.
                    أعد فقط اسم المشروع بدون أي كلمات إضافية.
                    إذا لم تجد اسم مشروع، أعد كلمة "غير محدد".
                    
                    النص: {text}
                """,
                "رابط Figma": """
                    استخرج رابط Figma من النص التالي.
                    أعد فقط الرابط الكامل بدون أي كلمات إضافية.
                    إذا لم تجد رابط Figma، أعد كلمة "غير محدد".
                    
                    النص: {text}
                """,
                "رابط Lovable": """
                    استخرج رابط Lovable من النص التالي.
                    أعد فقط الرابط الكامل بدون أي كلمات إضافية.
                    إذا لم تجد رابط Lovable، أعد كلمة "غير محدد".
                    
                    النص: {text}
                """,
                "الـ Widgets": """
                    استخرج أسماء الـ Widgets المطلوبة من النص التالي.
                    أعد فقط أسماء الـ Widgets مفصولة بفواصل.
                    إذا لم تجد Widgets، أعد كلمة "غير محدد".
                    
                    النص: {text}
                """
            }
            
            prompt_template = prompts.get(field, prompts["اسم المشروع"])
            prompt = PromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm_model
            
            response = chain.invoke({"text": text})
            result = response.content.strip()
            
            # معالجة النتيجة
            if result and result != "غير محدد":
                # تنظيف النتيجة
                result = re.sub(r'^["\']|["\']$', '', result)
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"فشل استخراج باستخدام LLM: {e}")
            raise LLMExtractionError(
                message="فشل استخراج المعلومات باستخدام النموذج اللغوي",
                details={"field": field, "error": str(e)}
            )
    
    def get_context_memory(self) -> List[Dict]:
        """الحصول على الذاكرة السياقية"""
        return self._context_memory.copy()
    
    def get_stats(self) -> Dict:
        """الحصول على إحصائيات الاستخراج"""
        return {
            **self.stats,
            "cache_size": len(self._cache),
            "memory_size": len(self._context_memory),
            "success_rate": (
                (self.stats["regex_success"] + self.stats["llm_success"]) / 
                max(self.stats["total_extractions"], 1) * 100
            )
        }
    
    def clear_cache(self):
        """مسح التخزين المؤقت"""
        self._cache.clear()
        logger.info("تم مسح التخزين المؤقت")
    
    def clear_memory(self):
        """مسح الذاكرة السياقية"""
        self._context_memory.clear()
        logger.info("تم مسح الذاكرة السياقية")
    
    def save_memory_to_file(self, file_path: str = "memory_snapshot.json"):
        """حفظ الذاكرة السياقية إلى ملف"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "memory": self._context_memory,
                "stats": self.get_stats()
            }
            Path(file_path).write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            logger.info(f"تم حفظ الذاكرة إلى: {file_path}")
            return True
        except Exception as e:
            logger.error(f"فشل حفظ الذاكرة: {e}")
            return False
    
    def load_memory_from_file(self, file_path: str = "memory_snapshot.json") -> bool:
        """تحميل الذاكرة السياقية من ملف"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"الملف غير موجود: {file_path}")
                return False
            
            data = json.loads(path.read_text(encoding='utf-8'))
            self._context_memory = data.get("memory", [])
            logger.info(f"تم تحميل الذاكرة من: {file_path}")
            return True
        except Exception as e:
            logger.error(f"فشل تحميل الذاكرة: {e}")
            return False


class RegexPatterns:
    """
    مجموعة ثابتة من أنماط Regex للاستخدام في جميع أنحاء التطبيق
    """
    
    # أنماط عامة
    EMAIL = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE = r'\+?[0-9]{1,3}[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,4}'
    
    # أنماط FlutterFlow
    PROJECT_ID = r'ff_[a-zA-Z0-9]+'
    WIDGET_ID = r'w_[a-zA-Z0-9]+'
    
    # أنماط التنسيق
    HEX_COLOR = r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'
    RGB_COLOR = r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
    
    # أنماط الوثائق
    JSON_OBJECT = r'\{[^{}]*\}'
    JSON_ARRAY = r'\[[^\[\]]*\]'
    
    @staticmethod
    def get_all_patterns() -> Dict[str, str]:
        """الحصول على جميع الأنماط"""
        return {
            "email": RegexPatterns.EMAIL,
            "phone": RegexPatterns.PHONE,
            "project_id": RegexPatterns.PROJECT_ID,
            "widget_id": RegexPatterns.WIDGET_ID,
            "hex_color": RegexPatterns.HEX_COLOR,
            "rgb_color": RegexPatterns.RGB_COLOR,
        }


# ============================================================
# دوال مساعدة للاستخدام السريع
# ============================================================

def create_extractor(llm_model=None) -> InformationExtractor:
    """دالة مساعدة لإنشاء مستخرج المعلومات"""
    return InformationExtractor(llm_model)


def quick_extract(text: str, field: str, llm_model=None) -> Optional[str]:
    """
    استخراج سريع لمعلومة محددة من النص
    
    Args:
        text: النص المراد استخراج المعلومات منه
        field: نوع المعلومة ('project_name', 'url', 'widgets', 'modifications')
        llm_model: نموذج LLM للاستخدام (اختياري)
    
    Returns:
        المعلومة المستخرجة أو None
    """
    extractor = InformationExtractor(llm_model)
    
    if field == "project_name":
        return extractor.extract_project_name(text)
    elif field == "url":
        return extractor.extract_url(text)
    elif field == "widgets":
        return extractor.extract_widgets(text)
    elif field == "modifications":
        return extractor.extract_modifications(text)
    elif field == "colors":
        return extractor.extract_colors(text)
    elif field == "all":
        return extractor.extract_all(text)
    else:
        raise ValueError(f"حقل غير معروف: {field}")


__all__ = [
    "InformationExtractor",
    "RegexPatterns",
    "create_extractor",
    "quick_extract",
]