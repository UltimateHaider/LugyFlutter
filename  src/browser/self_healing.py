"""
LugyFlutter - نظام الشفاء الذاتي للعناصر (Self-Healing Selectors)
نظام متقدم لإصلاح محددات العناصر تلقائياً عند تغير الواجهة
"""

import re
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict

from ..core.config import config
from ..core.exceptions import SelfHealingError, ElementNotFoundError
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


class SelfHealingSelector:
    """
    نظام الشفاء الذاتي للعناصر
    الميزات:
    - محاولة محددات DOM متعددة
    - البحث بالنص كخيار بديل
    - الرؤية الحاسوبية كخيار أخير
    - تعلم الأنماط وتحسين المحددات
    - تخزين المحددات الناجحة
    """
    
    def __init__(self, browser_manager):
        """
        تهيئة نظام الشفاء الذاتي
        
        Args:
            browser_manager: مدير المتصفح
        """
        self.browser = browser_manager
        self.selector_history = []
        self.healing_cache = {}
        self.learning_stats = defaultdict(int)
        self.max_history = 100
        
        # إحصائيات
        self.stats = {
            "dom_success": 0,
            "text_success": 0,
            "vision_success": 0,
            "total_attempts": 0,
            "healing_events": 0,
            "failed_healings": 0
        }
        
        # قاعدة المحددات الناجحة (سيتم تعبئتها أثناء التشغيل)
        self.successful_selectors = {}
        
        logger.info("تم تهيئة SelfHealingSelector")
    
    async def find_element(
        self,
        selectors: List[str],
        target_description: str = None,
        timeout: int = 10
    ) -> Optional[Dict]:
        """
        البحث عن عنصر باستخدام محددات متعددة مع خيارات بديلة
        
        Args:
            selectors: قائمة بمحددات CSS/XPath
            target_description: وصف نصي للعنصر (للرؤية الحاسوبية)
            timeout: مهلة الانتظار
        
        Returns:
            Dict: معلومات العنصر أو None
        """
        self.stats["total_attempts"] += 1
        
        # محاولة من التخزين المؤقت
        cache_key = self._get_cache_key(selectors, target_description)
        if cache_key in self.healing_cache:
            cached = self.healing_cache[cache_key]
            if cached and self._is_element_valid(cached):
                logger.debug(f"استخدام عنصر من التخزين المؤقت: {cache_key}")
                return cached.copy()
        
        # 1. محاولة المحددات التقليدية
        for selector in selectors:
            try:
                element = await self._try_selector(selector, timeout)
                if element:
                    self.stats["dom_success"] += 1
                    self._record_success(selector, "dom", element)
                    self._update_cache(cache_key, element)
                    return element
            except Exception as e:
                logger.debug(f"فشل المحدد {selector}: {e}")
                continue
        
        # 2. محاولة البحث بالنص
        if target_description:
            try:
                element = await self._find_by_text(target_description, timeout)
                if element:
                    self.stats["text_success"] += 1
                    self._record_success(target_description, "text", element)
                    self._update_cache(cache_key, element)
                    return element
            except Exception as e:
                logger.debug(f"فشل البحث بالنص: {e}")
        
        # 3. استخدام الرؤية الحاسوبية
        if target_description and config.VISION_FALLBACK_ENABLED:
            try:
                element = await self._find_by_vision(target_description)
                if element:
                    self.stats["vision_success"] += 1
                    self._record_success(target_description, "vision", element)
                    self._update_cache(cache_key, element)
                    return element
            except Exception as e:
                logger.debug(f"فشل الرؤية الحاسوبية: {e}")
        
        # 4. محاولة استخدام المحددات الناجحة سابقاً
        if selectors:
            for selector in selectors:
                if selector in self.successful_selectors:
                    try:
                        element = await self._try_selector(
                            self.successful_selectors[selector],
                            timeout
                        )
                        if element:
                            self.stats["healing_events"] += 1
                            self._update_cache(cache_key, element)
                            return element
                    except:
                        continue
        
        self.stats["failed_healings"] += 1
        logger.warning(f"فشل العثور على العنصر بعد جميع المحاولات")
        return None
    
    async def _try_selector(self, selector: str, timeout: int) -> Optional[Dict]:
        """محاولة استخدام محدد DOM"""
        js_code = f"""
        (function() {{
            try {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    const rect = element.getBoundingClientRect();
                    return {{
                        x: Math.round(rect.x + rect.width/2),
                        y: Math.round(rect.y + rect.height/2),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        text: element.textContent || '',
                        selector: '{selector}',
                        tagName: element.tagName.toLowerCase(),
                        className: element.className || '',
                        id: element.id || '',
                        visible: rect.width > 0 && rect.height > 0,
                        attributes: Array.from(element.attributes).reduce((acc, attr) => {{
                            acc[attr.name] = attr.value;
                            return acc;
                        }}, {{}})
                    }};
                }}
            }} catch(e) {{
                return null;
            }}
            return null;
        }})();
        """
        
        element = await self.browser.execute_js(js_code)
        return element
    
    async def _find_by_text(self, text: str, timeout: int) -> Optional[Dict]:
        """البحث عن عنصر يحتوي على نص معين"""
        js_code = f"""
        (function() {{
            try {{
                const elements = document.querySelectorAll('*');
                for (const el of elements) {{
                    if (el.textContent && el.textContent.includes('{text}')) {{
                        const rect = el.getBoundingClientRect();
                        return {{
                            x: Math.round(rect.x + rect.width/2),
                            y: Math.round(rect.y + rect.height/2),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            text: el.textContent,
                            selector: 'text:{text}',
                            tagName: el.tagName.toLowerCase(),
                            className: el.className || '',
                            id: el.id || '',
                            visible: rect.width > 0 && rect.height > 0,
                            attributes: Array.from(el.attributes).reduce((acc, attr) => {{
                                acc[attr.name] = attr.value;
                                return acc;
                            }}, {{}})
                        }};
                    }}
                }}
            }} catch(e) {{
                return null;
            }}
            return null;
        }})();
        """
        
        element = await self.browser.execute_js(js_code)
        return element
    
    async def _find_by_vision(self, target_description: str) -> Optional[Dict]:
        """
        استخدام الرؤية الحاسوبية للعثور على العنصر
        """
        try:
            # التقاط لقطة شاشة
            screenshot = await self.browser.take_screenshot()
            
            # استخدام OpenCV و Tesseract للكشف
            import cv2
            import numpy as np
            from PIL import Image
            import pytesseract
            import io
            
            # تحويل الصورة
            image = Image.open(io.BytesIO(screenshot))
            img_np = np.array(image)
            
            # الكشف عن النص
            text_data = pytesseract.image_to_data(
                img_np,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            # البحث عن النص المطلوب
            target_words = target_description.lower().split()
            
            for i, text in enumerate(text_data['text']):
                if not text:
                    continue
                    
                # التحقق من تطابق النص
                text_lower = text.lower()
                if any(word in text_lower for word in target_words):
                    x = text_data['left'][i] + text_data['width'][i] // 2
                    y = text_data['top'][i] + text_data['height'][i] // 2
                    
                    return {
                        'x': x,
                        'y': y,
                        'width': text_data['width'][i],
                        'height': text_data['height'][i],
                        'text': text,
                        'selector': 'vision:autodetect',
                        'tagName': 'unknown',
                        'className': '',
                        'id': '',
                        'visible': True,
                        'attributes': {}
                    }
            
            # محاولة الكشف عن أزرار باستخدام OpenCV
            gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 50 and h > 20:  # حجم زر تقريبي
                    return {
                        'x': x + w//2,
                        'y': y + h//2,
                        'width': w,
                        'height': h,
                        'text': '',
                        'selector': 'vision:contour',
                        'tagName': 'unknown',
                        'className': '',
                        'id': '',
                        'visible': True,
                        'attributes': {}
                    }
            
        except Exception as e:
            logger.debug(f"فشل الكشف بالرؤية: {e}")
        
        return None
    
    def _is_element_valid(self, element: Dict) -> bool:
        """التحقق من صحة العنصر"""
        if not element:
            return False
        if not element.get('visible', True):
            return False
        if element.get('width', 0) <= 0 or element.get('height', 0) <= 0:
            return False
        return True
    
    def _get_cache_key(self, selectors: List[str], description: str) -> str:
        """إنشاء مفتاح للتخزين المؤقت"""
        key = f"{'|'.join(selectors)}|{description or ''}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _update_cache(self, key: str, element: Dict):
        """تحديث التخزين المؤقت"""
        self.healing_cache[key] = element.copy()
        
        # تنظيف التخزين المؤقت
        if len(self.healing_cache) > 100:
            # إزالة أقدم العناصر
            oldest = sorted(self.healing_cache.items(), key=lambda x: x[1].get('timestamp', 0))
            for key_to_remove, _ in oldest[:20]:
                del self.healing_cache[key_to_remove]
    
    def _record_success(self, selector: str, method: str, element: Dict):
        """تسجيل محدد ناجح للتعلم"""
        record = {
            "selector": selector,
            "method": method,
            "element": element,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        self.selector_history.append(record)
        self.learning_stats[method] += 1
        
        # حفظ المحدد الناجح
        if "selector" in element:
            self.successful_selectors[selector] = element["selector"]
        
        # تنظيف التاريخ
        if len(self.selector_history) > self.max_history:
            self.selector_history = self.selector_history[-self.max_history:]
    
    def generate_alternative_selectors(self, element: Dict) -> List[str]:
        """
        توليد محددات بديلة بناءً على معلومات العنصر
        
        Args:
            element: معلومات العنصر
        
        Returns:
            List[str]: قائمة بالمحددات البديلة
        """
        selectors = []
        
        # محددات أساسية
        if element.get('id'):
            selectors.append(f"#{element['id']}")
        
        if element.get('tagName'):
            tag = element['tagName']
            if element.get('className'):
                classes = element['className'].split()
                for cls in classes:
                    if cls:
                        selectors.append(f"{tag}.{cls}")
        
        if element.get('text'):
            text = element['text'][:50]
            selectors.append(f"*[text*='{text}']")
            selectors.append(f"*:contains('{text}')")
        
        if element.get('attributes'):
            attrs = element['attributes']
            for key, value in attrs.items():
                if key not in ['class', 'id'] and value:
                    selectors.append(f"[{key}='{value}']")
        
        # محددات XPath
        if element.get('tagName'):
            tag = element['tagName']
            text = element.get('text', '')[:50]
            if text:
                selectors.append(f"//{tag}[contains(text(),'{text}')]")
        
        return selectors
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الشفاء الذاتي"""
        total = self.stats["total_attempts"]
        success_rate = (
            (self.stats["dom_success"] + self.stats["text_success"] + self.stats["vision_success"]) /
            max(total, 1) * 100
        )
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%",
            "cache_size": len(self.healing_cache),
            "history_size": len(self.selector_history),
            "learning_stats": dict(self.learning_stats),
            "successful_selectors": len(self.successful_selectors)
        }
    
    def clear_cache(self):
        """مسح التخزين المؤقت"""
        self.healing_cache.clear()
        logger.info("تم مسح تخزين الشفاء الذاتي")
    
    def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        self.stats = {
            "dom_success": 0,
            "text_success": 0,
            "vision_success": 0,
            "total_attempts": 0,
            "healing_events": 0,
            "failed_healings": 0
        }
        self.learning_stats.clear()
        logger.info("تم إعادة تعيين إحصائيات الشفاء الذاتي")


__all__ = ["SelfHealingSelector"]