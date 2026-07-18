from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel


app = FastAPI()

task_db = [
    {"id": 1, "title": "Assingment 1", "done": True},
    {"id": 2, "title": "Assignment 2", "done": False},
    {"id": 3, "title": "Assignment 3", "done": False}
]

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
                

    
