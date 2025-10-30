import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from database import async_session_maker
from models import User, Project, ProjectMember, Task, MemberRole, ProjectStatus, TaskPriority, TaskStatus


class AsyncORM:
    """
    Класс, содержащий асинхронные статические методы
    для взаимодействия с базой данных (CRUD операции).
    """

    @staticmethod
    async def create_user(data: dict) -> User:
        """Создание нового пользователя."""
        async with async_session_maker() as session:
            new_user = User(**data)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        """Получение пользователя по его ID."""
        async with async_session_maker() as session:
            # Для получения объекта по первичному ключу session.get - самый эффективный способ
            user = await session.get(User, user_id)
            return user
        
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[User]:
        """Получение пользователя по его имени (username)."""
        async with async_session_maker() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """Получение пользователя по email."""
        async with async_session_maker() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_user(user_id: int, data: dict) -> Optional[User]:
        """Обновление данных пользователя."""
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return None
            for key, value in data.items():
                setattr(user, key, value)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def create_project(owner_id: int, data: dict) -> Project:
        """Создание нового проекта и добавление владельца как участника."""
        async with async_session_maker() as session:
            new_project = Project(owner_id=owner_id, **data)
            session.add(new_project)
            # Сразу добавляем создателя как владельца проекта
            owner_membership = ProjectMember(
                user_id=owner_id, 
                project=new_project, 
                role=MemberRole.OWNER
            )
            session.add(owner_membership)
            await session.commit()
            await session.refresh(new_project)
            return new_project
    
    @staticmethod
    async def get_user_projects(user_id: int) -> List[Project]:
        """Получение списка проектов, в которых пользователь является участником."""
        async with async_session_maker() as session:
            stmt = (
                select(Project)
                .join(ProjectMember, Project.id == ProjectMember.project_id)
                .where(ProjectMember.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_project_details(project_id: int, limit: int | None = None) -> Optional[Project]:
        """Получение полной информации о проекте с участниками и задачами."""
        async with async_session_maker() as session:
            stmt = (
                select(Project)
                .where(Project.id == project_id)
                .options(
                    selectinload(Project.members).options(
                        joinedload(ProjectMember.user)
                    ),
                    selectinload(Project.tasks)
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_project(project_id: int, data: dict) -> Optional[Project]:
        """Обновление данных проекта."""
        async with async_session_maker() as session:
            project = await session.get(Project, project_id)
            if not project:
                return None
            for key, value in data.items():
                setattr(project, key, value)
            await session.commit()
            await session.refresh(project)
            return project
            
    @staticmethod
    async def delete_project(project_id: int) -> bool:
        """Удаление проекта."""
        async with async_session_maker() as session:
            project = await session.get(Project, project_id)
            if not project:
                return False
            await session.delete(project)
            await session.commit()
            return True

    @staticmethod
    async def add_project_member(project_id: int, user_id: int, role: MemberRole) -> ProjectMember:
        """Добавление нового участника в проект."""
        async with async_session_maker() as session:
            new_member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
            session.add(new_member)
            await session.commit()
            await session.refresh(new_member)
            return new_member
            
    @staticmethod
    async def get_project_member(project_id: int, user_id: int) -> Optional[ProjectMember]:
        """Получение информации об одном участнике проекта."""
        async with async_session_maker() as session:
            return await session.get(ProjectMember, {"project_id": project_id, "user_id": user_id})

    @staticmethod
    async def update_member_role(project_id: int, user_id: int, new_role: MemberRole) -> Optional[ProjectMember]:
        """Изменение роли участника проекта."""
        async with async_session_maker() as session:
            member = await session.get(ProjectMember, {"project_id": project_id, "user_id": user_id})
            if not member:
                return None
            member.role = new_role
            await session.commit()
            await session.refresh(member)
            return member

    @staticmethod
    async def delete_project_member(project_id: int, user_id: int) -> bool:
        """Удаление участника из проекта."""
        async with async_session_maker() as session:
            member = await session.get(ProjectMember, {"project_id": project_id, "user_id": user_id})
            if not member:
                return False
            await session.delete(member)
            await session.commit()
            return True

    @staticmethod
    async def create_task(project_id: int, creator_id: int, data: dict) -> Task:
        """Создание новой задачи в проекте."""
        async with async_session_maker() as session:
            new_task = Task(project_id=project_id, creator_id=creator_id, **data)
            session.add(new_task)
            await session.commit()
            await session.refresh(new_task)
            return new_task

    @staticmethod
    async def get_task(task_id: int) -> Optional[Task]:
        """Получение задачи по ID с информацией о создателе и исполнителе."""
        async with async_session_maker() as session:
            stmt = select(Task).where(Task.id == task_id).options(
                joinedload(Task.creator),
                joinedload(Task.assignee)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_task(task_id: int, data: dict) -> Optional[Task]:
        """Обновление задачи."""
        async with async_session_maker() as session:
            task = await session.get(Task, task_id)
            if not task:
                return None
            for key, value in data.items():
                if value is not None:
                    setattr(task, key, value)
            await session.commit()
            await session.refresh(task)
            return task

    @staticmethod
    async def delete_task(task_id: int) -> bool:
        """Удаление задачи."""
        async with async_session_maker() as session:
            task = await session.get(Task, task_id)
            if not task:
                return False
            await session.delete(task)
            await session.commit()
            return True
