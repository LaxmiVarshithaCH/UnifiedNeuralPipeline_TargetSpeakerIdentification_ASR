from fastapi import FastAPI, UploadFile, File, WebSocket
import uvicorn
import uuid, os, json
from mysql.connector import connect
from main import run_offline
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

def get_db():
    return connect(
        host="localhost",
        user="unify",
        password="password123",
        database="unified_pipeline"
    )

AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.post("/process")
async def process_audio(mixture: UploadFile = File(...), target: UploadFile = File(...)):
    job_id = str(uuid.uuid4())

    mix_path = f"{AUDIO_DIR}/{job_id}_mixture.wav"
    target_path = f"{AUDIO_DIR}/{job_id}_target.wav"

    with open(mix_path, "wb") as f:
        f.write(await mixture.read())
    with open(target_path, "wb") as f:
        f.write(await target.read())

    out_json = f"{AUDIO_DIR}/{job_id}_diarization.json"
    out_target_wav = f"{AUDIO_DIR}/{job_id}_target_speaker.wav"

    run_offline(
        mixture_path=mix_path,
        target_sample_path=target_path,
        out_json_path=out_json,
        out_target_wav=out_target_wav
    )

    result = json.load(open(out_json))

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO jobs (id, mixture_path, target_path, result_json_path, status) VALUES (%s,%s,%s,%s,%s)",
        (job_id, mix_path, target_path, out_json, "done")
    )
    db.commit()

    return {
        "jobId": job_id,
        "result": result
    }

@app.websocket("/ws/stream")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()  
            await ws.send_text("ack")
    except Exception as e:
        print("WebSocket closed:", e)
