from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="MusiceID API")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MONGODB CONNECTION ---
MONGO_DETAILS = "mongodb+srv://sainicc01_db_user:wPKh8kwhDsU9PyBb@cluster0.y25sbxx.mongodb.net/?appName=Cluster0"

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.musice_db
song_collection = database.get_collection("songs")

# --- DATA MODELS ---
class SongSchema(BaseModel):
    song_id_string: str
    name: str
    img: str

class LoginSchema(BaseModel):
    password: str

# Helper to format MongoDB documents
def song_helper(song) -> dict:
    return {
        "song_id_string": str(song.get("song_id_string", "")),
        "name": str(song.get("name", "Unknown")),
        "img": str(song.get("img", "")),
    }

# --- ROUTES ---

@app.post("/login")
async def login(data: LoginSchema):
    if data.password == "1":
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/songs", response_model=List[SongSchema])
async def get_songs():
    songs = []
    async for song in song_collection.find():
        songs.append(song_helper(song))
    return songs

@app.post("/songs")
async def add_song(song: SongSchema):
    existing = await song_collection.find_one({"song_id_string": song.song_id_string})
    if existing:
        raise HTTPException(status_code=400, detail="Song ID already exists in library")
    
    song_data = song.model_dump() 
    await song_collection.insert_one(song_data)
    return {"message": "Success"}

@app.put("/songs/{song_id_string}")
async def update_song(song_id_string: str, updated_data: SongSchema):
    update_dict = updated_data.model_dump()
    update_result = await song_collection.update_one(
        {"song_id_string": song_id_string}, {"$set": update_dict}
    )
    if update_result.matched_count == 1:
        return {"message": "Updated"}
    raise HTTPException(status_code=404, detail="Song not found")

@app.delete("/songs/{song_id_string}")
async def delete_song(song_id_string: str):
    delete_result = await song_collection.delete_one({"song_id_string": song_id_string})
    if delete_result.deleted_count == 1:
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)