"""
LugyFlutter - مدير المحددات المتقدم (Selectors Manager)
إدارة وتوليد محددات العناصر المتقدمة
"""

import re
from typing import List, Dict, Any, Optional, Union
from collections import defaultdict

from ..core.exceptions import SelectorGenerationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SelectorManager:
    """
    مدير المحددات - توليد وتحسين محددات العناصر
    الميزات:
    - توليد محددات CSS متعددة
    - توليد محددات XPath
    - تحسين المحددات بناءً على النجاح السابق
    - دمج محددات متعددة
    """
    
    def __init__(self):
        self.selector_cache = {}
        self.selector_performance = defaultdict(int)
        self.selector_blacklist = set()
        self.max_generators = 10
        
        logger.info("تم تهيئة SelectorManager")
    
    def generate_css_selectors(self, element_info: Dict[str, Any]) -> List[str]:
        """
        توليد محددات CSS متعددة للعنصر
        
        Args:
            element_info: معلومات العنصر
        
        Returns:
            List[str]: قائمة بمحددات CSS
        """
        selectors = []
        
        if not element_info:
            return selectors
        
        # محدد ID
        if element_info.get('id'):
            selectors.append(f"#{element_info['id']}")
        
        # محدد Class
        if element_info.get('className'):
            classes = element_info['className'].split()
            for cls in classes:
                if cls:
                    selectors.append(f".{cls}")
            if len(classes) > 1:
                selectors.append(f".{'.'.join(classes)}")
        
        # محدد Tag + Class
        tag = element_info.get('tagName', '')
        if tag and element_info.get('className'):
            classes = element_info['className'].split()
            for cls in classes:
                if cls:
                    selectors.append(f"{tag}.{cls}")
        
        # محدد Tag + ID
        if tag and element_info.get('id'):
            selectors.append(f"{tag}#{element_info['id']}")
        
        # محددات السمات
        if element_info.get('attributes'):
            attrs = element_info['attributes']
            for key, value in attrs.items():
                if key not in ['id', 'class', 'style'] and value:
                    # تجنب السمات الطويلة جداً
                    if len(value) < 50:
                        selectors.append(f"[{key}='{value}']")
        
        # محدد النص
        if element_info.get('text'):
            text = element_info['text'][:50]
            selectors.append(f"*:contains('{text}')")
        
        # محدد متعدد السمات
        if len(selectors) > 1:
            for i in range(min(3, len(selectors))):
                for j in range(i + 1, min(len(selectors), i + 3)):
                    combined = f"{selectors[i]}{selectors[j]}"
                    if combined not in selectors:
                        selectors.append(combined)
        
        # إزالة المكررات والفرز
        selectors = list(dict.fromkeys(selectors))
        
        # إزالة المحددات المحظورة
        selectors = [s for s in selectors if s not in self.selector_blacklist]
        
        logger.debug(f"توليد {len(selectors)} محددات CSS")
        return selectors
    
    def generate_xpath_selectors(self, element_info: Dict[str, Any]) -> List[str]:
        """
        توليد محددات XPath للعنصر
        
        Args:
            element_info: معلومات العنصر
        
        Returns:
            List[str]: قائمة بمحددات XPath
        """
        selectors = []
        
        if not element_info:
            return selectors
        
        tag = element_info.get('tagName', '')
        text = element_info.get('text', '')
        classes = element_info.get('className', '').split()
        element_id = element_info.get('id', '')
        
        # محدد بالـ ID
        if element_id:
            selectors.append(f"//*[@id='{element_id}']")
        
        # محدد بالنص
        if text:
            text_clean = text.strip()
            if len(text_clean) < 100:
                selectors.append(f"//{tag}[contains(text(),'{text_clean}')]")
                selectors.append(f"//*[contains(text(),'{text_clean}')]")
        
        # محدد بالـ Class
        if classes:
            for cls in classes:
                if cls:
                    selectors.append(f"//{tag}[@class='{cls}']")
        
        # محددات متعددة
        if classes and len(classes) >= 2:
            class_condition = ' and '.join([f"contains(@class, '{cls}')" for cls in classes])
            selectors.append(f"//{tag}[{class_condition}]")
        
        # محددات السمات
        if element_info.get('attributes'):
            attrs = element_info['attributes']
            for key, value in attrs.items():
                if key not in ['class', 'id', 'style'] and value:
                    if len(value) < 50:
                        selectors.append(f"//{tag}[@{key}='{value}']")
        
        # محددات الموضع (في حالة عدم وجود محددات أخرى)
        if not selectors and tag:
            selectors.append(f"//{tag}")
        
        # إزالة المكررات
        selectors = list(dict.fromkeys(selectors))
        
        logger.debug(f"توليد {len(selectors)} محددات XPath")
        return selectors
    
    def generate_all_selectors(self, element_info: Dict[str, Any]) -> List[str]:
        """
        توليد جميع المحددات الممكنة
        
        Args:
            element_info: معلومات العنصر
        
        Returns:
            List[str]: قائمة بجميع المحددات
        """
        all_selectors = []
        
        # محددات CSS
        css_selectors = self.generate_css_selectors(element_info)
        all_selectors.extend(css_selectors)
        
        # محددات XPath
        xpath_selectors = self.generate_xpath_selectors(element_info)
        all_selectors.extend(xpath_selectors)
        
        # إزالة المكررات
        all_selectors = list(dict.fromkeys(all_selectors))
        
        # ترتيب المحددات حسب الأداء
        all_selectors.sort(
            key=lambda s: self.selector_performance.get(s, 0),
            reverse=True
        )
        
        # تحديد عدد المحددات
        if len(all_selectors) > self.max_generators:
            all_selectors = all_selectors[:self.max_generators]
        
        logger.debug(f"توليد {len(all_selectors)} محدد كلي")
        return all_selectors
    
    def get_optimal_selectors(self, element_info: Dict[str, Any]) -> List[str]:
        """
        الحصول على المحددات المثلى للعنصر
        
        Args:
            element_info: معلومات العنصر
        
        Returns:
            List[str]: قائمة بالمحددات المثلى
        """
        selectors = self.generate_all_selectors(element_info)
        
        # ترتيب حسب الثبات المتوقع
        stable_selectors = []
        dynamic_selectors = []
        
        for selector in selectors:
            # محددات ID و Class ثابتة
            if selector.startswith('#') or selector.startswith('.'):
                stable_selectors.append(selector)
            # محددات XPath بالنص ثابتة نسبياً
            elif 'text' in selector or 'contains' in selector:
                stable_selectors.append(selector)
            else:
                dynamic_selectors.append(selector)
        
        # دمج المحددات
        optimal = stable_selectors + dynamic_selectors
        
        # إزالة المكررات
        optimal = list(dict.fromkeys(optimal))
        
        return optimal[:5]  # إرجاع أفضل 5 محددات
    
    def record_selector_performance(self, selector: str, success: bool):
        """
        تسجيل أداء المحدد
        
        Args:
            selector: المحدد المستخدم
            success: نجاح أو فشل
        """
        if success:
            self.selector_performance[selector] += 1
        else:
            self.selector_performance[selector] -= 1
            
            # إذا فشل المحدد عدة مرات، أضفه إلى القائمة السوداء
            if self.selector_performance[selector] < -3:
                self.selector_blacklist.add(selector)
                logger.debug(f"إضافة المحدد إلى القائمة السوداء: {selector}")
        
        # تنظيف المحددات ذات الأداء الضعيف
        if len(self.selector_performance) > 100:
            # إزالة المحددات الأقل استخداماً
            sorted_sel = sorted(self.selector_performance.items(), key=lambda x: x[1])
            to_remove = sorted_sel[:20]
            for sel, _ in to_remove:
                del self.selector_performance[sel]
    
    def get_selector_history(self, selector: str) -> Dict[str, Any]:
        """
        الحصول على تاريخ أداء المحدد
        
        Args:
            selector: المحدد
        
        Returns:
            Dict: تاريخ الأداء
        """
        return {
            "selector": selector,
            "performance": self.selector_performance.get(selector, 0),
            "is_blacklisted": selector in self.selector_blacklist,
            "is_optimal": self.selector_performance.get(selector, 0) > 5
        }
    
    def clear_performance_data(self):
        """مسح بيانات الأداء"""
        self.selector_performance.clear()
        self.selector_blacklist.clear()
        logger.info("تم مسح بيانات أداء المحددات")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المدير"""
        return {
            "total_selectors_tracked": len(self.selector_performance),
            "blacklisted_selectors": len(self.selector_blacklist),
            "avg_performance": (
                sum(self.selector_performance.values()) / max(len(self.selector_performance), 1)
            ),
            "cache_size": len(self.selector_cache)
        }


__all__ = ["SelectorManager"]