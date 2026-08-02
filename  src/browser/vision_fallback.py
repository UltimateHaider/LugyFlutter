"""
LugyFlutter - نظام الرؤية الحاسوبية (Vision Fallback)
خيار بديل متقدم باستخدام الرؤية الحاسوبية عند فشل المحددات التقليدية
"""

import io
import base64
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from ..core.config import config
from ..core.exceptions import VisionFallbackError
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


class VisionFallback:
    """
    نظام الرؤية الحاسوبية للكشف عن العناصر
    الميزات:
    - الكشف عن النص باستخدام Tesseract OCR
    - الكشف عن الأزرار والأشكال باستخدام OpenCV
    - التعرف على الألوان والأنماط
    - مقارنة الصور لاكتشاف التغييرات
    """
    
    def __init__(self, browser_manager):
        """
        تهيئة نظام الرؤية الحاسوبية
        
        Args:
            browser_manager: مدير المتصفح
        """
        self.browser = browser_manager
        self.last_screenshot = None
        self.previous_screenshots = []
        self.max_history = 10
        
        # إحصائيات
        self.stats = {
            "ocr_attempts": 0,
            "ocr_success": 0,
            "contour_detections": 0,
            "template_matches": 0,
            "comparisons": 0,
            "total_detections": 0
        }
        
        if not TESSERACT_AVAILABLE:
            logger.warning("pytesseract غير مثبت. سيتم تعطيل OCR.")
        
        logger.info("تم تهيئة VisionFallback")
    
    async def detect_text(self, target_text: str, region: Tuple[int, int, int, int] = None) -> Optional[Dict]:
        """
        الكشف عن نص في الصفحة باستخدام OCR
        
        Args:
            target_text: النص المطلوب الكشف عنه
            region: منطقة البحث (x, y, width, height)
        
        Returns:
            Dict: معلومات النص المكتشف
        """
        if not TESSERACT_AVAILABLE:
            logger.warning("OCR غير متاح - Tesseract غير مثبت")
            return None
        
        try:
            self.stats["ocr_attempts"] += 1
            
            # التقاط لقطة شاشة
            screenshot = await self.browser.take_screenshot()
            image = Image.open(io.BytesIO(screenshot))
            
            # قص المنطقة إذا تم تحديدها
            if region:
                x, y, w, h = region
                image = image.crop((x, y, x + w, y + h))
            
            # تحويل الصورة
            img_np = np.array(image)
            
            # معالجة الصورة
            gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # استخراج النص
            text_data = pytesseract.image_to_data(
                processed,
                output_type=pytesseract.Output.DICT,
                config='--psm 6 --oem 3'
            )
            
            # البحث عن النص المطلوب
            target_lower = target_text.lower()
            
            for i, text in enumerate(text_data['text']):
                if not text:
                    continue
                
                if target_lower in text.lower():
                    # حساب الموقع
                    x = text_data['left'][i]
                    y = text_data['top'][i]
                    w = text_data['width'][i]
                    h = text_data['height'][i]
                    
                    # إضافة إزاحة المنطقة إذا تم تحديدها
                    if region:
                        x += region[0]
                        y += region[1]
                    
                    self.stats["ocr_success"] += 1
                    self.stats["total_detections"] += 1
                    
                    return {
                        'x': x + w // 2,
                        'y': y + h // 2,
                        'width': w,
                        'height': h,
                        'text': text,
                        'confidence': text_data['conf'][i],
                        'method': 'ocr'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"فشل الكشف عن النص: {e}")
            return None
    
    async def detect_button(self, region: Tuple[int, int, int, int] = None) -> Optional[Dict]:
        """
        الكشف عن أزرار في الصفحة باستخدام OpenCV
        
        Args:
            region: منطقة البحث (x, y, width, height)
        
        Returns:
            Dict: معلومات الزر المكتشف
        """
        try:
            # التقاط لقطة شاشة
            screenshot = await self.browser.take_screenshot()
            image = Image.open(io.BytesIO(screenshot))
            img_np = np.array(image)
            
            # قص المنطقة إذا تم تحديدها
            if region:
                x, y, w, h = region
                img_np = img_np[y:y+h, x:x+w]
            
            # تحويل إلى صورة رمادية
            gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            
            # كشف الحواف
            edges = cv2.Canny(gray, 50, 150)
            
            # كشف الأضلاع
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # تصفية الأضلاع للعثور على أزرار
            buttons = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # معايير الزر التقريبية
                if 30 < w < 200 and 20 < h < 80:
                    # حساب نسبة العرض للارتفاع
                    aspect_ratio = w / h
                    if 0.5 < aspect_ratio < 3:
                        # مساحة الزر
                        area = w * h
                        if 600 < area < 16000:
                            buttons.append({
                                'x': x + w // 2,
                                'y': y + h // 2,
                                'width': w,
                                'height': h,
                                'area': area,
                                'aspect_ratio': aspect_ratio,
                                'method': 'contour'
                            })
            
            # إضافة إزاحة المنطقة إذا تم تحديدها
            if region and buttons:
                for btn in buttons:
                    btn['x'] += region[0]
                    btn['y'] += region[1]
            
            if buttons:
                self.stats["contour_detections"] += 1
                self.stats["total_detections"] += 1
                # إرجاع أكبر زر
                return max(buttons, key=lambda b: b['area'])
            
            return None
            
        except Exception as e:
            logger.error(f"فشل الكشف عن الزر: {e}")
            return None
    
    async def detect_color(self, target_color: str) -> Optional[Dict]:
        """
        الكشف عن لون معين في الصفحة
        
        Args:
            target_color: لون (HEX أو اسم)
        
        Returns:
            Dict: معلومات المنطقة الملونة
        """
        try:
            # تحويل اللون إلى RGB
            if target_color.startswith('#'):
                # HEX to RGB
                target_rgb = self._hex_to_rgb(target_color)
            else:
                # اسم اللون
                target_rgb = self._color_name_to_rgb(target_color)
            
            if not target_rgb:
                return None
            
            # التقاط لقطة شاشة
            screenshot = await self.browser.take_screenshot()
            image = Image.open(io.BytesIO(screenshot))
            img_np = np.array(image)
            
            # البحث عن اللون
            for y in range(0, img_np.shape[0], 10):
                for x in range(0, img_np.shape[1], 10):
                    pixel = img_np[y, x]
                    # حساب المسافة اللونية
                    distance = self._color_distance(pixel, target_rgb)
                    if distance < 30:  # عتبة التسامح
                        return {
                            'x': x,
                            'y': y,
                            'color': target_color,
                            'rgb': target_rgb,
                            'method': 'color_detection'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"فشل الكشف عن اللون: {e}")
            return None
    
    async def compare_screenshots(self, save_diff: bool = False) -> Dict[str, Any]:
        """
        مقارنة لقطة الشاشة الحالية مع السابقة
        
        Args:
            save_diff: حفظ صورة الفرق
        
        Returns:
            Dict: نتائج المقارنة
        """
        try:
            self.stats["comparisons"] += 1
            
            # التقاط لقطة شاشة جديدة
            current = await self.browser.take_screenshot()
            current_img = Image.open(io.BytesIO(current))
            current_np = np.array(current_img)
            
            if self.last_screenshot is None:
                self.last_screenshot = current_np
                return {
                    'has_changes': False,
                    'message': 'أول لقطة شاشة'
                }
            
            # مقارنة الصور
            prev_np = self.last_screenshot
            
            # حساب الفرق
            diff = cv2.absdiff(current_np, prev_np)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # نسبة التغيير
            changed_pixels = np.sum(diff_gray > 30)
            total_pixels = diff_gray.size
            change_ratio = changed_pixels / total_pixels
            
            # تحديث السابقة
            self.previous_screenshots.append(current_np)
            if len(self.previous_screenshots) > self.max_history:
                self.previous_screenshots.pop(0)
            
            self.last_screenshot = current_np
            
            # حفظ صورة الفرق
            diff_path = None
            if save_diff and change_ratio > 0.01:
                diff_path = f"logs/diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(diff_path, diff)
            
            return {
                'has_changes': change_ratio > 0.01,
                'change_ratio': change_ratio,
                'changed_pixels': changed_pixels,
                'total_pixels': total_pixels,
                'diff_image_path': diff_path,
                'screenshots_history': len(self.previous_screenshots)
            }
            
        except Exception as e:
            logger.error(f"فشل مقارنة الصور: {e}")
            return {
                'has_changes': False,
                'error': str(e)
            }
    
    async def find_template(self, template_path: str, threshold: float = 0.8) -> Optional[Dict]:
        """
        البحث عن قالب (Template Matching)
        
        Args:
            template_path: مسار صورة القالب
            threshold: عتبة المطابقة
        
        Returns:
            Dict: موقع القالب
        """
        try:
            self.stats["template_matches"] += 1
            
            # تحميل القالب
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"فشل تحميل القالب: {template_path}")
                return None
            
            # التقاط لقطة شاشة
            screenshot = await self.browser.take_screenshot()
            image = Image.open(io.BytesIO(screenshot))
            img_np = np.array(image)
            
            # البحث عن القالب
            result = cv2.matchTemplate(img_np, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                x, y = max_loc
                
                self.stats["total_detections"] += 1
                
                return {
                    'x': x + w // 2,
                    'y': y + h // 2,
                    'width': w,
                    'height': h,
                    'confidence': max_val,
                    'method': 'template_matching'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"فشل البحث عن القالب: {e}")
            return None
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
        """تحويل HEX إلى RGB"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except:
            return None
    
    @staticmethod
    def _color_name_to_rgb(color_name: str) -> Optional[Tuple[int, int, int]]:
        """تحويل اسم اللون إلى RGB"""
        colors = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'pink': (255, 192, 203),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'grey': (128, 128, 128),
            'أحمر': (255, 0, 0),
            'أزرق': (0, 0, 255),
            'أخضر': (0, 255, 0),
            'أصفر': (255, 255, 0),
            'أسود': (0, 0, 0),
            'أبيض': (255, 255, 255),
        }
        return colors.get(color_name.lower())
    
    @staticmethod
    def _color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """حساب المسافة بين لونين (Euclidean)"""
        return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) ** 0.5
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النظام"""
        return {
            **self.stats,
            "tesseract_available": TESSERACT_AVAILABLE,
            "history_size": len(self.previous_screenshots),
            "has_last_screenshot": self.last_screenshot is not None
        }
    
    def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        self.stats = {
            "ocr_attempts": 0,
            "ocr_success": 0,
            "contour_detections": 0,
            "template_matches": 0,
            "comparisons": 0,
            "total_detections": 0
        }


__all__ = ["VisionFallback"]