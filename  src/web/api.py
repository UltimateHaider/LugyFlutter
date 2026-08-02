# LugyFlutter - واجهة API (FastAPI)
# توفير واجهات برمجية للتفاعل مع LugyFlutter عن بعد

import os
import sys
import json
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

# إضافة المسار الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn

from src.core.config import config
from src.core.agent import LugyFlutter
from src.core.enums import TaskType, InteractionMode
from src.utils.logger import get_logger
from src.utils.helpers import get_system_info, export_logs_to_zip
from src.utils.validators import Validators

logger = get_logger(__name__)


# نماذج البيانات (Pydantic Models)

class TaskRequest(BaseModel):
    user_input: str = Field(..., description="طلب المستخدم", min_length=1, max_length=1000)
    mode: str = Field("full_interactive", description="وضع التفاعل", enum=["auto", "confirm_steps", "ask_clarifications", "full_interactive", "debug"])
    project_name: Optional[str] = Field(None, description="اسم المشروع (اختياري)")
    auto_execute: bool = Field(False, description="تنفيذ تلقائي بدون تأكيد")
    
    @validator('mode')
    def validate_mode(cls, v):
        valid_modes = ["auto", "confirm_steps", "ask_clarifications", "full_interactive", "debug"]
        if v not in valid_modes:
            raise ValueError(f"الوضع غير صحيح. الخيارات المتاحة: {', '.join(valid_modes)}")
        return v


class TaskResponse(BaseModel):
    task_id: str = Field(..., description="معرف المهمة")
    status: str = Field(..., description="حالة المهمة")
    result: Optional[str] = Field(None, description="نتيجة المهمة")
    error: Optional[str] = Field(None, description="رسالة الخطأ")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    progress: int = Field(0, ge=0, le=100)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str = Field(..., description="اسم المشروع", min_length=2, max_length=50)
    template: str = Field("blank", description="قالب المشروع", enum=["blank", "app", "game"])
    description: Optional[str] = Field(None, description="وصف المشروع")
    
    @validator('name')
    def validate_name(cls, v):
        if not Validators.validate_project_name(v):
            raise ValueError("اسم المشروع غير صحيح. يجب أن يكون 2-50 حرفاً")
        return v


class ProjectClone(BaseModel):
    source_url: str = Field(..., description="رابط المصدر (Figma/Lovable)")
    source_type: str = Field(..., description="نوع المصدر", enum=["figma", "lovable"])
    project_name: str = Field(..., description="اسم المشروع الجديد", min_length=2, max_length=50)
    
    @validator('source_url')
    def validate_source_url(cls, v, values):
        if 'source_type' in values:
            if values['source_type'] == 'figma':
                if not Validators.validate_figma_url(v):
                    raise ValueError("رابط Figma غير صحيح")
            elif values['source_type'] == 'lovable':
                if not Validators.validate_lovable_url(v):
                    raise ValueError("رابط Lovable غير صحيح")
        return v


class CheckpointCreate(BaseModel):
    description: str = Field(..., description="وصف نقطة التفتيش")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CheckpointResponse(BaseModel):
    checkpoint_id: str
    step: int
    description: str
    timestamp: str
    has_screenshot: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    system_info: Dict[str, Any]
    agent_initialized: bool


# إدارة حالة الوكيل

