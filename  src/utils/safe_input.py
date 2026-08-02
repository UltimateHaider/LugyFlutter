"""
LugyFlutter - نظام الإدخال الآمن (Safe Input)
معالجة متقدمة للإدخال من المستخدم مع حماية من الأخطاء
"""

import sys
import re
from typing import Optional, List, Any, Callable
from datetime import datetime

from .colors import print_colored, Colors


class SafeInput:
    """
    نظام الإدخال الآمن والمتقدم
    الميزات:
    - حماية من EOFError و KeyboardInterrupt
    - دعم القيم الافتراضية
    - التحقق من صحة الإدخال
    - دعم قوائم الخيارات
    - دعم الإدخال المتعدد
    - تاريخ الإدخالات
    """
    
    # تاريخ الإدخالات للتراجع
    _history: List[str] = []
    _history_limit: int = 100
    _history_index: int = -1
    
    @classmethod
    def get_input(
        cls,
        prompt: str = "",
        default: str = "",
        allow_empty: bool = False,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "إدخال غير صالح، حاول مرة أخرى",
        max_attempts: int = 3,
        history: bool = True
    ) -> str:
        """
        الحصول على إدخال من المستخدم مع حماية من الأخطاء
        
        Args:
            prompt: نص السؤال
            default: القيمة الافتراضية
            allow_empty: السماح بإدخال فارغ
            validator: دالة للتحقق من صحة الإدخال
            error_message: رسالة الخطأ
            max_attempts: عدد المحاولات القصوى
            history: حفظ الإدخال في التاريخ
        
        Returns:
            str: إدخال المستخدم
        """
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # عرض المطالبة مع القيمة الافتراضية
                full_prompt = prompt
                if default and not allow_empty:
                    full_prompt += f" (افتراضي: {default})"
                full_prompt += " "
                
                # الحصول على الإدخال
                response = input(full_prompt).strip()
                
                # استخدام القيمة الافتراضية إذا كان الإدخال فارغاً
                if not response and default:
                    response = default
                
                # التحقق من السماح بالإدخال الفارغ
                if not response and not allow_empty:
                    print_colored("⚠️ الإدخال لا يمكن أن يكون فارغاً", Colors.YELLOW)
                    attempts += 1
                    continue
                
                # التحقق من الصحة باستخدام الـ Validator
                if validator and not validator(response):
                    print_colored(f"⚠️ {error_message}", Colors.YELLOW)
                    attempts += 1
                    continue
                
                # حفظ في التاريخ
                if history and response:
                    cls._add_to_history(response)
                
                return response
                
            except EOFError:
                # بيئة غير تفاعلية
                print_colored("\n⚠️ بيئة غير تفاعلية، استخدام القيمة الافتراضية", Colors.YELLOW)
                return default if default else ""
                
            except KeyboardInterrupt:
                # المستخدم قام بقطع البرنامج
                print_colored("\n\n👋 تم إلغاء العملية بواسطة المستخدم.", Colors.RED)
                return "إلغاء تلقائي"
                
            except Exception as e:
                print_colored(f"⚠️ خطأ في الإدخال: {e}", Colors.RED)
                attempts += 1
        
        print_colored(f"❌ فشل الإدخال بعد {max_attempts} محاولات", Colors.RED)
        return default if default else ""
    
    @classmethod
    def get_choice(
        cls,
        prompt: str,
        options: List[str],
        default: Optional[str] = None,
        allow_custom: bool = False,
        case_sensitive: bool = False
    ) -> str:
        """
        الحصول على اختيار من قائمة خيارات
        
        Args:
            prompt: نص السؤال
            options: قائمة الخيارات المتاحة
            default: الخيار الافتراضي
            allow_custom: السماح بإدخال نص مخصص
            case_sensitive: تمييز حالة الأحرف
        
        Returns:
            str: الخيار المختار
        """
        if not options:
            return cls.get_input(prompt, default=default)
        
        # عرض الخيارات
        print_colored(f"\n{prompt}", Colors.CYAN)
        for i, opt in enumerate(options, 1):
            print_colored(f"   {i}. {opt}", Colors.BLUE)
        
        if allow_custom:
            print_colored("   أو اكتب نصاً مخصصاً", Colors.MAGENTA)
        
        if default:
            print_colored(f"   (افتراضي: {default})", Colors.YELLOW)
        
        while True:
            choice = cls.get_input("اختر رقم (أو اكتب النص): ", default=default, allow_empty=True)
            
            if not choice and default:
                return default
            
            # محاولة الرقم
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            except ValueError:
                pass
            
            # محاولة النص
            if not case_sensitive:
                choice_lower = choice.lower()
                for opt in options:
                    if opt.lower() == choice_lower:
                        return opt
            else:
                if choice in options:
                    return choice
            
            # السماح بالنص المخصص
            if allow_custom:
                if choice.strip():
                    return choice.strip()
            
            print_colored(f"⚠️ خيار غير صحيح. الخيارات المتاحة: {', '.join(options)}", Colors.YELLOW)
    
    @classmethod
    def get_multiple_input(
        cls,
        prompt: str,
        count: int,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "إدخال غير صالح"
    ) -> List[str]:
        """
        الحصول على عدة مدخلات متتالية
        
        Args:
            prompt: نص السؤال
            count: عدد المدخلات المطلوبة
            validator: دالة للتحقق من صحة الإدخال
            error_message: رسالة الخطأ
        
        Returns:
            List[str]: قائمة المدخلات
        """
        results = []
        
        for i in range(count):
            response = cls.get_input(
                f"{prompt} {i+1}/{count}: ",
                validator=validator,
                error_message=error_message
            )
            results.append(response)
        
        return results
    
    @classmethod
    def get_confirmation(cls, prompt: str = "هل أنت متأكد؟", default: str = "لا") -> bool:
        """
        الحصول على تأكيد من المستخدم
        
        Args:
            prompt: نص السؤال
            default: الإجابة الافتراضية
        
        Returns:
            bool: True إذا وافق المستخدم
        """
        response = cls.get_choice(
            prompt,
            ["نعم", "لا"],
            default=default
        )
        return response == "نعم"
    
    @classmethod
    def get_password(cls, prompt: str = "كلمة المرور: ", confirm: bool = False) -> str:
        """
        الحصول على كلمة مرور من المستخدم
        
        Args:
            prompt: نص السؤال
            confirm: طلب تأكيد كلمة المرور
        
        Returns:
            str: كلمة المرور
        """
        try:
            import getpass
            password = getpass.getpass(prompt)
            
            if confirm:
                confirm_pwd = getpass.getpass("تأكيد كلمة المرور: ")
                if password != confirm_pwd:
                    print_colored("⚠️ كلمة المرور غير متطابقة", Colors.RED)
                    return cls.get_password(prompt, confirm)
            
            return password
            
        except (ImportError, EOFError):
            # في حالة عدم توفر getpass
            return cls.get_input(prompt)
    
    @classmethod
    def get_yes_no(cls, prompt: str, default: Optional[bool] = None) -> bool:
        """
        الحصول على إجابة نعم/لا
        
        Args:
            prompt: نص السؤال
            default: القيمة الافتراضية (True/False)
        
        Returns:
            bool: True لنعم، False للا
        """
        options = ["نعم", "لا"]
        
        if default is True:
            default_str = "نعم"
        elif default is False:
            default_str = "لا"
        else:
            default_str = None
        
        response = cls.get_choice(prompt, options, default=default_str)
        return response == "نعم"
    
    @classmethod
    def get_number(
        cls,
        prompt: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        default: Optional[float] = None,
        allow_float: bool = True
    ) -> Optional[float]:
        """
        الحصول على رقم من المستخدم
        
        Args:
            prompt: نص السؤال
            min_val: الحد الأدنى
            max_val: الحد الأقصى
            default: القيمة الافتراضية
            allow_float: السماح بالأرقام العشرية
        
        Returns:
            Optional[float]: الرقم المدخل
        """
        def validator(value: str) -> bool:
            try:
                num = float(value) if allow_float else int(value)
                
                if min_val is not None and num < min_val:
                    return False
                if max_val is not None and num > max_val:
                    return False
                return True
            except ValueError:
                return False
        
        error_msg = f"الرجاء إدخال رقم"
        if min_val is not None:
            error_msg += f" >= {min_val}"
        if max_val is not None:
            error_msg += f" <= {max_val}"
        
        response = cls.get_input(
            prompt,
            default=str(default) if default is not None else "",
            validator=validator,
            error_message=error_msg
        )
        
        if not response:
            return default
        
        try:
            return float(response) if allow_float else int(response)
        except ValueError:
            return default
    
    @classmethod
    def get_int(cls, prompt: str, min_val: Optional[int] = None, max_val: Optional[int] = None, default: Optional[int] = None) -> Optional[int]:
        """الحصول على عدد صحيح"""
        return cls.get_number(prompt, min_val, max_val, default, allow_float=False)
    
    @classmethod
    def get_float(cls, prompt: str, min_val: Optional[float] = None, max_val: Optional[float] = None, default: Optional[float] = None) -> Optional[float]:
        """الحصول على رقم عشري"""
        return cls.get_number(prompt, min_val, max_val, default, allow_float=True)
    
    @classmethod
    def get_email(cls, prompt: str = "البريد الإلكتروني: ", default: str = "") -> str:
        """الحصول على بريد إلكتروني صحيح"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        def validator(value: str) -> bool:
            return bool(re.match(email_pattern, value))
        
        return cls.get_input(
            prompt,
            default=default,
            validator=validator,
            error_message="الرجاء إدخال بريد إلكتروني صحيح"
        )
    
    @classmethod
    def get_url(cls, prompt: str = "الرابط: ", default: str = "") -> str:
        """الحصول على رابط صحيح"""
        url_pattern = r'^https?://[^\s]+$'
        
        def validator(value: str) -> bool:
            return bool(re.match(url_pattern, value))
        
        return cls.get_input(
            prompt,
            default=default,
            validator=validator,
            error_message="الرجاء إدخال رابط صحيح (يبدأ بـ http:// أو https://)"
        )
    
    @classmethod
    def _add_to_history(cls, value: str):
        """إضافة قيمة إلى تاريخ الإدخالات"""
        cls._history.append(value)
        if len(cls._history) > cls._history_limit:
            cls._history.pop(0)
        cls._history_index = len(cls._history) - 1
    
    @classmethod
    def get_history(cls) -> List[str]:
        """الحصول على تاريخ الإدخالات"""
        return cls._history.copy()
    
    @classmethod
    def clear_history(cls):
        """مسح تاريخ الإدخالات"""
        cls._history.clear()
        cls._history_index = -1
    
    @classmethod
    def get_previous_input(cls) -> Optional[str]:
        """الحصول على الإدخال السابق"""
        if cls._history and cls._history_index > 0:
            cls._history_index -= 1
            return cls._history[cls._history_index]
        return None
    
    @classmethod
    def get_next_input(cls) -> Optional[str]:
        """الحصول على الإدخال التالي"""
        if cls._history and cls._history_index < len(cls._history) - 1:
            cls._history_index += 1
            return cls._history[cls._history_index]
        return None


__all__ = ["SafeInput"]