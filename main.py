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
    conn = sqlite3.connect("tasks.db")

    # This magic line tells SQLite to return data like a Python dictionary
    # instead of a plain list of values. FastAPI needs this to make JSON!

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Get everything from the tasks table
    cursor.execute("SELECT * FROM tasks")

    # Grab the results

    tasks = cursor.fetchall()

    conn.close()

    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a task by its ID."""
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Speak SQL: "Get all columns from tasks where the ID matches this number"
    # The (?, ) safely injects the task_id into the SQL command

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id))

    #Grab just the one single row
    task = cursor.fetchone()
    conn.close()

    if task is None:
        return JSONResponse(
            status_code = 404,
            content = {"error": f"Task {task_id} not found" }
        )

    return task


@app.post("/tasks", status_code= 201)
def create_task(task_data: TaskCreate):
    """Create a new task with the given title. The task will be marked as not done by default."""  

#we will manually check if the title is empty and return a 400 error if it is
    if not task_data.title.strip():
        return JSONResponse(
            status_code = 400,
            content = {"error": "Title cannot be empty"}
        )
    
    #connect to the database
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    #Insert a new row into the tasks table
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task_data.title, False)
    )

    #save the changes permanently
    conn.commit()

    new_id = cursor.lastrowid

    # fetch the newly created task so we can return it to the user

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    new_task = cursor.fetchone()

    conn.close()

    return new_task()


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
                

    
