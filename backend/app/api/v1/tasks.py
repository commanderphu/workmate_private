"""
Task management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from ...db.session import get_db
from ...schemas import TaskCreate, TaskUpdate, TaskResponse
from ...models import User, Task
from ..dependencies import get_current_user
from ...services.task_event_mapping_service import TaskEventMappingService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all tasks for current user
    """
    query = db.query(Task).filter(Task.user_id == current_user.id)

    # Filter by status if provided
    if status_filter:
        query = query.filter(Task.status == status_filter)

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new task

    If task has a due_date, a calendar event will be automatically created.
    """
    new_task = Task(
        user_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        priority=task_data.priority,
        amount=task_data.amount,
        currency=task_data.currency,
        document_id=task_data.document_id,
        parent_task_id=task_data.parent_task_id,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Automatically create calendar event if task has due_date
    if new_task.due_date:
        mapping_service = TaskEventMappingService(db)
        mapping_service.create_event_from_task(new_task)
        db.refresh(new_task)

    return new_task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific task
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: uuid.UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a task

    Calendar event will be automatically updated if task has due_date changes.
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Update fields
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Update completed_at timestamp if status changed to done
    if task_data.status == "done" and not task.completed_at:
        task.completed_at = datetime.utcnow()
    elif task_data.status and task_data.status != "done":
        task.completed_at = None

    db.commit()
    db.refresh(task)

    # Automatically update/create/delete calendar event based on due_date
    mapping_service = TaskEventMappingService(db)
    mapping_service.update_event_from_task(task)
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a task
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    return None
