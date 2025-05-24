from fastapi import FastAPI
import uvicorn
from fastapi.staticfiles import StaticFiles
from handlers.app.ama.router import chats_router
from handlers.home.router import home_router
from handlers.auth.router import auth_router
from handlers.app.setting.router import settings_router
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
load_dotenv()

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Chat router
app.include_router(
    chats_router,
    prefix="/app/{userId}/chats",
    tags=["Chats"]
)

# Chat router
app.include_router(
    settings_router,
    prefix="/app/{userId}/settings",
    tags=["settings"]
)

# Auth router
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"]
)

# Home router
app.include_router(
    home_router,
    prefix="/app",
    tags=["Home"]
)

@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login", status_code=303)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    # uvicorn.run(app, host="0.0.0.0", port=8000)