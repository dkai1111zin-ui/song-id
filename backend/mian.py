from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List

app = FastAPI(title="MusiceID API 🎀")

# --- CORS SETTINGS ---
# This allows your pink coquette frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MONGODB CONNECTION ---
# Using your provided MongoDB string
MONGO_DETAILS = "mongodb+srv://sainicc01_db_user:wPKh8kwhDsU9PyBb@cluster0.y25sbxx.mongodb.net/?appName=Cluster0"

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.musice_db
song_collection = database.get_collection("songs")

# --- DATA MODELS ---
class SongSchema(BaseModel):
    song_id_string: str
    name: str
    img: str  # This handles both URLs and Base64 Uploaded images

class LoginSchema(BaseModel):
    password: str

# Helper to format MongoDB data for the frontend
def song_helper(song) -> dict:
    return {
        "song_id_string": str(song.get("song_id_string", "")),
        "name": str(song.get("name", "Unknown Melody")),
        "img": str(song.get("img", "")),
    }

# --- ROUTES ---

# 1. Health Check (Required for Render to show "Live")
@app.get("/")
async def root():
    return {
        "status": "online", 
        "message": "MusiceID API is running beautifully ✨",
        "hint": "Check /songs to see the library!"
    }

# 2. Admin Login
@app.post("/login")
async def login(data: LoginSchema):
    # Your secret password is "1"
    if data.password == "1":
        return {"message": "Login successful, bestie! 🎀"}
    raise HTTPException(status_code=401, detail="Wrong password! 🌸")

# 3. Get All Songs (Library View)
@app.get("/songs", response_model=List[SongSchema])
async def get_songs():
    songs = []
    async for song in song_collection.find():
        songs.append(song_helper(song))
    return songs

# 4. Add New Song (Admin Only)
@app.post("/songs")
async def add_song(song: SongSchema):
    # Check if ID already exists
    existing = await song_collection.find_one({"song_id_string": song.song_id_string})
    if existing:
        raise HTTPException(status_code=400, detail="This ID is already in the library! 🎀")
    
    song_data = song.model_dump() 
    await song_collection.insert_one(song_data)
    return {"message": "Song added successfully ✨"}

# 5. Update Existing Song (Admin Only)
@app.put("/songs/{song_id_string}")
async def update_song(song_id_string: str, updated_data: SongSchema):
    update_dict = updated_data.model_dump()
    update_result = await song_collection.update_one(
        {"song_id_string": song_id_string}, {"$set": update_dict}
    )
    if update_result.matched_count == 1:
        return {"message": "Melody updated! 🌸"}
    raise HTTPException(status_code=404, detail="Song not found")

# 6. Delete Song (Admin Only)
@app.delete("/songs/{song_id_string}")
async def delete_song(song_id_string: str):
    delete_result = await song_collection.delete_one({"song_id_string": song_id_string})
    if delete_result.deleted_count == 1:
        return {"message": "Melody deleted from library 👋"}
    raise HTTPException(status_code=404, detail="Song not found")