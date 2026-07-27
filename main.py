from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3


app = FastAPI()

def init_db():
    # 1.connect to the file task.db (it will create if not exist)
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    # 2. create the table if not exists
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
            )
""")

    # 3. CHECK IF THE TABLE IS EMPTY
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    # 4. if empty insert the 3 default tasks
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Assignment 1", True),
                ("Assignment 2", True),
                ("Assignment 3", False),

            ]
        )

        conn.commit()

    conn.close()


init_db()


class TaskCreate(BaseModel):
    title:str


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None



@app.get("/")
def read_root():
    """Root endpoint that returns basic information about the API."""
    return {"name": "Task API", "version": "1.0", "endpoints": "/tasks"}

@app.get("/health")
def check_health():
    """Check the health of the API."""
    return {"status": "Ok"}

# Tasks
@app.get("/tasks")
def get_tasks():
    """Get a list of all tasks."""
    return task_db


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a task by its ID."""
    for task in task_db:
        if task["id"] == task_id:
            return task
        

    return JSONResponse(
        status_code = 404,
        content = {"error": f"Task {task_id} not found" }
    )


@app.post("/tasks", status_code= 201)
def create_task(task_data: TaskCreate):
    """Create a new task with the given title. The task will be marked as not done by default."""  

#we will manually check if the title is empty and return a 400 error if it is
    if not task_data.title.strip():
        return JSONResponse(
            status_code = 400,
            content = {"error": "Title cannot be empty"}
        )
    
#we will figure out the next id by getting the max id in the task_db and adding 1 to it

    new_id = 1 if not task_db else max(task["id"] for task in task_db) + 1

#new task
    new_task = {
        "id": new_id,
        "title": task_data.title,
        "done": False 
    }

    task_db.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    """Update the title and/or done status of a task with the given ID."""
    if task_update.title is None and task_update.done is None:
        return JSONResponse(
            status_code = 400,
            content = {"error": "Body cannot be empty"}
        )
    
    #loop to find the task
    for task in task_db:
        if task["id"] == task_id:
            if task_update.title is not None:
                if not task_update.title.strip():
                    return JSONResponse(
                        status_code = 400,
                        content = {"error": "Title cannot be empty"}
                    )
                task["title"] = task_update.title

        if task_update.done is not None:
            task["done"] = task_update.done

        return task
    
    return JSONResponse(
        status_code = 404,
        content = {"error": f"Task {task_id} not found"}
    )


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task with the given ID."""
    for task in task_db:
        if task["id"] == task_id:
            task_db.remove(task)
            return Response(status_code=204)
        
    return JSONResponse(
        status_code = 404,
        content = {"error": f"Task {task_id} not found"}
    )
                

    
