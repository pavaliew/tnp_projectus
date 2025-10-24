from app.database import SessionLocal, engine, Base
from app.models import User, Project, Task, ProjectMember
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    user1 = User(
        username="alice", 
        email="alice@example.com", 
        password_hash=pwd_context.hash("password123")
    )
    user2 = User(
        username="bob", 
        email="bob@example.com",        
        password_hash=pwd_context.hash("password123")
    )
    
    db.add_all([user1, user2])
    db.commit()
    
    project = Project(
        name="Website Redesign", 
        description="Redesign company website", 
        owner_id=user1.id
    )
    db.add(project)
    db.commit()
    
    member = ProjectMember(
        project_id=project.id, 
        user_id=user2.id, 
        role="member"
    )
    db.add(member)
    db.commit()
    
    task1 = Task(
        project_id=project.id, 
        title="Design mockups", 
        assignee_id=user2.id, 
        created_by=user1.id
    )
    task2 = Task(
        project_id=project.id, 
        title="Implement frontend", 
        assignee_id=user2.id, 
        created_by=user1.id
    )
    
    db.add_all([task1, task2])
    db.commit()
    
    print("[V] Test data seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed_data()
