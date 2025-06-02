from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.task import TaskCreate, TaskOut
from app.cruds.task import create_task
from app.celery.tasks import parse_url_task

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/parse-url", response_model=TaskOut)
def parse_url(data: TaskCreate, db: Session = Depends(get_db)):
    task = create_task(db, url=data.url)
    parse_url_task.delay(task.id, data.url, data.client_id)
    return task