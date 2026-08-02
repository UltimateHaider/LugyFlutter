"""
LugyFlutter - مدير المتصفح (Browser Manager)
إدارة دورة حياة المتصفح والتفاعل مع الصفحات
"""

import asyncio
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from browser_use import Browser, BrowserConfig, BrowserContext
from browser_use.browser.browser import BrowserState

from ..core.config import config
from ..core.exceptions import (
    BrowserError,
    BrowserInitializationError,
    BrowserNavigationError,
    ElementNotFoundError,
    ElementInteractionError,
    TimeoutError
)
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


class BrowserManager:
    """
    مدير المتصفح - إدارة دورة حياة المتصفح والتفاعل مع الصفحات
    الميزات:
    - تهيئة وإدارة المتصفح
    - التنقل بين الصفحات
    - التقاط لقطات الشاشة
    - تنفيذ JavaScript
    - إدارة الجلسات والكوكيز
    - مراقبة حالة الصفحة
    """
    
    def __init__(self, headless: bool = None, user_data_dir: str = None):
        """
        تهيئة مدير المتصفح
        
        Args:
            headless: تشغيل المتصفح في وضع بدون واجهة
            user_data_dir: مسار ملف تعريف المستخدم
        """
        self.headless = headless if headless is not None else config.BROWSER_HEADLESS
        self.user_data_dir = user_data_dir or config.CHROME_USER_DATA_DIR
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_url: Optional[str] = None
        self.page_state: Optional[Dict] = None
        self.is_initialized = False
        self.screenshot_counter = 0
        
        # إحصائيات
        self.stats = {
            "navigations": 0,
            "screenshots": 0,
            "errors": 0,
            "start_time": None,
            "active_duration": 0
        }
        
        logger.info("تم تهيئة BrowserManager")
    
    async def initialize(self) -> bool:
        """
        تهيئة المتصفح
        
        Returns:
            bool: نجاح التهيئة
        """
        try:
            if self.is_initialized:
                logger.warning("المتصفح مهيأ بالفعل")
                return True
            
            print_colored("🌐 جاري تهيئة المتصفح...", Colors.CYAN)
            
            # تحديد مسار ملف تعريف Chrome
            chrome_path = self.user_data_dir or self._get_default_chrome_path()
            
            if not Path(chrome_path).exists():
                print_colored(f"⚠️ لم يتم العثور على ملف تعريف Chrome في: {chrome_path}", Colors.YELLOW)
                print_colored("💡 سيتم استخدام ملف تعريف جديد", Colors.BLUE)
                chrome_path = None
            
            # إعدادات المتصفح
            browser_config = BrowserConfig(
                headless=self.headless,
                user_data_dir=chrome_path,
                default_navigation_timeout=config.BROWSER_TIMEOUT,
                default_action_timeout=10,
                minimum_wait_page_load_time=3,
                disable_security=True,
                keep_alive=True
            )
            
            # إنشاء المتصفح
            self.browser = Browser(config=browser_config)
            
            # إنشاء سياق
            self.context = await self.browser.new_context()
            
            self.is_initialized = True
            self.stats["start_time"] = datetime.now()
            
            print_colored("✅ تم تهيئة المتصفح بنجاح", Colors.GREEN)
            logger.info("تم تهيئة المتصفح بنجاح")
            
            return True
            
        except Exception as e:
            logger.error(f"فشل تهيئة المتصفح: {e}")
            self.stats["errors"] += 1
            raise BrowserInitializationError(
                message="فشل تهيئة المتصفح",
                details={"error": str(e)}
            )
    
    def _get_default_chrome_path(self) -> str:
        """الحصول على المسار الافتراضي لـ Chrome حسب النظام"""
        system = platform.system()
        
        if system == "Windows":
            return Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"
        elif system == "Darwin":  # Mac
            return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
        else:  # Linux
            return Path.home() / ".config" / "google-chrome"
    
    async def navigate_to(self, url: str, timeout: int = None) -> bool:
        """
        التنقل إلى صفحة معينة
        
        Args:
            url: عنوان URL
            timeout: مهلة الانتظار بالثواني
        
        Returns:
            bool: نجاح التنقل
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            timeout = timeout or config.BROWSER_TIMEOUT
            
            print_colored(f"🌐 جاري التنقل إلى: {url}", Colors.BLUE)
            
            # التنقل إلى الصفحة
            await self.context.navigate_to(url, timeout=timeout)
            
            # تحديث الحالة
            self.current_url = url
            self.stats["navigations"] += 1
            
            # انتظار تحميل الصفحة
            await asyncio.sleep(2)
            
            # تحديث حالة الصفحة
            self.page_state = await self._get_page_state()
            
            print_colored(f"✅ تم التنقل إلى: {url}", Colors.GREEN)
            logger.info(f"تم التنقل إلى: {url}")
            
            return True
            
        except asyncio.TimeoutError:
            self.stats["errors"] += 1
            raise TimeoutError(
                timeout=timeout,
                message=f"انتهى وقت الانتظار للتنقل إلى {url}"
            )
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"فشل التنقل إلى {url}: {e}")
            raise BrowserNavigationError(
                url=url,
                message="فشل التنقل إلى الصفحة",
                details={"error": str(e)}
            )
    
    async def take_screenshot(self, full_page: bool = True, path: str = None) -> bytes:
        """
        التقاط لقطة شاشة للصفحة
        
        Args:
            full_page: التقاط الصفحة كاملة
            path: مسار حفظ الصورة (اختياري)
        
        Returns:
            bytes: بيانات الصورة
        """
        if not self.is_initialized:
            raise BrowserError("المتصفح غير مهيأ")
        
        try:
            screenshot = await self.context.take_screenshot(full_page=full_page)
            self.stats["screenshots"] += 1
            self.screenshot_counter += 1
            
            # حفظ الصورة إذا تم تحديد المسار
            if path:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(screenshot)
                logger.debug(f"تم حفظ لقطة الشاشة: {path}")
            
            return screenshot
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"فشل التقاط لقطة شاشة: {e}")
            raise BrowserError(
                message="فشل التقاط لقطة شاشة",
                details={"error": str(e)}
            )
    
    async def execute_js(self, script: str, *args) -> Any:
        """
        تنفيذ كود JavaScript في الصفحة
        
        Args:
            script: كود JavaScript
            *args: معاملات إضافية
        
        Returns:
            Any: نتيجة التنفيذ
        """
        if not self.is_initialized:
            raise BrowserError("المتصفح غير مهيأ")
        
        try:
            result = await self.context.evaluate(script, *args)
            logger.debug(f"تنفيذ JavaScript: {script[:50]}...")
            return result
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"فشل تنفيذ JavaScript: {e}")
            raise BrowserError(
                message="فشل تنفيذ JavaScript",
                details={"script": script[:100], "error": str(e)}
            )
    
    async def find_element(self, selector: str, timeout: int = 10) -> Optional[Dict]:
        """
        البحث عن عنصر في الصفحة
        
        Args:
            selector: محدد العنصر (CSS أو XPath)
            timeout: مهلة الانتظار
        
        Returns:
            Dict: معلومات العنصر أو None
        """
        if not self.is_initialized:
            raise BrowserError("المتصفح غير مهيأ")
        
        try:
            # تنفيذ JavaScript للعثور على العنصر
            js_code = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                const rect = element.getBoundingClientRect();
                return {{
                    x: rect.x + rect.width/2,
                    y: rect.y + rect.height/2,
                    width: rect.width,
                    height: rect.height,
                    text: element.textContent || '',
                    selector: '{selector}',
                    tagName: element.tagName,
                    className: element.className || '',
                    id: element.id || '',
                    visible: rect.width > 0 && rect.height > 0
                }};
            }}
            return null;
            """
            
            result = await self.execute_js(js_code)
            
            if result:
                logger.debug(f"تم العثور على العنصر: {selector}")
                return result
            else:
                logger.debug(f"العنصر غير موجود: {selector}")
                return None
                
        except Exception as e:
            logger.error(f"فشل البحث عن العنصر {selector}: {e}")
            return None
    
    async def wait_for_element(self, selector: str, timeout: int = 30) -> bool:
        """
        انتظار ظهور عنصر في الصفحة
        
        Args:
            selector: محدد العنصر
            timeout: مهلة الانتظار بالثواني
        
        Returns:
            bool: ظهور العنصر
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            element = await self.find_element(selector)
            if element:
                return True
            await asyncio.sleep(0.5)
        
        raise TimeoutError(
            timeout=timeout,
            message=f"انتهى وقت الانتظار للعنصر: {selector}"
        )
    
    async def click_element(self, selector: str, timeout: int = 10) -> bool:
        """
        النقر على عنصر
        
        Args:
            selector: محدد العنصر
            timeout: مهلة الانتظار
        
        Returns:
            bool: نجاح النقر
        """
        try:
            # انتظار العنصر
            await self.wait_for_element(selector, timeout)
            
            # النقر على العنصر
            js_code = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.click();
                return true;
            }}
            return false;
            """
            
            result = await self.execute_js(js_code)
            
            if result:
                logger.debug(f"تم النقر على العنصر: {selector}")
                return True
            else:
                raise ElementNotFoundError(selector)
                
        except Exception as e:
            self.stats["errors"] += 1
            raise ElementInteractionError(
                action="click",
                message=f"فشل النقر على العنصر: {selector}",
                details={"error": str(e)}
            )
    
    async def type_text(self, selector: str, text: str, delay: int = 50) -> bool:
        """
        كتابة نص في حقل إدخال
        
        Args:
            selector: محدد العنصر
            text: النص المراد كتابته
            delay: التأخير بين الأحرف (مللي ثانية)
        
        Returns:
            bool: نجاح الكتابة
        """
        try:
            # انتظار العنصر
            await self.wait_for_element(selector)
            
            # كتابة النص
            js_code = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.focus();
                element.value = '';
                element.value = `{text}`;
                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            
            result = await self.execute_js(js_code)
            
            if result:
                logger.debug(f"تم كتابة النص في: {selector}")
                return True
            else:
                raise ElementNotFoundError(selector)
                
        except Exception as e:
            self.stats["errors"] += 1
            raise ElementInteractionError(
                action="type",
                message=f"فشل كتابة النص في: {selector}",
                details={"error": str(e)}
            )
    
    async def get_page_content(self) -> str:
        """الحصول على محتوى الصفحة HTML"""
        if not self.is_initialized:
            raise BrowserError("المتصفح غير مهيأ")
        
        try:
            content = await self.execute_js("document.documentElement.outerHTML")
            return content
        except Exception as e:
            logger.error(f"فشل الحصول على محتوى الصفحة: {e}")
            return ""
    
    async def _get_page_state(self) -> Dict:
        """الحصول على حالة الصفحة الحالية"""
        try:
            state = await self.execute_js("""
                return {
                    url: window.location.href,
                    title: document.title,
                    readyState: document.readyState,
                    scrollX: window.scrollX,
                    scrollY: window.scrollY,
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight,
                    totalWidth: document.documentElement.scrollWidth,
                    totalHeight: document.documentElement.scrollHeight
                };
            """)
            return state
        except:
            return {}
    
    async def scroll_to(self, x: int = 0, y: int = 0) -> bool:
        """التمرير إلى موقع معين"""
        try:
            await self.execute_js(f"window.scrollTo({x}, {y});")
            return True
        except Exception as e:
            logger.error(f"فشل التمرير: {e}")
            return False
    
    async def scroll_to_element(self, selector: str) -> bool:
        """التمرير إلى عنصر معين"""
        try:
            js_code = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                return true;
            }}
            return false;
            """
            return await self.execute_js(js_code)
        except Exception as e:
            logger.error(f"فشل التمرير إلى العنصر {selector}: {e}")
            return False
    
    async def get_current_url(self) -> str:
        """الحصول على عنوان URL الحالي"""
        if self.current_url:
            return self.current_url
        try:
            url = await self.execute_js("window.location.href")
            self.current_url = url
            return url
        except:
            return ""
    
    async def get_page_title(self) -> str:
        """الحصول على عنوان الصفحة"""
        try:
            return await self.execute_js("document.title")
        except:
            return ""
    
    async def wait_for_page_load(self, timeout: int = 30) -> bool:
        """انتظار تحميل الصفحة بالكامل"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            state = await self._get_page_state()
            if state and state.get("readyState") == "complete":
                return True
            await asyncio.sleep(0.5)
        
        raise TimeoutError(
            timeout=timeout,
            message="انتهى وقت الانتظار لتحميل الصفحة"
        )
    
    async def refresh(self) -> bool:
        """تحديث الصفحة"""
        try:
            await self.execute_js("location.reload();")
            await self.wait_for_page_load()
            return True
        except Exception as e:
            logger.error(f"فشل تحديث الصفحة: {e}")
            return False
    
    async def go_back(self) -> bool:
        """الرجوع للصفحة السابقة"""
        try:
            await self.execute_js("history.back();")
            await self.wait_for_page_load()
            return True
        except Exception as e:
            logger.error(f"فشل الرجوع للخلف: {e}")
            return False
    
    async def close(self):
        """إغلاق المتصفح"""
        if self.browser:
            try:
                await self.browser.close()
                self.is_initialized = False
                logger.info("تم إغلاق المتصفح")
            except Exception as e:
                logger.error(f"فشل إغلاق المتصفح: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المتصفح"""
        if self.stats["start_time"]:
            duration = (datetime.now() - self.stats["start_time"]).total_seconds()
            self.stats["active_duration"] = duration
        
        return {
            **self.stats,
            "is_initialized": self.is_initialized,
            "current_url": self.current_url,
            "screenshots_taken": self.screenshot_counter,
            "headless": self.headless
        }


__all__ = ["BrowserManager"]