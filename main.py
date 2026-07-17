from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

task_db = [
    {"id": 1, "title": "Assingment 1", "done": True},
    {"id": 2, "title": "Assignment 2", "done": False},
    {"id": 3, "title": "Assignment 3", "done": False}
]


@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": "/tasks"}

@app.get("/health")
def check_health():
    return {"status": "Ok"}

# Tasks
@app.get("/tasks")
def get_tasks():
    return task_db


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in task_db:
        if task["id"] == task_id:
            return task
        

    return JSONResponse(
        status_code = 404,
        content = {"error": f"Task {task_id} not found" }
    )