class AgentManager:
    _instance = None
    _agent: Optional[LugyFlutter] = None
    _tasks: Dict[str, Dict[str, Any]] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_agent(cls) -> Optional[LugyFlutter]:
        return cls._agent
    
    @classmethod
    async def initialize_agent(cls) -> bool:
        try:
            if cls._initialized:
                return True
            
            logger.info("جاري تهيئة LugyFlutter...")
            
            cls._agent = LugyFlutter(
                mode=InteractionMode.AUTO,
                api_key=config.GOOGLE_API_KEY
            )
            
            await cls._agent.initialize_browser()
            
            cls._initialized = True
            logger.info("تم تهيئة LugyFlutter بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"فشل تهيئة LugyFlutter: {e}")
            return False
    
    @classmethod
    def get_task(cls, task_id: str) -> Optional[Dict[str, Any]]:
        return cls._tasks.get(task_id)
    
    @classmethod
    def create_task(cls, task_id: str) -> Dict[str, Any]:
        task = {
            "task_id": task_id,
            "status": "pending",
            "result": None,
            "error": None,
            "progress": 0,
            "steps": [],
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None
        }
        cls._tasks[task_id] = task
        return task
    
    @classmethod
    def update_task(cls, task_id: str, **kwargs):
        if task_id in cls._tasks:
            cls._tasks[task_id].update(kwargs)
            cls._tasks[task_id]["updated_at"] = datetime.now().isoformat()
    
    @classmethod
    def complete_task(cls, task_id: str, result: str = None, error: str = None):
        if task_id in cls._tasks:
            cls._tasks[task_id]["status"] = "completed" if not error else "failed"
            cls._tasks[task_id]["result"] = result
            cls._tasks[task_id]["error"] = error
            cls._tasks[task_id]["progress"] = 100
            cls._tasks[task_id]["completed_at"] = datetime.now().isoformat()
            cls._tasks[task_id]["updated_at"] = datetime.now().isoformat()


# إنشاء تطبيق FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("بدء تشغيل LugyFlutter API...")
    await AgentManager.initialize_agent()
    yield
    logger.info("إيقاف تشغيل LugyFlutter API...")

app = FastAPI(
    title="LugyFlutter API",
    description="الوكيل الذكي المتخصص في FlutterFlow - واجهة برمجية",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# نقاط النهاية (Endpoints)

@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "name": "LugyFlutter API",
        "version": "2.0.0",
        "status": "running",
        "description": "الوكيل الذكي المتخصص في FlutterFlow",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    agent = AgentManager.get_agent()
    return HealthResponse(
        status="healthy" if agent else "unhealthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        system_info=get_system_info(),
        agent_initialized=AgentManager._initialized
    )


@app.post("/task/execute", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks
):
    try:
        agent = AgentManager.get_agent()
        if not agent:
            raise HTTPException(status_code=503, detail="الوكيل غير جاهز")
        
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = AgentManager.create_task(task_id)
        task["status"] = "running"
        
        background_tasks.add_task(
            _run_task,
            task_id,
            request.user_input,
            request.mode
        )
        
        return TaskResponse(
            task_id=task_id,
            status="started",
            result=None
        )
        
    except Exception as e:
        logger.error(f"فشل تنفيذ المهمة: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    task = AgentManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        result=task["result"],
        error=task["error"],
        progress=task["progress"],
        steps=task["steps"],
        started_at=task["started_at"],
        updated_at=task["updated_at"],
        completed_at=task.get("completed_at")
    )


@app.get("/task/{task_id}/wait", response_model=TaskStatus)
async def wait_for_task(
    task_id: str,
    timeout: int = Query(60, description="مهلة الانتظار بالثواني")
):
    task = AgentManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        task = AgentManager.get_task(task_id)
        if task and task["status"] in ["completed", "failed"]:
            return TaskStatus(
                task_id=task["task_id"],
                status=task["status"],
                result=task["result"],
                error=task["error"],
                progress=task["progress"],
                steps=task["steps"],
                started_at=task["started_at"],
                updated_at=task["updated_at"],
                completed_at=task.get("completed_at")
            )
        await asyncio.sleep(0.5)
    
    raise HTTPException(status_code=408, detail="انتهت مهلة الانتظار")


@app.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(
    limit: int = Query(20, description="عدد المهام", ge=1, le=100),
    status: Optional[str] = Query(None, description="تصفية حسب الحالة")
):
    tasks = list(AgentManager._tasks.values())
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    tasks.sort(key=lambda x: x["started_at"], reverse=True)
    return tasks[:limit]


@app.post("/project/create", response_model=Dict[str, Any])
async def create_project(request: ProjectCreate):
    try:
        agent = AgentManager.get_agent()
        if not agent:
            raise HTTPException(status_code=503, detail="الوكيل غير جاهز")
        
        if hasattr(agent, 'registry'):
            agent.registry.register_project(
                project_name=request.name,
                metadata={"template": request.template, "description": request.description}
            )
        
        return {
            "status": "success",
            "message": f"تم إنشاء المشروع {request.name} بنجاح",
            "project": {
                "name": request.name,
                "template": request.template,
                "description": request.description,
                "created_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"فشل إنشاء المشروع: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/project/clone", response_model=Dict[str, Any])
async def clone_project(request: ProjectClone):
    try:
        agent = AgentManager.get_agent()
        if not agent:
            raise HTTPException(status_code=503, detail="الوكيل غير جاهز")
        
        if hasattr(agent, 'registry'):
            agent.registry.register_clone(
                source_url=request.source_url,
                flutterflow_project=request.project_name,
                source_type=request.source_type
            )
        
        return {
            "status": "success",
            "message": f"تم نسخ المشروع من {request.source_type} بنجاح",
            "project": {
                "name": request.project_name,
                "source_type": request.source_type,
                "source_url": request.source_url,
                "created_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"فشل نسخ المشروع: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/checkpoints", response_model=List[CheckpointResponse])
async def list_checkpoints():
    agent = AgentManager.get_agent()
    if not agent or not hasattr(agent, 'checkpoints'):
        raise HTTPException(status_code=503, detail="نظام نقاط التفتيش غير متاح")
    
    checkpoints = agent.checkpoints.list_checkpoints()
    
    return [
        CheckpointResponse(
            checkpoint_id=cp.get("id", ""),
            step=cp.get("step", 0),
            description=cp.get("description", ""),
            timestamp=cp.get("timestamp", ""),
            has_screenshot=cp.get("has_screenshot", False)
        )
        for cp in checkpoints
    ]


@app.post("/checkpoints", response_model=Dict[str, str])
async def create_checkpoint(request: CheckpointCreate):
    agent = AgentManager.get_agent()
    if not agent or not hasattr(agent, 'checkpoints'):
        raise HTTPException(status_code=503, detail="نظام نقاط التفتيش غير متاح")
    
    screenshot = None
    if hasattr(agent, 'browser') and agent.browser:
        try:
            screenshot = await agent.browser.take_screenshot()
        except:
            pass
    
    checkpoint_id = agent.checkpoints.save_checkpoint(
        step=agent.context.current_step,
        state={"context": agent.context.to_dict()},
        screenshot=screenshot,
        description=request.description,
        metadata=request.metadata
    )
    
    return {
        "status": "success",
        "checkpoint_id": checkpoint_id,
        "message": "تم حفظ نقطة التفتيش بنجاح"
    }


@app.post("/checkpoints/undo", response_model=Dict[str, Any])
async def undo_checkpoint():
    agent = AgentManager.get_agent()
    if not agent or not hasattr(agent, 'checkpoints'):
        raise HTTPException(status_code=503, detail="نظام نقاط التفتيش غير متاح")
    
    checkpoint = agent.checkpoints.undo()
    if checkpoint:
        return {
            "status": "success",
            "checkpoint": {
                "id": checkpoint.checkpoint_id,
                "description": checkpoint.description,
                "step": checkpoint.step
            },
            "message": "تم التراجع بنجاح"
        }
    else:
        raise HTTPException(status_code=404, detail="لا توجد نقاط تفتيش للتراجع")


@app.post("/checkpoints/redo", response_model=Dict[str, Any])
async def redo_checkpoint():
    agent = AgentManager.get_agent()
    if not agent or not hasattr(agent, 'checkpoints'):
        raise HTTPException(status_code=503, detail="نظام نقاط التفتيش غير متاح")
    
    checkpoint = agent.checkpoints.redo()
    if checkpoint:
        return {
            "status": "success",
            "checkpoint": {
                "id": checkpoint.checkpoint_id,
                "description": checkpoint.description,
                "step": checkpoint.step
            },
            "message": "تم الإعادة بنجاح"
        }
    else:
        raise HTTPException(status_code=404, detail="لا توجد نقاط تفتيش للإعادة")


@app.get("/screenshot", response_class=StreamingResponse)
async def get_screenshot():
    agent = AgentManager.get_agent()
    if not agent or not hasattr(agent, 'browser'):
        raise HTTPException(status_code=503, detail="المتصفح غير متاح")
    
    try:
        screenshot = await agent.browser.take_screenshot()
        return StreamingResponse(
            iter([screenshot]),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل التقاط لقطة الشاشة: {e}")


@app.get("/status", response_model=Dict[str, Any])
async def get_status():
    agent = AgentManager.get_agent()
    
    if not agent:
        return {
            "status": "not_initialized",
            "message": "الوكيل غير مهيأ"
        }
    
    return {
        "status": "running",
        "name": "LugyFlutter",
        "version": "2.0.0",
        "context": agent.context.to_dict() if agent.context else {},
        "stats": agent.stats,
        "checkpoints": len(agent.checkpoints.checkpoints) if hasattr(agent, 'checkpoints') else 0,
        "projects": len(agent.registry.projects) if hasattr(agent, 'registry') else 0,
        "browser_ready": agent.browser is not None if hasattr(agent, 'browser') else False
    }


@app.post("/export/logs", response_model=Dict[str, str])
async def export_logs():
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            raise HTTPException(status_code=404, detail="لا توجد سجلات")
        
        zip_path = export_logs_to_zip(log_dir)
        
        if zip_path:
            return {
                "status": "success",
                "file_path": str(zip_path),
                "message": "تم تصدير السجلات بنجاح"
            }
        else:
            raise HTTPException(status_code=500, detail="فشل تصدير السجلات")
            
    except Exception as e:
        logger.error(f"فشل تصدير السجلات: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/logs/download")
async def download_logs():
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            raise HTTPException(status_code=404, detail="لا توجد سجلات")
        
        zip_path = export_logs_to_zip(log_dir)
        
        if zip_path and zip_path.exists():
            return FileResponse(
                path=zip_path,
                filename=zip_path.name,
                media_type="application/zip"
            )
        else:
            raise HTTPException(status_code=500, detail="فشل إنشاء ملف السجلات")
            
    except Exception as e:
        logger.error(f"فشل تحميل السجلات: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/restart", response_model=Dict[str, str])
async def restart_agent():
    try:
        AgentManager._initialized = False
        AgentManager._agent = None
        
        success = await AgentManager.initialize_agent()
        
        if success:
            return {
                "status": "success",
                "message": "تم إعادة تشغيل الوكيل بنجاح"
            }
        else:
            raise HTTPException(status_code=500, detail="فشل إعادة تشغيل الوكيل")
            
    except Exception as e:
        logger.error(f"فشل إعادة تشغيل الوكيل: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# دوال مساعدة

async def _run_task(task_id: str, user_input: str, mode: str):
    try:
        agent = AgentManager.get_agent()
        if not agent:
            AgentManager.update_task(task_id, status="failed", error="الوكيل غير جاهز")
            return
        
        AgentManager.update_task(task_id, status="running", progress=10)
        
        mode_map = {
            "auto": InteractionMode.AUTO,
            "confirm_steps": InteractionMode.CONFIRM_STEPS,
            "ask_clarifications": InteractionMode.ASK_CLARIFICATIONS,
            "full_interactive": InteractionMode.FULL_INTERACTIVE,
            "debug": InteractionMode.DEBUG
        }
        
        agent.mode = mode_map.get(mode, InteractionMode.FULL_INTERACTIVE)
        
        AgentManager.update_task(task_id, progress=30)
        
        result = await agent.process_user_request(user_input)
        
        AgentManager.update_task(task_id, progress=90)
        
        AgentManager.complete_task(task_id, result=str(result))
        
    except Exception as e:
        logger.error(f"فشل تنفيذ المهمة {task_id}: {e}")
        AgentManager.complete_task(task_id, error=str(e))


# التشغيل

def run_api(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(
        "src.web.api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_api()