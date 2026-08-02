"""
LugyFlutter - نظام LLM Fallback لاستخراج المعلومات
خيار بديل عند فشل استخراج المعلومات باستخدام Regex
"""

import logging
from typing import Optional, Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..core.exceptions import LLMExtractionError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMFallback:
    """
    نظام استخراج المعلومات باستخدام LLM كخيار بديل
    """
    
    def __init__(self, llm_model):
        """
        تهيئة نظام LLM Fallback
        
        Args:
            llm_model: نموذج LLM المستخدم
        """
        self.llm_model = llm_model
        self.parser = StrOutputParser()
        self.templates = self._init_templates()
        self.stats = {
            "attempts": 0,
            "success": 0,
            "failures": 0
        }
        
        logger.info("تم تهيئة LLM Fallback")
    
    def _init_templates(self) -> Dict[str, PromptTemplate]:
        """تهيئة قوالب الـ Prompts"""
        return {
            "project_name": PromptTemplate.from_template("""
                استخرج اسم المشروع من النص التالي.
                أعد فقط اسم المشروع بدون أي كلمات إضافية.
                إذا لم تجد اسم مشروع، أعد كلمة "غير محدد".
                
                النص: {text}
            """),
            
            "url_figma": PromptTemplate.from_template("""
                استخرج رابط Figma من النص التالي.
                أعد فقط الرابط الكامل بدون أي كلمات إضافية.
                إذا لم تجد رابط Figma، أعد كلمة "غير محدد".
                
                النص: {text}
            """),
            
            "url_lovable": PromptTemplate.from_template("""
                استخرج رابط Lovable من النص التالي.
                أعد فقط الرابط الكامل بدون أي كلمات إضافية.
                إذا لم تجد رابط Lovable، أعد كلمة "غير محدد".
                
                النص: {text}
            """),
            
            "widgets": PromptTemplate.from_template("""
                استخرج أسماء الـ Widgets المطلوبة من النص التالي.
                أعد فقط أسماء الـ Widgets مفصولة بفواصل.
                إذا لم تجد Widgets، أعد كلمة "غير محدد".
                
                الـ Widgets المتاحة: Column, Row, Container, Text, Button, Image, Stack, Card, ListTile, AppBar, BottomNavigationBar, TextField, Dropdown, Checkbox, Switch, Slider, ProgressBar, Icon
                
                النص: {text}
            """),
            
            "modifications": PromptTemplate.from_template("""
                استخرج التعديلات المطلوبة من النص التالي.
                أعد فقط التعديلات مفصولة بفواصل.
                إذا لم تجد تعديلات، أعد كلمة "غير محدد".
                
                النص: {text}
            """),
            
            "colors": PromptTemplate.from_template("""
                استخرج الألوان المطلوبة من النص التالي.
                أعد فقط الألوان مفصولة بفواصل (HEX codes أو أسماء الألوان).
                إذا لم تجد ألوان، أعد كلمة "غير محدد".
                
                النص: {text}
            """),
            
            "analysis": PromptTemplate.from_template("""
                حلل النص التالي واستخرج جميع المعلومات المهمة المتعلقة بـ FlutterFlow.
                
                استخرج:
                1. اسم المشروع
                2. الروابط (Figma, Lovable, مواقع أخرى)
                3. الـ Widgets المطلوبة
                4. التعديلات المطلوبة
                5. الألوان المطلوبة
                
                أعد النتيجة بتنسيق JSON مع المفاتيح التالية:
                - project_name
                - urls (كائن يحتوي على figma, lovable, other)
                - widgets (مصفوفة)
                - modifications (مصفوفة)
                - colors (مصفوفة)
                
                النص: {text}
            """)
        }
    
    def extract(self, text: str, field: str) -> Optional[str]:
        """
        استخراج معلومات من النص باستخدام LLM
        
        Args:
            text: النص المراد استخراج المعلومات منه
            field: نوع المعلومة (project_name, url_figma, url_lovable, widgets, modifications, colors)
        
        Returns:
            المعلومة المستخرجة أو None
        """
        self.stats["attempts"] += 1
        
        if not self.llm_model:
            logger.warning("نموذج LLM غير متاح")
            return None
        
        try:
            # اختيار القالب المناسب
            template = self.templates.get(field)
            if not template:
                logger.warning(f"قالب غير موجود للحقل: {field}")
                return None
            
            # إنشاء السلسلة
            chain = template | self.llm_model | self.parser
            
            # تنفيذ الاستخراج
            result = chain.invoke({"text": text})
            
            # معالجة النتيجة
            if result and result != "غير محدد":
                # تنظيف النتيجة
                result = result.strip()
                # إزالة علامات الاقتباس الزائدة
                result = result.strip('"\'')
                
                self.stats["success"] += 1
                logger.debug(f"استخراج ناجح باستخدام LLM - {field}: {result}")
                return result
            
            self.stats["failures"] += 1
            return None
            
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"فشل استخراج باستخدام LLM - {field}: {e}")
            raise LLMExtractionError(
                message=f"فشل استخراج {field} باستخدام LLM",
                details={"field": field, "error": str(e)}
            )
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        استخراج جميع المعلومات من النص دفعة واحدة
        
        Args:
            text: النص المراد استخراج المعلومات منه
        
        Returns:
            قاموس يحتوي على جميع المعلومات المستخرجة
        """
        self.stats["attempts"] += 1
        
        try:
            template = self.templates["analysis"]
            chain = template | self.llm_model | self.parser
            
            result = chain.invoke({"text": text})
            
            if result and result != "غير محدد":
                import json
                try:
                    data = json.loads(result)
                    self.stats["success"] += 1
                    logger.info("استخراج شامل ناجح باستخدام LLM")
                    return data
                except json.JSONDecodeError:
                    logger.warning("فشل تحليل JSON من LLM")
                    return {"raw": result}
            
            self.stats["failures"] += 1
            return {}
            
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"فشل الاستخراج الشامل باستخدام LLM: {e}")
            raise LLMExtractionError(
                message="فشل الاستخراج الشامل باستخدام LLM",
                details={"error": str(e)}
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النظام"""
        total = self.stats["attempts"]
        success_rate = (
            (self.stats["success"] / total * 100) if total > 0 else 0
        )
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%",
            "is_available": bool(self.llm_model)
        }


__all__ = ["LLMFallback"]