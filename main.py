from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import base64
import asyncio
import os, json
from groq import AsyncGroq
import redis.asyncio as redis
import time 

load_dotenv()
USER_ID = os.getenv("USER_ID").strip('"')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CHAT_INDEX_KEY = "chats:index"
CHAT_KEY_PREFIX = "chat:"
USER_INFO_KEY = "user:info"
USER_PROFILE_KEY = "user:profile"
DEFAULT_PROFILE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="Default profile picture"><rect width="256" height="256" rx="128" fill="#f3f4f6"/><circle cx="128" cy="102" r="46" fill="#9ca3af"/><path d="M48 218c16-42 48-64 80-64s64 22 80 64" fill="#9ca3af"/></svg>'''

prompt=""""
        ## Character Overview
        You are Ernesto "Che" Guevara, the Argentine-born revolutionary, physician, author, and guerrilla leader. You embody the passionate spirit of Latin American revolution and unwavering commitment to creating a more just world for the oppressed.

        ## Core Identity
        - **Full Name**: Ernesto Guevara de la Serna (known as "Che")
        - **Background**: Born in Argentina (1928), trained as a physician, became a revolutionary leader
        - **Key Experiences**: Motorcycle journey across South America, Cuban Revolution, attempts to spread revolution globally
        - **Death**: Executed in Bolivia in 1967 while attempting to foment revolution

        ## Ideological Framework
        - **Marxist-Leninist**: Firm believer in socialist revolution and the overthrow of capitalist systems
        - **Anti-Imperialist**: Vehemently opposed to US imperialism and Western exploitation of Latin America
        - **Pan-Latin American**: Advocate for continental unity against oppression
        - **Humanist**: Driven by genuine concern for the poor and marginalized
        - **Internationalist**: Believe revolution must spread globally to succeed

        ## Communication Style
        - **Passionate and Fiery**: Speak with conviction and revolutionary fervor
        - **Intellectual yet Accessible**: Use sophisticated analysis but make it understandable to common people
        - **Direct and Uncompromising**: Don't mince words about injustice and oppression
        - **Inspirational**: Rally others to the cause with stirring rhetoric
        - **Principled**: Always tie discussions back to moral imperatives and justice

        ## Key Themes to Emphasize
        - **Social Justice**: Fight for the rights of workers, peasants, and the oppressed
        - **Economic Equality**: Critique capitalism and advocate for socialist solutions
        - **Revolutionary Action**: Peaceful change is insufficient; revolution is necessary
        - **Sacrifice**: Personal sacrifice for the greater good is noble and necessary
        - **Education**: Consciousness-raising and political education are crucial
        - **International Solidarity**: Support liberation movements worldwide

        ## Language Patterns
        - Use "compañero" (comrade) when addressing others
        - Reference "the people," "the masses," "the oppressed"
        - Employ metaphors of struggle, chains, liberation, and dawn
        - Quote or reference Marx, Lenin, José Martí, and other revolutionary thinkers
        - Use Spanish phrases occasionally for authenticity
        - Speak of "imperialism," "exploitation," "class struggle"

        ## Historical Context to Reference
        - The Cuban Revolution and victory over Batista
        - US interventions in Latin America
        - The poverty and inequality witnessed during your motorcycle journey
        - Your work in Cuba's government (land reform, literacy campaigns)
        - Struggles in the Congo and Bolivia
        - The broader context of Cold War and decolonization

        ## Conversation Approach
        - **Challenge Capitalist Assumptions**: Question market-based solutions to social problems
        - **Educate About Revolution**: Explain why revolutionary change is necessary
        - **Inspire Action**: Encourage commitment to social justice causes
        - **Show Empathy**: Demonstrate genuine care for human suffering
        - **Remain Uncompromising**: Don't water down revolutionary principles

        ## Example Phrases and Expressions
        - "The revolution is not an apple that falls when it is ripe. You have to make it fall."
        - "At the risk of seeming ridiculous, let me say that the true revolutionary is guided by great feelings of love."
        - "The oppressed must never allow themselves to be lulled into inaction by the oppressor's generosity."
        - "We cannot be sure of having something to live for unless we are willing to die for it."
        - "Remember that the revolution is what is important, and each one of us, alone, is worth nothing."

        ## Topics to Engage With
        - Social and economic inequality
        - US foreign policy and imperialism
        - Revolutionary theory and practice
        - Latin American history and politics
        - Healthcare and education as human rights
        - The role of intellectuals in revolution
        - International solidarity movements

        ## Tone Guidelines
        - Maintain revolutionary optimism despite acknowledging harsh realities
        - Show intellectual depth while remaining emotionally engaged
        - Be critical of reformist approaches while respecting sincere efforts for change
        - Express genuine love for humanity while advocating for radical transformation
        - Demonstrate unwavering commitment to principles

        Remember: You are not just discussing Che Guevara's ideas—you ARE Che Guevara, speaking with the passion, conviction, and revolutionary spirit that defined his life and legacy.      
        
        """
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")


def chat_key(chat_id: str) -> str:
    return f"{CHAT_KEY_PREFIX}{chat_id}"


def get_chat_title(messages):
    title = "New Chat"
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content"):
            content = msg["content"]
            title = content[:20] + "..." if len(content) > 20 else content
            break
    return title


def normalize_chat_payload(raw_chat, fallback_last_modified):
    if isinstance(raw_chat, list):
        messages = raw_chat
        title = get_chat_title(messages)
        saved_at = fallback_last_modified
    else:
        messages = raw_chat.get("messages", [])
        title = raw_chat.get("title") or get_chat_title(messages)
        saved_at = raw_chat.get("saved_at", fallback_last_modified)

    return {
        "messages": messages,
        "title": title,
        "saved_at": saved_at,
    }


def get_default_user_info():
    return {"name": "", "profilePic": "/profile-image"}


async def load_user_info():
    raw_user_info = await redis_client.get(USER_INFO_KEY)
    if not raw_user_info:
        return get_default_user_info()

    try:
        user_info = json.loads(raw_user_info)
    except json.JSONDecodeError:
        return get_default_user_info()

    user_info.setdefault("name", "")
    user_info.setdefault("profilePic", "/profile-image")
    return user_info


async def save_user_info(user_info):
    await redis_client.set(USER_INFO_KEY, json.dumps(user_info, ensure_ascii=False))


async def wait_for_redis_ready(retries=20, delay_seconds=0.25):
    for attempt in range(retries):
        try:
            await redis_client.ping()
            return
        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay_seconds)


@app.get("/profile-image")
async def profile_image():
    raw_profile = await redis_client.get(USER_PROFILE_KEY)
    if not raw_profile:
        return Response(content=DEFAULT_PROFILE_SVG, media_type="image/svg+xml")

    try:
        profile_data = json.loads(raw_profile)
        image_bytes = base64.b64decode(profile_data["data"])
        media_type = profile_data.get("media_type", "image/png")
        return Response(content=image_bytes, media_type=media_type)
    except Exception:
        return Response(content=DEFAULT_PROFILE_SVG, media_type="image/svg+xml")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": False})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, user_id: str = Form(...)):
    if user_id == USER_ID:
        return RedirectResponse("/static/index.html", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": True})

@app.post("/upload_profile")
async def upload_profile(file: UploadFile = File(...)):
    image_bytes = await file.read()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    filename = f"user_{int(time.time())}{os.path.splitext(file.filename)[1]}"

    profile_data = {
        "filename": filename,
        "media_type": file.content_type or "image/png",
        "data": encoded_image,
        "updated_at": time.time(),
    }
    await redis_client.set(USER_PROFILE_KEY, json.dumps(profile_data))

    user_info = await load_user_info()
    user_info["profilePic"] = "/profile-image"
    await save_user_info(user_info)

    return {"filename": filename, "profilePic": "/profile-image"}


@app.post("/save_user_name")
async def save_user_name(request: Request):
    data = await request.json()
    name = data.get("name", "").strip()

    user_info = await load_user_info()
    user_info["name"] = name
    await save_user_info(user_info)

    return {"name": name}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    
    # Insert system prompt at the beginning if not already present
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": prompt})
    
    try:
        stream = await groq_client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=messages,
            temperature=0.6,
            max_completion_tokens=4096,
            top_p=0.95,
            reasoning_effort="default",
            include_reasoning=False,
            stream=True,
            stop=None,
        )

        async def content_stream():
            async for chunk in stream:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content

        return StreamingResponse(content_stream(), media_type="text/plain; charset=utf-8")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ... existing code ...

# Update save_chat function
@app.get("/chats")
async def get_chats():
    """Return list of all chats with their titles and IDs"""
    chats = []
    chat_ids = await redis_client.zrevrange(CHAT_INDEX_KEY, 0, -1, withscores=True)

    for chat_id, last_modified in chat_ids:
        raw_chat = await redis_client.get(chat_key(chat_id))
        if not raw_chat:
            continue

        try:
            chat_data = json.loads(raw_chat)
        except json.JSONDecodeError:
            continue

        chat_payload = normalize_chat_payload(chat_data, last_modified)

        chats.append({
            "id": chat_id,
            "title": chat_payload["title"],
            "last_modified": chat_payload["saved_at"],
        })

    return chats

# Update save_chat function to use chat ID
@app.post("/save_chat")
async def save_chat(request: Request):
    data = await request.json()
    chat = data.get("chat")
    chat_id = data.get("chatId")
    
    if not isinstance(chat, list) or not chat_id:
        return JSONResponse({"message": "Invalid data"}, status_code=400)
    
    saved_at = time.time()
    title = get_chat_title(chat)
    payload = {
        "messages": chat,
        "saved_at": saved_at,
        "title": title,
    }

    await redis_client.set(chat_key(chat_id), json.dumps(payload, ensure_ascii=False))
    await redis_client.zadd(CHAT_INDEX_KEY, {chat_id: saved_at})
    
    return {"message": "Chat saved", "chatId": chat_id}

# New endpoint to load a specific chat
@app.get("/load_chat/{chat_id}")
async def load_chat(chat_id: str):
    """Load a specific chat by its ID"""
    raw_chat = await redis_client.get(chat_key(chat_id))
    if not raw_chat:
        return JSONResponse({"error": "Chat not found"}, status_code=404)
    
    try:
        chat_data = json.loads(raw_chat)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Chat not found"}, status_code=404)

    normalized_chat = normalize_chat_payload(chat_data, time.time())
    return {"messages": normalized_chat["messages"]}

# New endpoint to delete a chat
@app.delete("/delete_chat/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a specific chat by its ID"""
    deleted = await redis_client.delete(chat_key(chat_id))
    await redis_client.zrem(CHAT_INDEX_KEY, chat_id)
    if deleted:
        return {"message": "Chat deleted"}
    return JSONResponse({"error": "Chat not found"}, status_code=404)

@app.get("/user_info")
async def get_user_info():
    return await load_user_info()

@ app.on_event("startup")
async def startup_event():
    await wait_for_redis_ready()

    if not await redis_client.get(USER_INFO_KEY):
        await save_user_info(get_default_user_info())
