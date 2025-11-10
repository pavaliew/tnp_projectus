import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from database import Base, async_engine, async_session_maker
from models import (
    User,
    Project,
    ProjectMember,
    Board,
    Task,
    MemberRole,
    ProjectStatus,
    TaskStatus,
    TaskPriority,
)
from utils import hash_password



async def clear_data():
    """Очищает данные из таблиц в правильном порядке."""
    print("{INFO} Очистка старых данных...")
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(delete(Task))
            await session.execute(delete(ProjectMember))
            await session.execute(delete(Board))
            await session.execute(delete(Project))
            await session.execute(delete(User))
    print("{INFO} Старые данные удалены.")



async def seed_data():
    """
    Функция для заполнения базы данных начальными данными, сначала удаляя все старые данные и таблицы, а затем создает их заново.
    """

    async with async_session_maker() as session:
        async with session.begin():
            print("{INFO} Заполнение базы данных...")

            user_alice = User(
                username="Alice Potter",
                email="alice@example.com",
                password_hash=hash_password("password123"),
            )
            user_bob = User(
                username="Bob Brown",
                email="bob@example.com",
                password_hash=hash_password("password456"),
            )
            user_charlie = User(
                username="Charlie Smith",
                email="charlie@example.com",
                password_hash=hash_password("password789"),
            )
            session.add_all([user_alice, user_bob, user_charlie])
            await session.flush()
            print("{INFO} Созданы пользователи: Alice, Bob, Charlie.")

            project_phoenix = Project(
                name="Project Phoenix",
                status=ProjectStatus.ACTIVE,
            )
            project_hydra = Project(
                name="Project Hydra",
                status=ProjectStatus.PAUSED,
            )
            session.add_all([project_phoenix, project_hydra])
            await session.flush()
            print("{INFO} Созданы проекты: Phoenix, Hydra.")

            session.add_all([
                ProjectMember(project_id=project_phoenix.id, user_id=user_alice.id, role=MemberRole.OWNER),
                ProjectMember(project_id=project_phoenix.id, user_id=user_bob.id, role=MemberRole.MEMBER),
                ProjectMember(project_id=project_phoenix.id, user_id=user_charlie.id, role=MemberRole.MEMBER),
                ProjectMember(project_id=project_hydra.id, user_id=user_bob.id, role=MemberRole.OWNER),
                ProjectMember(project_id=project_hydra.id, user_id=user_charlie.id, role=MemberRole.MEMBER),
            ])
            print("{INFO} Участники добавлены в проекты.")

            board_phoenix_backlog = Board(
                project_id=project_phoenix.id, 
                title="Backlog",
                position=0
            )
            board_phoenix_progress = Board(
                project_id=project_phoenix.id, 
                title="In Progress",
                position=1
            )
            board_hydra_general = Board(
                project_id=project_hydra.id, 
                title="General",
                position=2
            )
            session.add_all([board_phoenix_backlog, board_phoenix_progress, board_hydra_general])
            await session.flush()
            print("{INFO} Созданы доски для проектов.")

            session.add_all([
                Task(
                    board_id=board_phoenix_progress.id,
                    title="Design new architecture",
                    status=TaskStatus.IN_PROGRESS,
                    priority=TaskPriority.CRITICAL,
                    assignee_id=user_alice.id,
                    position=0
                ),
                Task(
                    board_id=board_phoenix_backlog.id,
                    title="Set up CI/CD pipeline",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    assignee_id=user_bob.id,
                    position=1
                ),
                Task(
                    board_id=board_phoenix_backlog.id,
                    title="Review project documentation",
                    assignee_id=user_charlie.id,
                    position=0
                ),
                Task(
                    board_id=board_hydra_general.id,
                    title="Analyze legacy database",
                    assignee_id=user_bob.id,
                    position=0
                )
            ])
            print("{INFO} Задачи созданы.")
        
        # session.commit() вызывается автоматически при выходе из `async with session.begin()`
        
    print("{INFO} База данных успешно заполнена.")



if __name__ == "__main__":
    asyncio.run(clear_data())
    # asyncio.run(seed_data())
