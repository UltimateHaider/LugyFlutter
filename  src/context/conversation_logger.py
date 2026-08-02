"""
LugyFlutter - سجل المحادثات (Conversation Logger)
تسجيل وإدارة محادثات المستخدم مع الوكيل
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

from ..core.config import config
from ..utils.logger import get_logger
from ..utils.colors import print_colored, Colors

logger = get_logger(__name__)


@dataclass
class ConversationEntry:
    """
    مدخل في سجل المحادثة
    """
    role: str  # user, agent, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    parent_id: Optional[str] = None  # للردود المتسلسلة
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل المدخل إلى قاموس"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationEntry':
        """إنشاء مدخل من قاموس"""
        return cls(**data)
    
    def is_user(self) -> bool:
        """التحقق مما إذا كان المدخل من المستخدم"""
        return self.role == "user"
    
    def is_agent(self) -> bool:
        """التحقق مما إذا كان المدخل من الوكيل"""
        return self.role == "agent"
    
    def is_system(self) -> bool:
        """التحقق مما إذا كان المدخل من النظام"""
        return self.role == "system"


class ConversationLogger:
    """
    سجل المحادثات المتقدم
    الميزات:
    - تسجيل جميع المحادثات مع الطوابع الزمنية
    - دعم المحادثات المتسلسلة (الردود)
    - تصنيف المحادثات حسب النوع
    - البحث في المحادثات
    - تصدير المحادثات بتنسيقات متعددة
    - إحصائيات المحادثات
    """
    
    def __init__(self, log_file: str = "logs/conversation.json", max_entries: int = 1000):
        """
        تهيئة سجل المحادثات
        
        Args:
            log_file: مسار ملف السجل
            max_entries: الحد الأقصى لعدد المدخلات
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.entries: List[ConversationEntry] = []
        self.max_entries = max_entries
        
        # فهارس للبحث السريع
        self.index_by_role: Dict[str, List[int]] = {
            "user": [],
            "agent": [],
            "system": []
        }
        self.index_by_type: Dict[str, List[int]] = {}
        
        # إحصائيات
        self.stats = {
            "total_entries": 0,
            "user_messages": 0,
            "agent_messages": 0,
            "system_messages": 0,
            "conversation_start": None,
            "conversation_end": None,
            "last_export": None
        }
        
        # تحميل السجل
        self._load_conversation()
        
        logger.info(f"تم تهيئة ConversationLogger مع {len(self.entries)} مدخل")
    
    def add(
        self,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None,
        parent_id: str = None
    ) -> ConversationEntry:
        """
        إضافة مدخل جديد إلى سجل المحادثة
        
        Args:
            role: دور المتحدث (user, agent, system)
            content: محتوى الرسالة
            metadata: بيانات إضافية
            parent_id: معرف المدخل الأب (للسلاسل)
        
        Returns:
            ConversationEntry: المدخل المضاف
        """
        # إنشاء المدخل
        entry = ConversationEntry(
            role=role,
            content=content,
            metadata=metadata or {},
            parent_id=parent_id
        )
        
        # إضافة إلى القائمة
        self.entries.append(entry)
        
        # تحديث الفهارس
        self._update_index(entry)
        
        # تحديث الإحصائيات
        self._update_stats(entry)
        
        # التحقق من الحد الأقصى
        if len(self.entries) > self.max_entries:
            # إزالة أقدم المدخلات
            removed = self.entries[:-self.max_entries]
            self.entries = self.entries[-self.max_entries:]
            self._rebuild_index()
        
        # حفظ السجل
        self._save_conversation()
        
        logger.debug(f"إضافة مدخل: {role} - {content[:50]}...")
        return entry
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> ConversationEntry:
        """إضافة رسالة من المستخدم"""
        return self.add("user", content, metadata)
    
    def add_agent_message(self, content: str, metadata: Dict[str, Any] = None) -> ConversationEntry:
        """إضافة رسالة من الوكيل"""
        return self.add("agent", content, metadata)
    
    def add_system_message(self, content: str, metadata: Dict[str, Any] = None) -> ConversationEntry:
        """إضافة رسالة من النظام"""
        return self.add("system", content, metadata)
    
    def get_last(self, count: int = 5) -> List[ConversationEntry]:
        """
        الحصول على آخر n من المدخلات
        
        Args:
            count: عدد المدخلات المطلوبة
        
        Returns:
            List[ConversationEntry]: آخر المدخلات
        """
        return self.entries[-count:] if self.entries else []
    
    def get_by_role(self, role: str) -> List[ConversationEntry]:
        """
        الحصول على المدخلات حسب الدور
        
        Args:
            role: الدور المطلوب (user, agent, system)
        
        Returns:
            List[ConversationEntry]: قائمة المدخلات
        """
        indices = self.index_by_role.get(role, [])
        return [self.entries[i] for i in indices if i < len(self.entries)]
    
    def get_by_type(self, type_name: str) -> List[ConversationEntry]:
        """
        الحصول على المدخلات حسب النوع (من metadata)
        
        Args:
            type_name: النوع المطلوب
        
        Returns:
            List[ConversationEntry]: قائمة المدخلات
        """
        indices = self.index_by_type.get(type_name, [])
        return [self.entries[i] for i in indices if i < len(self.entries)]
    
    def search(self, query: str, case_sensitive: bool = False) -> List[ConversationEntry]:
        """
        البحث في محتوى المحادثات
        
        Args:
            query: نص البحث
            case_sensitive: تمييز حالة الأحرف
        
        Returns:
            List[ConversationEntry]: المدخلات المطابقة
        """
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for entry in self.entries:
            content = entry.content
            if not case_sensitive:
                content = content.lower()
            
            if query in content:
                results.append(entry)
        
        return results
    
    def get_conversation_flow(self, start_from: int = 0) -> List[Dict[str, Any]]:
        """
        الحصول على تدفق المحادثة بشكل منظم
        
        Args:
            start_from: الفهرس للبدء منه
        
        Returns:
            List[Dict]: تدفق المحادثة
        """
        flow = []
        for i, entry in enumerate(self.entries[start_from:]):
            flow.append({
                "index": i + start_from,
                "role": entry.role,
                "content": entry.content,
                "timestamp": entry.timestamp,
                "metadata": entry.metadata,
                "is_user": entry.is_user(),
                "is_agent": entry.is_agent()
            })
        return flow
    
    def get_conversation_thread(self, message_id: str) -> List[ConversationEntry]:
        """
        الحصول على سلسلة محادثة كاملة من رسالة معينة
        
        Args:
            message_id: معرف الرسالة
        
        Returns:
            List[ConversationEntry]: سلسلة المحادثة
        """
        # العثور على المدخل
        start_index = None
        for i, entry in enumerate(self.entries):
            if entry.message_id == message_id:
                start_index = i
                break
        
        if start_index is None:
            return []
        
        # جمع السلسلة
        thread = []
        current_id = message_id
        
        # العودة إلى الجذر
        while current_id:
            for i, entry in enumerate(self.entries[:start_index + 1]):
                if entry.message_id == current_id:
                    thread.insert(0, entry)
                    current_id = entry.parent_id
                    break
            else:
                break
        
        return thread
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        الحصول على ملخص المحادثة
        
        Returns:
            Dict: ملخص المحادثة
        """
        if not self.entries:
            return {"message": "لا توجد محادثات"}
        
        total = len(self.entries)
        user_msgs = len(self.get_by_role("user"))
        agent_msgs = len(self.get_by_role("agent"))
        system_msgs = len(self.get_by_role("system"))
        
        # حساب متوسط طول الرسائل
        avg_user_len = sum(len(e.content) for e in self.get_by_role("user")) / max(user_msgs, 1)
        avg_agent_len = sum(len(e.content) for e in self.get_by_role("agent")) / max(agent_msgs, 1)
        
        # حساب مدة المحادثة
        start_time = datetime.fromisoformat(self.entries[0].timestamp)
        end_time = datetime.fromisoformat(self.entries[-1].timestamp)
        duration = (end_time - start_time).total_seconds()
        
        return {
            "total_messages": total,
            "user_messages": user_msgs,
            "agent_messages": agent_msgs,
            "system_messages": system_msgs,
            "average_user_length": round(avg_user_len, 1),
            "average_agent_length": round(avg_agent_len, 1),
            "duration_seconds": round(duration, 1),
            "duration_formatted": self._format_duration(duration),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "first_message": self.entries[0].content[:100],
            "last_message": self.entries[-1].content[:100]
        }
    
    def _format_duration(self, seconds: float) -> str:
        """تنسيق المدة الزمنية"""
        if seconds < 60:
            return f"{int(seconds)} ثانية"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes} دقيقة {secs} ثانية"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours} ساعة {minutes} دقيقة"
    
    def _update_index(self, entry: ConversationEntry):
        """تحديث فهارس البحث"""
        # فهرس حسب الدور
        index = len(self.entries) - 1
        if entry.role in self.index_by_role:
            self.index_by_role[entry.role].append(index)
        
        # فهرس حسب النوع
        if "type" in entry.metadata:
            type_name = entry.metadata["type"]
            if type_name not in self.index_by_type:
                self.index_by_type[type_name] = []
            self.index_by_type[type_name].append(index)
    
    def _update_stats(self, entry: ConversationEntry):
        """تحديث الإحصائيات"""
        self.stats["total_entries"] = len(self.entries)
        
        if entry.role == "user":
            self.stats["user_messages"] += 1
        elif entry.role == "agent":
            self.stats["agent_messages"] += 1
        elif entry.role == "system":
            self.stats["system_messages"] += 1
        
        if not self.stats["conversation_start"]:
            self.stats["conversation_start"] = entry.timestamp
        
        self.stats["conversation_end"] = entry.timestamp
    
    def _rebuild_index(self):
        """إعادة بناء الفهارس"""
        self.index_by_role = {"user": [], "agent": [], "system": []}
        self.index_by_type = {}
        
        for i, entry in enumerate(self.entries):
            if entry.role in self.index_by_role:
                self.index_by_role[entry.role].append(i)
            
            if "type" in entry.metadata:
                type_name = entry.metadata["type"]
                if type_name not in self.index_by_type:
                    self.index_by_type[type_name] = []
                self.index_by_type[type_name].append(i)
    
    def _save_conversation(self):
        """حفظ السجل في الملف"""
        try:
            data = {
                "entries": [e.to_dict() for e in self.entries],
                "stats": self.stats,
                "updated_at": datetime.now().isoformat()
            }
            
            self.log_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
        except Exception as e:
            logger.error(f"فشل حفظ السجل: {e}")
    
    def _load_conversation(self):
        """تحميل السجل من الملف"""
        if not self.log_file.exists():
            return
        
        try:
            data = json.loads(self.log_file.read_text(encoding='utf-8'))
            
            self.entries = [
                ConversationEntry.from_dict(e)
                for e in data.get("entries", [])
            ]
            
            self.stats = data.get("stats", self.stats)
            
            # إعادة بناء الفهارس
            self._rebuild_index()
            
        except Exception as e:
            logger.error(f"فشل تحميل السجل: {e}")
            # إنشاء نسخة احتياطية من الملف التالف
            if self.log_file.exists():
                backup_path = self.log_file.with_suffix(".json.bak")
                self.log_file.rename(backup_path)
                logger.warning(f"تم إنشاء نسخة احتياطية من السجل التالف: {backup_path}")
    
    def export_to_markdown(self, file_path: str = None) -> str:
        """
        تصدير المحادثة إلى Markdown
        
        Args:
            file_path: مسار ملف التصدير
        
        Returns:
            str: مسار الملف المصدر
        """
        if not file_path:
            file_path = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            content = "# 📝 سجل محادثة LugyFlutter\n\n"
            content += f"**تاريخ التصدير:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += f"**إجمالي الرسائل:** {len(self.entries)}\n\n"
            content += "---\n\n"
            
            for entry in self.entries:
                role_emoji = {
                    "user": "🧑",
                    "agent": "🤖",
                    "system": "⚙️"
                }.get(entry.role, "🔹")
                
                role_name = {
                    "user": "المستخدم",
                    "agent": "LugyFlutter",
                    "system": "النظام"
                }.get(entry.role, entry.role)
                
                content += f"### {role_emoji} {role_name}\n"
                content += f"**الوقت:** {entry.timestamp}\n\n"
                content += f"{entry.content}\n\n"
                
                if entry.metadata:
                    content += f"**البيانات:** `{json.dumps(entry.metadata, ensure_ascii=False)}`\n\n"
                
                content += "---\n\n"
            
            Path(file_path).write_text(content, encoding='utf-8')
            
            self.stats["last_export"] = datetime.now().isoformat()
            logger.info(f"تصدير المحادثة إلى: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"فشل تصدير المحادثة: {e}")
            raise
    
    def export_to_json(self, file_path: str = None) -> str:
        """
        تصدير المحادثة إلى JSON
        
        Args:
            file_path: مسار ملف التصدير
        
        Returns:
            str: مسار الملف المصدر
        """
        if not file_path:
            file_path = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "stats": self.stats,
                "entries": [e.to_dict() for e in self.entries]
            }
            
            Path(file_path).write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            self.stats["last_export"] = datetime.now().isoformat()
            logger.info(f"تصدير المحادثة إلى: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"فشل تصدير المحادثة: {e}")
            raise
    
    def clear(self):
        """مسح جميع المدخلات"""
        self.entries.clear()
        self.index_by_role = {"user": [], "agent": [], "system": []}
        self.index_by_type = {}
        self.stats = {k: 0 if isinstance(v, (int, float)) else None for k, v in self.stats.items()}
        self._save_conversation()
        logger.info("تم مسح سجل المحادثة")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات السجل"""
        return {
            **self.stats,
            "total_entries": len(self.entries),
            "last_message": self.entries[-1].content[:50] + "..." if self.entries else None,
            "file_size": self.log_file.stat().st_size if self.log_file.exists() else 0
        }


__all__ = ["ConversationLogger", "ConversationEntry"]