"""
LugyFlutter - لوحة التحكم (Dashboard)
واجهة ويب تفاعلية باستخدام Streamlit لعرض حالة الوكيل والتحكم فيه
"""

import os
import sys
import json
import base64
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# إضافة المسار الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import config
from src.core.enums import TaskType, InteractionMode
from src.utils.colors import Colors, print_colored
from src.utils.logger import get_logger
from src.utils.helpers import get_file_size, format_duration

logger = get_logger(__name__)


# ============================================================
# إعدادات الصفحة
# ============================================================

st.set_page_config(
    page_title="LugyFlutter Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحميل CSS و JavaScript المخصص
def load_assets():
    """تحميل ملفات CSS و JavaScript"""
    
    # تحميل CSS
    css_path = Path(__file__).parent / "static" / "css" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_code = f.read()
        st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)
    
    # تحميل JavaScript
    js_path = Path(__file__) / "static" / "js" / "dashboard.js"
    if js_path.exists():
        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()
        st.markdown(f"<script>{js_code}</script>", unsafe_allow_html=True)

load_assets()


# ============================================================
# دوال مساعدة للواجهة
# ============================================================

def get_status_color(status: str) -> str:
    """الحصول على لون الحالة"""
    colors = {
        "success": "green",
        "warning": "orange",
        "error": "red",
        "info": "blue",
        "running": "#6200EE",
        "active": "#4CAF50",
        "archived": "#6C6C8A",
        "deleted": "#F44336",
        "draft": "#FFC107",
        "pending": "#FFC107",
        "completed": "#4CAF50",
        "failed": "#F44336"
    }
    return colors.get(status.lower(), "gray")


def format_timestamp(ts: str) -> str:
    """تنسيق الطابع الزمني"""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts


def create_metric_card(label: str, value: Any, delta: Optional[float] = None, icon: str = "") -> str:
    """إنشاء بطاقة مقياس"""
    delta_html = ""
    if delta is not None:
        color = "green" if delta > 0 else "red"
        delta_html = f'<div style="color: {color}; font-size: 0.85rem;">{delta:+.1f}%</div>'
    
    return f"""
    <div class="lugy-metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """


# ============================================================
# تهيئة الوكيل
# ============================================================

def get_agent():
    """الحصول على كائن الوكيل من Session State"""
    if "agent" not in st.session_state:
        st.session_state.agent = None
        st.session_state.agent_initialized = False
    return st.session_state.agent


def initialize_agent():
    """تهيئة الوكيل"""
    if st.session_state.agent_initialized:
        return st.session_state.agent
    
    try:
        from src.core.agent import LugyFlutter
        from src.core.enums import InteractionMode
        
        with st.spinner("🔧 جاري تهيئة LugyFlutter..."):
            agent = LugyFlutter(
                mode=InteractionMode.AUTO,
                api_key=config.GOOGLE_API_KEY
            )
            st.session_state.agent = agent
            st.session_state.agent_initialized = True
            st.success("✅ تم تهيئة LugyFlutter بنجاح!")
            return agent
    except Exception as e:
        st.error(f"❌ فشل تهيئة LugyFlutter: {e}")
        return None


# ============================================================
# الصفحة الرئيسية
# ============================================================

