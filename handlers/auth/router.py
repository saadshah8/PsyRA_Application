from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from bson.objectid import ObjectId
from core.database import user_collection
from datetime import datetime
import hashlib

auth_router = APIRouter()
views = Jinja2Templates(directory="views")

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SettingsRequest(BaseModel):
    old_password: str
    name: str
    password: str | None

def hash_password(password: str) -> str:
    """Hash the password using SHA-256 for storage."""
    return hashlib.sha256(password.encode()).hexdigest()

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return views.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={}
    )

@auth_router.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = user_collection.find_one({"email": email})
    if not user or user["password"] != hash_password(password):
        return views.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Invalid email or password"}
        )
    
    user_id = str(user["_id"])
    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to retrieve user ID")
    return RedirectResponse(url=f"/app/{user_id}", status_code=303)

@auth_router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return views.TemplateResponse(
        request=request,
        name="auth/signup.html",
        context={}
    )

@auth_router.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if not password.strip():
        return views.TemplateResponse(
            request=request,
            name="auth/signup.html",
            context={"error": "Password is required"}
        )
    
    if user_collection.find_one({"email": email}):
        return views.TemplateResponse(
            request=request,
            name="auth/signup.html",
            context={"error": "Email already registered"}
        )
    
    user_data = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    result = user_collection.insert_one(user_data)
    user_id = str(result.inserted_id)
    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return RedirectResponse(url=f"/app/{user_id}", status_code=303)

@auth_router.get("/logout", response_class=RedirectResponse)
async def logout():
    return RedirectResponse(url="/auth/login", status_code=303)

@auth_router.get("/settings/{userId}", response_class=JSONResponse)
async def get_settings(userId: str):
    user = user_collection.find_one({"_id": ObjectId(userId)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user["name"]}

@auth_router.post("/settings/{userId}", response_class=RedirectResponse)
async def update_settings(userId: str, old_password: str = Form(...), name: str = Form(...), password: str = Form(default="")):
    user = user_collection.find_one({"_id": ObjectId(userId)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["password"] != hash_password(old_password):
        raise HTTPException(status_code=401, detail="Incorrect old password")
    
    update_data = {
        "name": name,
        "updatedAt": datetime.utcnow()
    }
    if password:
        update_data["password"] = hash_password(password)
    
    user_collection.update_one(
        {"_id": ObjectId(userId)},
        {"$set": update_data}
    )
    return RedirectResponse(url=f"/app/{userId}", status_code=303)