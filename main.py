from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os, json, shutil
from datetime import datetime
from pathlib import Path
from groq import Groq
import time 

load_dotenv()
USER_ID = os.getenv("USER_ID").strip('"')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

CHAT_DIR = Path("chat")
CHAT_DIR.mkdir(exist_ok=True)
USER_INFO_FILE = Path("profile") / "user_info.json"

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
app.mount("/profile", StaticFiles(directory="profile"), name="profile")
templates = Jinja2Templates(directory="frontend")
Path("chat").mkdir(exist_ok=True)
Path("profile").mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": False})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, user_id: str = Form(...)):
    if user_id == USER_ID:
        return RedirectResponse("/static/index.html", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": True})

@app.post("/upload_profile")
async def upload_profile(file: UploadFile = File(...)):
    # Delete existing profile images (except user_info.json)
    for f in Path("profile").glob("*"):
        if f.is_file() and f.name != "user_info.json":
            f.unlink()
    
    # Save new image with timestamped filename
    filename = f"user_{int(time.time())}{Path(file.filename).suffix}"
    path = Path("profile") / filename
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user info with new profile pic
    user_info = {}
    if USER_INFO_FILE.exists():
        with open(USER_INFO_FILE, "r") as f:
            user_info = json.load(f)
    
    user_info["profile_pic"] = filename
    
    with open(USER_INFO_FILE, "w") as f:
        json.dump(user_info, f)
    
    return {"filename": filename}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    
    # Insert system prompt at the beginning if not already present
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": prompt})
    
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=messages
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ... existing code ...

# Update save_chat function
@app.get("/chats")
async def get_chats():
    """Return list of all chats with their titles and IDs"""
    chats = []
    for file in CHAT_DIR.glob("*.json"):
        with open(file, "r") as f:
            try:
                chat_data = json.load(f)
                # Extract first user message for title
                title = "New Chat"
                for msg in chat_data.get("messages", []):
                    if msg["role"] == "user":
                        title = msg["content"][:20] + "..." if len(msg["content"]) > 20 else msg["content"]
                        break
                chats.append({
                    "id": file.stem,
                    "title": title,
                    "last_modified": os.path.getmtime(file)
                })
            except json.JSONDecodeError:
                continue
    # Sort by last modified (newest first)
    chats.sort(key=lambda x: x["last_modified"], reverse=True)
    return {"chats": chats}

# Update save_chat function to use chat ID
@app.post("/save_chat")
async def save_chat(request: Request):
    data = await request.json()
    chat = data.get("chat")
    chat_id = data.get("chatId")
    
    if not chat or not chat_id:
        return JSONResponse({"message": "Invalid data"}, status_code=400)
    
    # Save chat with ID-based filename
    filename = f"{chat_id}.json"
    with open(CHAT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2, ensure_ascii=False)
    
    return {"message": "Chat saved", "filename": filename}

# New endpoint to load a specific chat
@app.get("/load_chat/{chat_id}")
async def load_chat(chat_id: str):
    """Load a specific chat by its ID"""
    chat_file = CHAT_DIR / f"{chat_id}.json"
    if not chat_file.exists():
        return JSONResponse({"error": "Chat not found"}, status_code=404)
    
    with open(chat_file, "r") as f:
        chat_data = json.load(f)
    
    return {"messages": chat_data}

# New endpoint to delete a chat
@app.delete("/delete_chat/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a specific chat by its ID"""
    chat_file = CHAT_DIR / f"{chat_id}.json"
    if chat_file.exists():
        chat_file.unlink()
        return {"message": "Chat deleted"}
    return JSONResponse({"error": "Chat not found"}, status_code=404)

# Update upload_profile to maintain single image
@app.post("/upload_profile")
async def upload_profile(file: UploadFile = File(...)):
    # Delete existing profile images
    for f in Path("profile").glob("*"):
        if f.is_file() and f.name != "user_info.json":
            f.unlink()
    
    # Save new image with timestamped filename
    filename = f"user_{int(time.time())}{Path(file.filename).suffix}"
    path = Path("profile") / filename
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user info with new profile pic
    user_info = {}
    if USER_INFO_FILE.exists():
        with open(USER_INFO_FILE, "r") as f:
            user_info = json.load(f)
    
    user_info["profile_pic"] = filename
    
    with open(USER_INFO_FILE, "w") as f:
        json.dump(user_info, f)
    
    return {"filename": filename}

# Update user_info to include profile picture
@app.get("/user_info")
async def get_user_info():
    if USER_INFO_FILE.exists():
        with open(USER_INFO_FILE, "r") as f:
            return json.load(f)
    return {"name": "", "profile_pic": ""}

@ app.on_event("startup")
async def startup_event():
    # Ensure user_info.json exists
    if not USER_INFO_FILE.exists():
        with open(USER_INFO_FILE, "w") as f:
            json.dump({"name": "", "profile_pic": ""}, f)
    
    # Ensure chat directory exists
    CHAT_DIR.mkdir(exist_ok=True)
    
    # Ensure profile directory exists
    Path("profile").mkdir(exist_ok=True)
