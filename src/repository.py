from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from database import async_session_maker
from models import User, Project, ProjectMember, Task, Board, MemberRole
import schemas
import utils



class Repository:
    """
    Класс, отвечающий за операции с базой данных (CRUD).
    """

    @staticmethod
    async def create_user(data: schemas.UserCreate) -> User:
        """Создание нового пользователя."""
        async with async_session_maker() as session:
            user_data = data.model_dump()
            plain_password = user_data.pop("password")
            new_user = User(
                **user_data, 
                password_hash=utils.hash_password(plain_password)
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        """Получает пользователя по его ID."""
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            return user

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """Получение пользователя по email."""
        async with async_session_maker() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def get_projects_for_user(user_id: int) -> List[Project]:
        """Получение списка проектов, в которых состоит пользователь."""
        async with async_session_maker() as session:
            query = (
                select(Project)
                .join(ProjectMember)
                .where(ProjectMember.user_id == user_id)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def create_project(creator_id: int, data: schemas.ProjectCreate) -> Project:
        """Создание нового проекта и назначение создателя владельцем."""
        async with async_session_maker() as session:
            async with session.begin():
                project_data = data.model_dump()
                new_project = Project(**project_data)
                session.add(new_project)
                await session.flush()

                owner_membership = ProjectMember(
                    project_id=new_project.id,
                    user_id=creator_id,
                    role=MemberRole.OWNER
                )
                session.add(owner_membership)
            
            await session.refresh(new_project)
            return new_project

    @staticmethod
    async def get_project_with_details(project_id: int) -> Optional[Project]:
        """Получение проекта с его участниками и досками (с задачами)."""
        async with async_session_maker() as session:
            query = (
                select(Project)
                .where(Project.id == project_id)
                .options(
                    selectinload(Project.members).joinedload(ProjectMember.user),
                    selectinload(Project.boards).selectinload(Board.tasks).selectinload(Task.assignee)
                )
            )
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def update_project(project_id: int, data: schemas.ProjectUpdate) -> Optional[Project]:
        """Частичное обновление проекта."""
        async with async_session_maker() as session:
            update_data = data.model_dump(exclude_unset=True)
            if not update_data:
                return None

            stmt = (
                update(Project)
                .where(Project.id == project_id)
                .values(**update_data)
                .returning(Project)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.scalars().first()

    @staticmethod
    async def delete_project(project_id: int) -> bool:
        """Удаление проекта."""
        async with async_session_maker() as session:
            stmt = delete(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_project_members(project_id: int) -> List[ProjectMember]:
        """Получение списка участников проекта."""
        async with async_session_maker() as session:
            query = (
                select(ProjectMember)
                .where(ProjectMember.project_id == project_id)
                .options(selectinload(ProjectMember.user))
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def add_project_member(project_id: int, data: schemas.ProjectMemberCreate) -> ProjectMember:
        """Просто создает запись о членстве в проекте."""
        
        async with async_session_maker() as session:
            new_member = ProjectMember(
                project_id=project_id,
                user_id=data.user_id,
                role=data.role
            )
            session.add(new_member)
            
            await session.commit()
            
            await session.refresh(new_member)
            
            await session.refresh(new_member, attribute_names=['user'])

            return new_member

    @staticmethod
    async def remove_project_member(project_id: int, user_id: int) -> bool:
        """Удаление участника из проекта."""
        async with async_session_maker() as session:
            stmt = delete(ProjectMember).where(
                (ProjectMember.project_id == project_id) & (ProjectMember.user_id == user_id)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
        
    @staticmethod
    async def get_board_by_id(board_id: int) -> Optional[Board]:
        """Получение доски по ID с 'жадной' загрузкой задач и их исполнителей."""
        async with async_session_maker() as session:
            query = (
                select(Board)
                .where(Board.id == board_id)
                .options(
                    selectinload(Board.tasks).selectinload(Task.assignee)
                )
            )
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def create_board(project_id: int, data: schemas.BoardCreate) -> Optional[Board]:
        """
        Создает новую доску в проекте.
        Возвращает созданную доску или None, если доска с таким названием уже существует.
        """
        async with async_session_maker() as session:
            existing_board_query = select(Board).where(
                Board.project_id == project_id,
                Board.title == data.title
            )
            result = await session.execute(existing_board_query)
            if result.scalars().first():
                return None

            new_board = Board(
                title=data.title,
                project_id=project_id,
                position=data.position
            )
            session.add(new_board)
            await session.commit()
            new_board_id = new_board.id
        
        created_board = await Repository.get_board_by_id(new_board_id)
        return created_board

    @staticmethod
    async def update_board(board_id: int, data: schemas.BoardUpdate) -> Optional[Board]:
        """Частичное обновление доски."""
        async with async_session_maker() as session:
            update_data = data.model_dump(exclude_unset=True)
            
            if update_data:
                stmt = (
                    update(Board)
                    .where(Board.id == board_id)
                    .values(**update_data)
                )
                await session.execute(stmt)
                await session.commit()

            updated_board = await Repository.get_board_by_id(board_id)
            return updated_board

    @staticmethod
    async def delete_board(board_id: int) -> bool:
        """Удаление доски."""
        async with async_session_maker() as session:
            stmt = delete(Board).where(Board.id == board_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_task_by_id(task_id: int) -> Optional[Task]:
        """Получает задачу по ID с 'жадной' загрузкой исполнителя."""
        async with async_session_maker() as session:
            query = (
                select(Task)
                .where(Task.id == task_id)
                .options(selectinload(Task.assignee))
            )
            result = await session.execute(query)
            return result.scalars().first()
        
    @staticmethod
    async def create_task(board_id: int, data: schemas.TaskCreate) -> Task:
        """Создание новой задачи на доске."""
        async with async_session_maker() as session:
            new_task = Task(
                title=data.title,
                board_id=board_id,
                priority=data.priority,
                status=data.status,
                position=data.position,
                deadline=data.deadline,
                assignee_id=data.assignee_id
            )
            session.add(new_task)
            await session.commit()
            new_task_id = new_task.id
            
        created_task = await Repository.get_task_by_id(new_task_id)
        return created_task

    @staticmethod
    async def update_task(task_id: int, data: schemas.TaskUpdate) -> Optional[Task]:
        """
        Частичное обновление задачи.
        Сначала обновляем, потом "жадно" загружаем и возвращаем.
        """
        async with async_session_maker() as session:
            update_data = data.model_dump(exclude_unset=True)
            if not update_data:
                return await Repository.get_task_by_id(task_id)

            stmt = (
                update(Task)
                .where(Task.id == task_id)
                .values(**update_data)
            )
            await session.execute(stmt)
            await session.commit()

            updated_task = await Repository.get_task_by_id(task_id)
            return updated_task

    @staticmethod
    async def delete_task(task_id: int) -> bool:
        """Удаление задачи."""
        async with async_session_maker() as session:
            stmt = delete(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
