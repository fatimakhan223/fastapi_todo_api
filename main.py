import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel



# Load the variables from your .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

# Helper function to open a Postgres connection
def get_db_connection():
    # RealDictCursor makes Postgres return data as dictionaries (just like sqlite3.Row did)
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    # --- NEW RETRY LOGIC ---
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            break  # If successful, break out of the loop!
        except psycopg2.OperationalError:
            print(f"Database not ready yet, retrying in 2 seconds... ({retries} attempts left)")
            time.sleep(2)
            retries -= 1
            
    if retries == 0:
        raise Exception("Could not connect to the database after 5 attempts.")
    # -----------------------

    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()['count']
    
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("Assignment 1", True), 
                ("Assignment 2", False), 
                ("Assignment 3", False)
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a task by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Speak SQL: "Get all columns from tasks where the ID matches this number"

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))

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
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert a new row into the tasks table AND return the new id
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
        (task_data.title, False)
    )
    
    new_id = cursor.fetchone()['id']
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (new_id,))
    new_task = cursor.fetchone()
    conn.close()
    
    return new_task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    if task_update.title is None and task_update.done is None:
        return JSONResponse(status_code=400, content={"error": "Body cannot be empty"})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    if cursor.fetchone() is None:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    
    if task_update.title is not None:
        if not task_update.title.strip():
            conn.close()
            return JSONResponse(status_code=400, content={"error": "Title cannot be empty"})
        cursor.execute("UPDATE tasks SET title = %s WHERE id = %s", (task_update.title, task_id))
        
    if task_update.done is not None:
        cursor.execute("UPDATE tasks SET done = %s WHERE id = %s", (task_update.done, task_id))
        
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    updated_task = cursor.fetchone()
    conn.close()
    
    return updated_task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
    if cursor.fetchone() is None:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    
    return Response(status_code=204)