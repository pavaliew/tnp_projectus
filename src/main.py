from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import timedelta

import orm
import schemas
import utils
import security
import models
from database import get_async_session, async_engine, Base
from config import settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Обработчик жизненного цикла приложения.
    """

    print("Application startup... Creating database tables.")
    async with async_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    print("Application shutdown.")



app = FastAPI(title="Task Management API", lifespan=lifespan)



@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    user = await orm.get_user_by_username(db, username=form_data.username)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



@app.post("/users/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_session)):
    db_user = await orm.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await orm.create_user(db=db, user=user)



@app.get("/users/me/", response_model=schemas.UserRead)
async def read_users_me(current_user: models.User = Depends(security.get_current_active_user)):
    return current_user



@app.get("/users/", response_model=List[schemas.UserRead])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)):
    users = await orm.get_users(db, skip=skip, limit=limit)
    return users



@app.post("/projects/", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_async_session), current_user: models.User = Depends(security.get_current_active_user)):
    return await orm.create_project(db=db, project=project, owner_id=current_user.id)



@app.get("/projects/", response_model=List[schemas.ProjectWithDetails])
async def read_projects(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)):
    projects = await orm.get_projects(db, skip=skip, limit=limit)
    return projects



@app.get("/projects/{project_id}", response_model=schemas.ProjectWithDetails)
async def read_project(project_id: int, db: AsyncSession = Depends(get_async_session)):
    db_project = await orm.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project



@app.post("/tasks/", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: schemas.TaskCreate, db: AsyncSession = Depends(get_async_session), current_user: models.User = Depends(security.get_current_active_user)):
    return await orm.create_task(db=db, task=task, author_id=current_user.id)



@app.get("/tasks/{task_id}", response_model=schemas.TaskReadWithDetails)
async def read_task(task_id: int, db: AsyncSession = Depends(get_async_session)):
    db_task = await orm.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task



@app.put("/tasks/{task_id}", response_model=schemas.TaskRead)
async def update_task(task_id: int, task: schemas.TaskUpdate, db: AsyncSession = Depends(get_async_session), current_user: models.User = Depends(security.get_current_active_user)):
    db_task = await orm.update_task(db=db, task_id=task_id, task_data=task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task



@app.post("/tasks/{task_id}/assign", response_model=schemas.TaskRead)
async def assign_user_to_task(task_id: int, user_id: int, db: AsyncSession = Depends(get_async_session), current_user: models.User = Depends(security.get_current_active_user)):
    db_task = await orm.assign_user_to_task(db, task_id, user_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task or User not found")
    return db_task



@app.post("/tasks/{task_id}/comments/", response_model=schemas.CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment_for_task(task_id: int, comment: schemas.CommentCreate, db: AsyncSession = Depends(get_async_session), current_user: models.User = Depends(security.get_current_active_user)):
    return await orm.create_comment(db=db, comment=comment, task_id=task_id, author_id=current_user.id)



@app.get("/tasks/{task_id}/comments/", response_model=List[schemas.CommentRead])
async def read_comments_for_task(task_id: int, db: AsyncSession = Depends(get_async_session)):
    comments = await orm.get_comments_for_task(db, task_id=task_id)
    return comments



@app.get("/")
async def read_root():
    return {"message": "Welcome to the Task Management API"}
