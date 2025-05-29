from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from core.agent import Agent
from datetime import datetime
from bson.objectid import ObjectId
from core.database import conversations, user_collection
from typing import Optional
from modules.psyra_promptl4 import PSYRA_PROMPT

chats_router = APIRouter()
views = Jinja2Templates(directory="views")

class ChatMessageRequest(BaseModel):
    message: str

class ChatCreateRequest(BaseModel):
    title: str = "New Chat"

class ChatRenameRequest(BaseModel):
    title: str

def convert_mongo_doc(doc):
    if isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    elif isinstance(doc, dict):
        return {k: convert_mongo_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_mongo_doc(v) for v in doc]
    return doc

@chats_router.get("", response_class=HTMLResponse)
async def chats_page(request: Request, userId: str):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user = user_collection.find_one({"_id": ObjectId(userId)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    chats = list(conversations.find(
        {"userId": ObjectId(userId)},
        {"title": 1, "createdAt": 1, "updatedAt": 1, "session_index": 1}
    ).sort("updatedAt", -1))
    
    for chat in chats:
        chat["_id"] = str(chat["_id"])
        chat["createdAt"] = chat["createdAt"].strftime('%Y-%m-%d %H:%M')
        chat["updatedAt"] = chat["updatedAt"].strftime('%Y-%m-%d %H:%M')
    
    return views.TemplateResponse(
        request=request,
        name="ama/chat.html",
        context={
            "userId": userId,
            "user_name": user.get("name", "User"),
            "chats": chats
        }
    )

@chats_router.get("/{chat_id}", response_class=HTMLResponse)
async def chats_page_with_chat_id(request: Request, userId: str, chat_id: str):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user = user_collection.find_one({"_id": ObjectId(userId)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    chats = list(conversations.find(
        {"userId": ObjectId(userId)},
        {"title": 1, "createdAt": 1, "updatedAt": 1, "session_index": 1}
    ).sort("updatedAt", -1))
    
    for chat in chats:
        chat["_id"] = str(chat["_id"])
        chat["createdAt"] = chat["createdAt"].strftime('%Y-%m-%d %H:%M')
        chat["updatedAt"] = chat["updatedAt"].strftime('%Y-%m-%d %H:%M')
    
    return views.TemplateResponse(
        request=request,
        name="ama/chat.html",
        context={
            "userId": userId,
            "user_name": user.get("name", "User"),
            "chats": chats,
            "current_chat_id": chat_id
        }
    )

@chats_router.get("/{chat_id}/messages", response_class=JSONResponse)
async def get_chat_messages(userId: str, chat_id: str):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    chat = conversations.find_one({
        "_id": ObjectId(chat_id),
        "userId": ObjectId(userId)
    })
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return convert_mongo_doc(chat)

@chats_router.post("", response_class=JSONResponse)
async def create_new_chat(userId: str, request: ChatCreateRequest):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Find the highest session_index for the user
    latest_chat = conversations.find_one(
        {"userId": ObjectId(userId)},
        sort=[("session_index", -1)]
    )
    next_session_index = (latest_chat["session_index"] + 1) if latest_chat and "session_index" in latest_chat else 1
    
    chat_data = {
        "userId": ObjectId(userId),
        "title": f"Session {next_session_index}",
        "session_index": next_session_index,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "messages": []
    }
    
    result = conversations.insert_one(chat_data)
    return {"chat_id": str(result.inserted_id)}

@chats_router.patch("/{chat_id}", response_class=JSONResponse)
async def rename_chat(userId: str, chat_id: str, request: ChatRenameRequest):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    chat = conversations.find_one({
        "_id": ObjectId(chat_id),
        "userId": ObjectId(userId)
    })
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    conversations.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"title": request.title, "updatedAt": datetime.utcnow()}}
    )
    
    return {"message": "Chat renamed successfully", "title": request.title}

# RECENT_MESSAGE_LIMIT = 8

@chats_router.post("/{chat_id}/message_send", response_class=JSONResponse)
async def send_chat_message(userId: str, chat_id: str, request: ChatMessageRequest):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    if not user_collection.find_one({"_id": ObjectId(userId)}):
        raise HTTPException(status_code=404, detail="User not found")
    
    chat = conversations.find_one({
        "_id": ObjectId(chat_id),
        "userId": ObjectId(userId)
    })
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    agent = Agent()
    agent.set_user_id(userId)
    agent.system_prompt(PSYRA_PROMPT)

    # Load recent messages for context
    # recent_messages = chat["messages"][-RECENT_MESSAGE_LIMIT:] # load previous limited messages
    recent_messages = chat["messages"][:] # load all messages

    for msg in recent_messages:
        agent.messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Get response and original user message
    response, original_user_message = agent.chat(request.message)
    
    # Store messages in MongoDB
    user_message = {
        "role": "user",
        "content": original_user_message,  # Store only the user's input
        "createdAt": datetime.utcnow()
    }
    
    ai_message = {
        "role": "assistant",
        "content": response,
        "createdAt": datetime.utcnow()
    }
    
    # Update chat title if this is the first message
    update_data = {
        "$push": {"messages": {"$each": [user_message, ai_message]}},
        "$set": {"updatedAt": datetime.utcnow()}
    }
    
    if len(chat["messages"]) == 0 and "session_index" not in chat:
        # This should not typically happen since session_index is set at creation,
        # but as a fallback, we can set it here
        latest_chat = conversations.find_one(
            {"userId": ObjectId(userId), "_id": {"$ne": ObjectId(chat_id)}},
            sort=[("session_index", -1)]
        )
        next_session_index = (latest_chat["session_index"] + 1) if latest_chat and "session_index" in latest_chat else 1
        update_data["$set"]["title"] = f"Session {next_session_index}"
        update_data["$set"]["session_index"] = next_session_index
    
    conversations.update_one(
        {"_id": ObjectId(chat_id)},
        update_data
    )
    
    return {
        "role": "assistant",
        "content": response,
        "chat_id": chat_id
    }

@chats_router.delete("/{chat_id}", response_class=JSONResponse)
async def delete_chat(userId: str, chat_id: str):
    if not userId or userId.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    result = conversations.delete_one({
        "_id": ObjectId(chat_id),
        "userId": ObjectId(userId)
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}