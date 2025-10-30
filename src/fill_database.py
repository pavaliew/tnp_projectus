import asyncio
from datetime import datetime, timedelta, timezone

from database import Base, async_engine, async_session_maker
from models import (
    User,
    Project,
    ProjectMember,
    Task,
    MemberRole,
    ProjectStatus,
    TaskStatus,
    TaskPriority,
)
from utils import hash_password



async def seed_data():
    """
    Функция для заполнения базы данных начальными данными, сначала удаляя все старые данные и таблицы, а затем создает их заново.
    """

    print("{INFO} Удаление и пересоздание всех таблиц...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("{INFO} Таблицы успешно пересозданы.")

    async with async_session_maker() as session:
        async with session.begin():
            print("{INFO} Заполнение базы данных...")

            user_alice = User(
                username="alice",
                email="alice@example.com",
                password_hash=hash_password("password123"),
            )
            user_bob = User(
                username="bob",
                email="bob@example.com",
                password_hash=hash_password("password456"),
            )
            user_charlie = User(
                username="charlie",
                email="charlie@example.com",
                password_hash=hash_password("password789"),
            )
            session.add_all([user_alice, user_bob, user_charlie])

            await session.flush()
            print("{INFO} Созданы пользователи: Alice, Bob, Charlie.")

            project_phoenix = Project(
                name="Project Phoenix",
                description="Rebuilding the core infrastructure from scratch.",
                owner_id=user_alice.id,
                status=ProjectStatus.ACTIVE,
            )
            project_hydra = Project(
                name="Project Hydra",
                description="Data migration and legacy system shutdown.",
                owner_id=user_bob.id,
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

            session.add_all([
                Task(
                    project_id=project_phoenix.id,
                    title="Design new architecture",
                    description="Create diagrams for the new service-oriented architecture.",
                    status=TaskStatus.IN_PROGRESS,
                    priority=TaskPriority.CRITICAL,
                    assignee_id=user_alice.id,
                    creator_id=user_alice.id,
                ),
                Task(
                    project_id=project_phoenix.id,
                    title="Set up CI/CD pipeline",
                    description="Configure GitHub Actions for automated testing and deployment.",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    assignee_id=user_bob.id,
                    creator_id=user_alice.id,
                ),
                Task(
                    project_id=project_phoenix.id,
                    title="Review project documentation",
                    assignee_id=user_charlie.id,
                    creator_id=user_bob.id,
                ),  
                Task(
                    project_id=project_hydra.id,
                    title="Analyze legacy database",
                    assignee_id=user_bob.id,
                    creator_id=user_bob.id,
                )
            ])
            print("{INFO} Задачи созданы.")
        
        print("{INFO} База данных успешно заполнена.")


if __name__ == "__main__":
    asyncio.run(seed_data())
