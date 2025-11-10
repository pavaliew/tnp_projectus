from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from models import MemberRole, ProjectStatus, TaskStatus, TaskPriority



class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr = Field(min_length=5, max_length=100)



class ProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    status: ProjectStatus = ProjectStatus.ACTIVE



class BoardBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)



class TaskBase(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM



class ProjectMemberBase(BaseModel):
    role: MemberRole



class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=256)



class ProjectCreate(ProjectBase):
    pass



class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    status: Optional[ProjectStatus] = None



class BoardCreate(BoardBase):
    position: Optional[int]



class BoardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    position: Optional[int] = None



class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None
    position: Optional[int] = None
    deadline: Optional[datetime] = None
    assignee_id: Optional[int] = None



class TaskUpdate(BaseModel):
    title: Optional[str] = None
    board_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    position: Optional[int] = None
    deadline: Optional[datetime] = None
    assignee_id: Optional[int] = None
    
class ProjectMemberCreate(ProjectMemberBase):
    user_id: int



class UserRead(UserBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True



class TaskRead(TaskBase):
    id: int
    board_id: int
    created_at: datetime
    updated_at: datetime
    assignee: Optional[UserRead] = None
    position: int

    class Config: from_attributes = True



class BoardRead(BoardBase):
    id: int
    position: int
    tasks: List[TaskRead] = []
    class Config: from_attributes = True



class ProjectMemberRead(ProjectMemberBase):
    user: UserRead 
    joined_at: datetime
    class Config: from_attributes = True



class ProjectRead(ProjectBase):
    """Простая схема для списков проектов."""
    id: int
    created_at: datetime
    class Config: from_attributes = True



class ProjectReadWithDetails(ProjectRead):
    """Полная схема для одного проекта с вложенными данными."""
    members: List[ProjectMemberRead] = []
    boards: List[BoardRead] = []
    class Config: from_attributes = True



class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

