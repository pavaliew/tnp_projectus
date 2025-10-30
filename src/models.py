from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    func,
    Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum

from database import Base



class MemberRole(enum.Enum):
    OWNER = "owner"
    MEMBER = "member"
    NOT_ACCESSABLE_MEMBER = "not_accessable_member"



class ProjectStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"



class TaskStatus(enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"



class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"



class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project_memberships: Mapped[list["ProjectMember"]] = relationship("ProjectMember", back_populates="user")
    assigned_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    created_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="creator", foreign_keys="Task.creator_id")



class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status_enum", create_type=True),
        default=ProjectStatus.ACTIVE
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    members: Mapped[list["ProjectMember"]] = relationship("ProjectMember", back_populates="project")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project")



class ProjectMember(Base):
    __tablename__ = "project_members"
    
    # project_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role_enum", create_type=True),
        default=MemberRole.MEMBER
    )
    joined_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        PrimaryKeyConstraint("project_id", "user_id"),
    )
    
    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")



class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assignee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum", create_type=True),
        default=TaskStatus.TODO
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority_enum", create_type=True),
        default=TaskPriority.MEDIUM
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    creator: Mapped["User"] = relationship("User", back_populates="created_tasks", foreign_keys=[creator_id])