def render_header():
    """تقديم رأس الصفحة"""
    status_text = "🟢 نشط" if st.session_state.agent_initialized else "🔴 غير نشط"
    status_class = "active" if st.session_state.agent_initialized else "inactive"
    
    st.markdown(f"""
    <div class="lugy-header">
        <h1>🤖 LugyFlutter Dashboard</h1>
        <p>الوكيل الذكي المتخصص في FlutterFlow - الإصدار 2.0.0</p>
        <div class="status-badge {status_class}">🚀 حالة الوكيل: {status_text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """تقديم الشريط الجانبي"""
    with st.sidebar:
        # الشعار
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 3rem;">🤖</div>
            <h2 style="color: #BB86FC; margin: 0;">LugyFlutter</h2>
            <p style="color: #8888A0; margin: 0; font-size: 0.9rem;">الإصدار 2.0.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # حالة الوكيل
        st.subheader("📊 حالة الوكيل")
        if st.session_state.agent_initialized:
            st.success("✅ متصل")
            
            # عرض معلومات سريعة
            agent = st.session_state.agent
            if agent:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📁 المشاريع", len(agent.registry.projects) if hasattr(agent, 'registry') else 0)
                with col2:
                    st.metric("💾 نقاط التفتيش", len(agent.checkpoints.checkpoints) if hasattr(agent, 'checkpoints') else 0)
        else:
            st.warning("⚠️ غير متصل")
            if st.button("🔄 تهيئة الوكيل", use_container_width=True):
                initialize_agent()
                st.rerun()
        
        st.markdown("---")
        
        # الأوامر السريعة
        st.subheader("⚡ أوامر سريعة")
        
        quick_commands = [
            ("📁 إنشاء مشروع", "create_project"),
            ("📝 تعديل مشروع", "edit_project"),
            ("📋 نسخ من Figma", "clone_figma"),
            ("🔄 تحديث الحالة", "refresh"),
            ("💾 حفظ نقاط التفتيش", "save_checkpoint")
        ]
        
        for label, cmd in quick_commands:
            if st.button(label, key=f"cmd_{cmd}", use_container_width=True):
                st.session_state.quick_command = cmd
                st.rerun()
        
        st.markdown("---")
        
        # معلومات النظام
        st.subheader("ℹ️ معلومات النظام")
        st.caption(f"🖥️ الإصدار: 2.0.0")
        st.caption(f"🐍 Python: {sys.version.split()[0]}")
        st.caption(f"📁 المسار: {Path(__file__).parent.parent.parent}")
        
        st.markdown("---")
        
        # زر التحديث
        if st.button("🔄 تحديث", use_container_width=True):
            st.rerun()


def render_metrics(agent):
    """تقديم المقاييس الرئيسية"""
    st.subheader("📈 المقاييس الرئيسية")
    
    # حساب نسبة النجاح
    success_rate = 0
    if agent.stats.get("tasks_executed", 0) > 0:
        success_rate = (agent.stats.get("successful_tasks", 0) / agent.stats.get("tasks_executed", 1)) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "المهام المنفذة",
            agent.stats.get("tasks_executed", 0),
            icon="📊"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "نسبة النجاح",
            f"{success_rate:.1f}%",
            icon="✅"
        ), unsafe_allow_html=True)
    
    with col3:
        checkpoint_count = len(agent.checkpoints.checkpoints) if hasattr(agent, 'checkpoints') else 0
        st.markdown(create_metric_card(
            "نقاط التفتيش",
            checkpoint_count,
            icon="💾"
        ), unsafe_allow_html=True)
    
    with col4:
        projects_count = len(agent.registry.projects) if hasattr(agent, 'registry') else 0
        st.markdown(create_metric_card(
            "المشاريع المسجلة",
            projects_count,
            icon="📁"
        ), unsafe_allow_html=True)


def render_status(agent):
    """تقديم الحالة الحالية"""
    st.subheader("📌 الحالة الحالية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 المشروع الحالي")
        if agent.context.project_name:
            st.success(f"📁 {agent.context.project_name}")
            st.caption(f"🆔 المعرف: {agent.context.project_id or 'غير محدد'}")
            st.caption(f"📂 العرض: {agent.context.current_view}")
            st.caption(f"📄 الصفحة: {agent.context.current_page or 'غير محددة'}")
        else:
            st.info("لا يوجد مشروع نشط")
    
    with col2:
        st.markdown("### 📝 التعديلات")
        modifications = agent.context.modifications_made if hasattr(agent.context, 'modifications_made') else []
        if modifications:
            st.markdown(f"**عدد التعديلات:** {len(modifications)}")
            for mod in modifications[-5:]:
                st.markdown(f"✅ {mod[:50]}...")
        else:
            st.info("لا توجد تعديلات")
    
    # عرض نقاط التفتيش
    if hasattr(agent, 'checkpoints'):
        st.markdown("### 💾 نقاط التفتيش")
        checkpoints = agent.checkpoints.list_checkpoints()
        if checkpoints:
            df = pd.DataFrame(checkpoints)
            st.dataframe(df[["step", "description", "timestamp"]], use_container_width=True)
        else:
            st.info("لا توجد نقاط تفتيش")


def render_performance_charts(agent):
    """تقديم رسوم بيانية للأداء"""
    st.subheader("📊 تحليلات الأداء")
    
    # إنشاء رسوم بيانية
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("المهام", "نقاط التفتيش", "التعديلات", "الأداء"),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "histogram"}, {"type": "indicator"}]]
    )
    
    # المهام
    tasks_data = [
        agent.stats.get("successful_tasks", 0),
        agent.stats.get("failed_tasks", 0)
    ]
    fig.add_trace(
        go.Bar(
            x=["ناجحة", "فاشلة"],
            y=tasks_data,
            marker_color=["#4CAF50", "#F44336"],
            name="المهام",
            text=tasks_data,
            textposition="auto"
        ),
        row=1, col=1
    )
    
    # نقاط التفتيش
    checkpoints = agent.checkpoints.list_checkpoints() if hasattr(agent, 'checkpoints') else []
    if checkpoints:
        df_cp = pd.DataFrame(checkpoints)
        fig.add_trace(
            go.Scatter(
                x=df_cp["timestamp"],
                y=df_cp["step"],
                mode="lines+markers",
                name="نقاط التفتيش",
                line=dict(color="#6200EE", width=2),
                marker=dict(size=8)
            ),
            row=1, col=2
        )
    
    # التعديلات
    modifications = agent.context.modifications_made if hasattr(agent.context, 'modifications_made') else []
    if modifications:
        fig.add_trace(
            go.Histogram(
                x=modifications,
                name="التعديلات",
                marker_color="#FF6B6B",
                nbinsx=10
            ),
            row=2, col=1
        )
    
    # الأداء العام
    if agent.stats.get("tasks_executed", 0) > 0:
        success_rate = (agent.stats.get("successful_tasks", 0) / agent.stats.get("tasks_executed", 1)) * 100
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=success_rate,
                title={"text": "نسبة النجاح", "font": {"color": "#C8C8D4"}},
                number={"suffix": "%", "font": {"color": "#C8C8D4"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#C8C8D4"},
                    "bar": {"color": "#6200EE"},
                    "steps": [
                        {"range": [0, 50], "color": "rgba(244, 67, 54, 0.3)"},
                        {"range": [50, 75], "color": "rgba(255, 193, 7, 0.3)"},
                        {"range": [75, 100], "color": "rgba(76, 175, 80, 0.3)"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 2},
                        "thickness": 0.75,
                        "value": 90
                    }
                }
            ),
            row=2, col=2
        )
    
    # تحديث التخطيط
    fig.update_layout(
        height=600,
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#C8C8D4"}
    )
    
    # تحديث محاور الرسوم البيانية
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", title_font={"color": "#C8C8D4"})
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", title_font={"color": "#C8C8D4"})
    
    st.plotly_chart(fig, use_container_width=True)


def render_checkpoints(agent):
    """تقديم نقاط التفتيش التفصيلية"""
    st.subheader("💾 نقاط التفتيش التفصيلية")
    
    if not hasattr(agent, 'checkpoints'):
        st.info("نظام نقاط التفتيش غير متاح")
        return
    
    checkpoints = agent.checkpoints.list_checkpoints()
    
    if not checkpoints:
        st.info("لا توجد نقاط تفتيش")
        return
    
    # عرض نقاط التفتيش
    col1, col2 = st.columns([3, 1])
    
    with col1:
        df = pd.DataFrame(checkpoints)
        st.dataframe(
            df[["index", "step", "description", "timestamp"]],
            use_container_width=True,
            column_config={
                "index": "الرقم",
                "step": "الخطوة",
                "description": "الوصف",
                "timestamp": "الوقت"
            }
        )
    
    with col2:
        st.markdown("### 🎮 التحكم")
        
        if st.button("↩️ التراجع (Undo)", use_container_width=True):
            checkpoint = agent.checkpoints.undo()
            if checkpoint:
                st.success(f"تم التراجع إلى: {checkpoint.description}")
                st.rerun()
            else:
                st.warning("لا توجد نقاط تفتيش للتراجع")
        
        if st.button("↪️ إعادة (Redo)", use_container_width=True):
            checkpoint = agent.checkpoints.redo()
            if checkpoint:
                st.success(f"تم الإعادة إلى: {checkpoint.description}")
                st.rerun()
            else:
                st.warning("لا توجد نقاط تفتيش للإعادة")
        
        if st.button("🗑️ مسح الكل", use_container_width=True):
            if st.button("تأكيد المسح", use_container_width=True):
                agent.checkpoints.clear_all()
                st.success("تم مسح جميع نقاط التفتيش")
                st.rerun()


def render_projects(agent):
    """تقديم المشاريع المسجلة"""
    st.subheader("📁 المشاريع المسجلة")
    
    if not hasattr(agent, 'registry'):
        st.info("سجل المشاريع غير متاح")
        return
    
    projects = agent.registry.projects
    
    if not projects:
        st.info("لا توجد مشاريع مسجلة")
        return
    
    # عرض المشاريع
    projects_data = []
    for name, record in projects.items():
        projects_data.append({
            "الاسم": name,
            "المصدر": record.source_type,
            "الحالة": record.status,
            "التعديلات": record.modifications_count,
            "العلامات": ", ".join(record.tags),
            "تاريخ الإنشاء": format_timestamp(record.created_at),
            "آخر تحديث": format_timestamp(record.updated_at)
        })
    
    df = pd.DataFrame(projects_data)
    st.dataframe(df, use_container_width=True)


def render_logs():
    """تقديم السجلات"""
    st.subheader("📝 السجلات")
    
    log_dir = Path("logs")
    if not log_dir.exists():
        st.info("لا توجد سجلات")
        return
    
    log_files = list(log_dir.glob("*.log*"))
    if not log_files:
        st.info("لا توجد ملفات سجل")
        return
    
    # اختيار ملف السجل
    log_names = [f.name for f in log_files]
    selected_log = st.selectbox("اختر ملف السجل", log_names)
    
    if selected_log:
        log_path = log_dir / selected_log
        if log_path.exists():
            # قراءة السجل
            with st.expander("عرض السجل", expanded=True):
                try:
                    content = log_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    # عرض آخر 100 سطر
                    st.text_area(
                        f"آخر {min(100, len(lines))} سطر",
                        "\n".join(lines[-100:]),
                        height=400
                    )
                    
                    # إحصائيات السجل
                    error_count = content.count("ERROR")
                    warning_count = content.count("WARNING")
                    info_count = content.count("INFO")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("❌ الأخطاء", error_count)
                    with col2:
                        st.metric("⚠️ التحذيرات", warning_count)
                    with col3:
                        st.metric("ℹ️ المعلومات", info_count)
                    
                except Exception as e:
                    st.error(f"فشل قراءة السجل: {e}")


def render_quick_command(agent):
    """تنفيذ الأوامر السريعة"""
    if "quick_command" not in st.session_state:
        return
    
    cmd = st.session_state.quick_command
    st.session_state.quick_command = None
    
    if cmd == "refresh":
        st.rerun()
    
    elif cmd == "create_project":
        st.info("🚀 جاري إنشاء مشروع جديد...")
        # يمكن إضافة منطق إنشاء المشروع هنا
    
    elif cmd == "edit_project":
        st.info("📝 جاري فتح محرر المشروع...")
    
    elif cmd == "clone_figma":
        st.info("📋 جاري فتح أداة النسخ من Figma...")
    
    elif cmd == "save_checkpoint":
        if hasattr(agent, 'checkpoints'):
            agent.checkpoints.save_checkpoint(
                step=agent.context.current_step,
                state={"context": agent.context.to_dict()},
                description="نقطة تفتيش يدوية"
            )
            st.success("💾 تم حفظ نقطة التفتيش بنجاح!")
            st.rerun()


def render_footer():
    """تقديم تذيير الصفحة"""
    st.markdown("""
    <div class="lugy-footer">
        <p>🤖 LugyFlutter v2.0.0 - الوكيل الذكي المتخصص في FlutterFlow</p>
        <p style="font-size: 0.7rem; opacity: 0.6;">
            © 2024 LugyFlutter | تم التطوير باستخدام ❤️ و Streamlit
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# الصفحة الرئيسية
# ============================================================

def main():
    """الوظيفة الرئيسية للوحة التحكم"""
    
    # تقديم الرأس
    render_header()
    
    # تقديم الشريط الجانبي
    render_sidebar()
    
    # تهيئة الوكيل
    agent = get_agent()
    if not agent and st.session_state.agent_initialized:
        agent = initialize_agent()
    
    # عرض المحتوى الرئيسي
    if agent:
        # تنفيذ الأوامر السريعة
        render_quick_command(agent)
        
        # إنشاء تبويبات
        tabs = st.tabs([
            "📊 نظرة عامة",
            "📌 الحالة",
            "💾 نقاط التفتيش",
            "📁 المشاريع",
            "📝 السجلات",
            "⚙️ الإعدادات"
        ])
        
        with tabs[0]:  # نظرة عامة
            render_metrics(agent)
            render_performance_charts(agent)
        
        with tabs[1]:  # الحالة
            render_status(agent)
        
        with tabs[2]:  # نقاط التفتيش
            render_checkpoints(agent)
        
        with tabs[3]:  # المشاريع
            render_projects(agent)
        
        with tabs[4]:  # السجلات
            render_logs()
        
        with tabs[5]:  # الإعدادات
            st.subheader("⚙️ إعدادات LugyFlutter")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🔧 الإعدادات العامة")
                
                # مستوى التسجيل
                log_level = st.selectbox(
                    "مستوى التسجيل",
                    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    index=1
                )
                
                # عدد نقاط التفتيش
                max_checkpoints = st.number_input(
                    "الحد الأقصى لنقاط التفتيش",
                    min_value=5,
                    max_value=100,
                    value=20
                )
                
                # مهلة المتصفح
                browser_timeout = st.number_input(
                    "مهلة المتصفح (ثانية)",
                    min_value=10,
                    max_value=120,
                    value=30
                )
            
            with col2:
                st.markdown("### 🎨 مظهر الواجهة")
                
                theme = st.selectbox(
                    "المظهر",
                    ["داكن", "فاتح", "تلقائي"],
                    index=0
                )
                
                st.markdown("### 📦 تصدير البيانات")
                
                if st.button("📤 تصدير السجلات"):
                    from src.utils.helpers import export_logs_to_zip
                    result = export_logs_to_zip("logs")
                    if result:
                        st.success(f"✅ تم التصدير إلى: {result}")
                
                if st.button("📤 تصدير نقاط التفتيش"):
                    if hasattr(agent, 'checkpoints'):
                        data = agent.checkpoints.export_checkpoints()
                        st.download_button(
                            label="تحميل نقاط التفتيش",
                            data=json.dumps(data, ensure_ascii=False, indent=2),
                            file_name=f"checkpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
            
            # زر حفظ الإعدادات
            if st.button("💾 حفظ الإعدادات", use_container_width=True):
                st.success("✅ تم حفظ الإعدادات بنجاح!")
    else:
        # الوكيل غير مهيأ
        st.warning("⚠️ الوكيل غير مهيأ. يرجى تهيئته من الشريط الجانبي.")
        
        # عرض معلومات الاتصال
        st.info("""
        ### 🔑 مطلوب مفتاح Google Gemini API
        
        للاتصال بـ LugyFlutter، تحتاج إلى:
        1. مفتاح Google Gemini API
        2. تثبيت المكتبات المطلوبة
        3. تهيئة المتصفح (Chrome)
        
        يمكنك تهيئة الوكيل بالنقر على زر "تهيئة الوكيل" في الشريط الجانبي.
        """)
    
    # تقديم التذيير
    render_footer()


# ============================================================
# تشغيل التطبيق
# ============================================================

if __name__ == "__main__":
    main()