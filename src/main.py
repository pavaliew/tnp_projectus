from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import uvicorn

from repository import Repository
from models import User, MemberRole
import schemas
import security
from utils import verify_password
from config import settings



app = FastAPI(title="Project Management API")



@app.post("/register", response_model=schemas.UserRead, status_code=201)
async def register_user(user_data: schemas.UserCreate):
    """Регистрация нового пользователя."""
    existing_user = await Repository.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    new_user = await Repository.create_user(data=user_data)
    return new_user




@app.post("/auth/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Аутентификация пользователя и выдача JWT токена."""
    user = await Repository.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "id": user.id, "username": user.username},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/users/me", response_model=schemas.UserRead)
async def read_users_me(current_user: User = Depends(security.get_current_user)):
    """Получение информации о текущем пользователе."""
    return current_user



@app.get("/projects", response_model=List[schemas.ProjectRead])
async def get_user_projects(current_user: User = Depends(security.get_current_user)):
    """Получить список проектов текущего пользователя."""
    print(current_user.id, current_user.email)
    return await Repository.get_projects_for_user(current_user.id)



@app.post("/projects", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project_data: schemas.ProjectCreate,
    current_user: User = Depends(security.get_current_user)
):
    """Создать новый проект."""
    return await Repository.create_project(current_user.id, project_data)



@app.get("/projects/{project_id}", response_model=schemas.ProjectReadWithDetails)
async def get_project_details(project_id: int, current_user: User = Depends(security.get_current_user)):
    """Получить детальную информацию о проекте (с досками и задачами)."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project



@app.patch("/projects/{project_id}", response_model=schemas.ProjectRead)
async def update_project_partial(
    project_id: int,
    project_data: schemas.ProjectUpdate,
    current_user: User = Depends(security.get_current_user)
):
    """Частично обновить проект."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project or current_user.id not in [member.user_id for member in project.members if member.role == MemberRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    updated_project = await Repository.update_project(project_id, project_data)
    if not updated_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return updated_project



@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_by_id(project_id: int, current_user: User = Depends(security.get_current_user)):
    """Удалить проект."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project or current_user.id not in [member.user_id for member in project.members if member.role == MemberRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not await Repository.delete_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")



@app.get("/projects/{project_id}/members", response_model=List[schemas.ProjectMemberRead])
async def get_project_members_list(project_id: int, current_user: User = Depends(security.get_current_user)):
    """Получить список участников проекта."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project or current_user.id not in [member.user_id for member in project.members if member.role == MemberRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return await Repository.get_project_members(project_id)



@app.post("/{project_id}/members", response_model=schemas.ProjectMemberRead, status_code=201)
async def add_project_member(
    project_id: int,
    member_data: schemas.ProjectMemberCreate,
    current_user: User = Depends(security.get_current_user)
):
    """Добавление участника в проект."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project or current_user.id not in [member.user_id for member in project.members if member.role == MemberRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user_to_add = await Repository.get_user_by_id(member_data.user_id) 
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User to add not found")

    new_member = await Repository.add_project_member(project_id, member_data)
    return new_member



@app.delete("/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_project(
    project_id: int, user_id: int, current_user: User = Depends(security.get_current_user)
):
    """Удалить участника из проекта."""

    project = await Repository.get_project_with_details(project_id)
    if not project or current_user.id not in [member.user_id for member in project.members if member.role == MemberRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not await Repository.remove_project_member(project_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in project")



@app.post("/projects/{project_id}/boards", response_model=schemas.BoardRead, status_code=status.HTTP_201_CREATED)
async def create_new_board_in_project(
    project_id: int,
    board_data: schemas.BoardCreate,
    current_user: User = Depends(security.get_current_user)
):
    """Создать новую доску в проекте."""

    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    return await Repository.create_board(project_id, board_data)



@app.patch("/projects/{project_id}/boards/{board_id}", response_model=schemas.BoardRead)
async def update_board_partial(
    project_id: int,
    board_id: int,
    board_data: schemas.BoardUpdate,
    current_user: User = Depends(security.get_current_user)
):
    """Частично обновить доску (например, переименовать или переместить)."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    updated_board = await Repository.update_board(board_id, board_data)
    
    if not updated_board:
        raise HTTPException(status_code=404, detail="Board not found")

    updated_board = await Repository.update_board(board_id, board_data)
    if not updated_board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return updated_board



@app.delete("/projects/{project_id}/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board_by_id(
    project_id: int, 
    board_id: int, 
    current_user: User = Depends(security.get_current_user)
):
    """Удалить доску."""
    
    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    if not await Repository.delete_board(board_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")



@app.post("/projects/{project_id}/boards/{board_id}/tasks", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
async def create_new_task_on_board(
    project_id: int,
    board_id: int,
    task_data: schemas.TaskCreate,
    current_user: User = Depends(security.get_current_user)
):
    """Создать новую задачу на доске."""

    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    board = await Repository.get_board_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    project = await Repository.get_project_with_details(board.project_id)
    member_ids = [member.user_id for member in project.members]
    if current_user.id not in member_ids:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    if task_data.assignee_id and task_data.assignee_id not in member_ids:
        raise HTTPException(status_code=409, detail="Assignee is not a member of this project")

    new_task = await Repository.create_task(board_id, task_data)
    return new_task



@app.get("/projects/{project_id}/boards/{board_id}/tasks{task_id}", response_model=schemas.TaskRead)
async def get_task_details(
    project_id: int,
    board_id: int,
    task_id: int, 
    current_user: User = Depends(security.get_current_user)
):
    """Получить детальную информацию о задаче."""

    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    board = await Repository.get_board_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    task = await Repository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task



@app.patch("/projects/{project_id}/boards/{board_id}/tasks{task_id}", response_model=schemas.TaskRead)
async def update_task_partial(
    project_id: int,
    board_id: int,
    task_id: int,
    task_data: schemas.TaskUpdate,
    current_user: User = Depends(security.get_current_user)
):
    """Частично обновить задачу."""

    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    board = await Repository.get_board_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    updated_task = await Repository.update_task(task_id, task_data)
    if not updated_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated_task



@app.delete("/projects/{project_id}/boards/{board_id}/tasks{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_id(
    project_id: int,
    board_id: int,
    task_id: int, 
    current_user: User = Depends(security.get_current_user)
):
    """Удалить задачу."""

    project = await Repository.get_project_with_details(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = next((m for m in project.members if m.user_id == current_user.id), None)
    
    if not membership or membership.role not in [MemberRole.OWNER, MemberRole.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an OWNER or MEMBER"
        )

    board = await Repository.get_board_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    if not await Repository.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)