from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from models import MemberRole, ProjectStatus, TaskStatus, TaskPriority



class Token(BaseModel):
    """Схема для JWT токена."""
    access_token: str
    token_type: str



class UserBase(BaseModel):
    """Базовая схема для пользователя."""

    username: str
    email: str



class UserCreate(UserBase):
    """Схема для создания пользователя (принимает пароль)."""

    password: str



class UserRead(UserBase):
    """Схема для чтения данных пользователя из БД."""

    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }



class ProjectBase(BaseModel):
    """Базовая схема для проекта."""

    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE



class ProjectCreate(ProjectBase):
    """Схема для создания проекта."""

    pass



class ProjectRead(ProjectBase):
    """Схема для чтения данных проекта из БД."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }



class ProjectMemberBase(BaseModel):
    """Базовая схема для участника проекта."""

    role: MemberRole



class ProjectMemberCreate(ProjectMemberBase):
    """Схема для добавления участника в проект."""

    user_id: int



class ProjectMemberRead(ProjectMemberBase):
    """Схема для чтения данных участника проекта."""

    project_id: int
    user_id: int
    joined_at: datetime

    model_config = {
        "from_attributes": True
    }



class TaskBase(BaseModel):
    """Базовая схема для задачи."""

    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    position: int = 0
    deadline: Optional[datetime] = None



class TaskCreate(TaskBase):
    """Схема для создания задачи."""

    assignee_id: Optional[int] = None



class TaskUpdate(TaskBase):
    """Схема для частичного обновления задачи."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    position: Optional[int] = None
    deadline: Optional[datetime] = None
    assignee_id: Optional[int] = None



class TaskRead(TaskBase):
    """Схема для чтения данных задачи из БД."""

    id: int
    project_id: int
    creator_id: int
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }



class ProjectMemberWithUser(ProjectMemberRead):
    """Участник проекта с данными самого пользователя."""

    user: UserRead



class TaskWithAssignee(TaskRead):
    """Задача с данными исполнителя."""

    assignee: Optional[UserRead] = None



class ProjectWithDetails(ProjectRead):
    """Проект с детальной информацией: участники и задачи."""

    members: List[ProjectMemberWithUser]
    tasks: List[TaskRead]



class UserWithProjects(UserRead):
    """Пользователь со списком его проектов."""

    projects: List[ProjectRead]



class CommentBase(BaseModel):
    """Базовая схема для комментария."""
    content: str



class CommentCreate(CommentBase):
    """Схема для создания комментария."""
    pass



class CommentRead(CommentBase):
    """Схема для чтения комментария из БД."""
    id: int
    author_id: int
    task_id: int
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }



class CommentReadWithAuthor(CommentRead):
    """Схема для чтения комментария с данными автора."""
    author: UserRead



class TaskReadWithDetails(TaskWithAssignee):
    """Задача со всеми деталями: исполнитель и комментарии."""
    comments: List[CommentReadWithAuthor] = []