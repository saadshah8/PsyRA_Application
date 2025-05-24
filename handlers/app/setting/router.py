from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from bson.objectid import ObjectId
from core.database import user_collection

# Initialize router and templates
settings_router = APIRouter()
views = Jinja2Templates(directory="views")

# Route to display the settings page
@settings_router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, userId: str):
    # Verify user exists
    user = user_collection.find_one({"_id": ObjectId(userId)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return views.TemplateResponse(
        request=request,
        name="setting/settings.html",
        context={
            "userId": userId,
            "user_name": user.get("name", "User")
        }
    )