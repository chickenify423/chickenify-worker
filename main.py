<<<<<<< HEAD
import os, io, tempfile, json, subprocess
from fastapi import FastAPI, UploadFile, Form, Header
from fastapi.responses import JSONResponse
import boto3, soundfile as sf, numpy as np
from ddsp_infer import render_chicken

WORKER_API_KEY = os.getenv("WORKER_API_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
S3_KEY = os.getenv("S3_KEY")
S3_SECRET = os.getenv("S3_SECRET")
MODEL_CHECKPOINT = os.getenv("MODEL_CHECKPOINT")

s3 = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
)

app = FastAPI()

def unauthorized():
    return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

@app.post("/infer")
async def infer(audio: UploadFile,
                job_id: str = Form(...),
                user_id: str = Form(...),
                s3_prefix: str = Form(...),
                x_api_key: str | None = Header(None)):
    if not x_api_key or x_api_key != WORKER_API_KEY:
        return unauthorized()

    with tempfile.TemporaryDirectory() as td:
        in_any = os.path.join(td, "in.any")
        in_wav = os.path.join(td, "in.wav")
        open(in_any, "wb").write(await audio.read())

        # Convert to 44.1kHz mono WAV
        subprocess.run(["ffmpeg", "-y", "-i", in_any, "-ar", "44100", "-ac", "1", in_wav],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # --- Separate vocals & instrumental with Demucs ---
        subprocess.run(["demucs", "-n", "htdemucs", "-o", td, in_wav],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        model_dir = os.path.join(td, "htdemucs")
        vocal, inst = None, None
        for root, _, files in os.walk(model_dir):
            for f in files:
                if f.endswith(".wav"):
                    p = os.path.join(root, f)
                    if "vocals" in f: vocal = p
                    if "accompaniment" in f or "other" in f or "no_vocals" in f: inst = p
        if not vocal:
            return JSONResponse({"ok": False, "error": "demucs failed"}, status_code=500)

        # --- Create chickenified vocal ---
        chicken_vocal = os.path.join(td, "chicken_vocal.wav")
        render_chicken(vocal, chicken_vocal, MODEL_CHECKPOINT)

        # --- Mix chicken + instrumental ---
        out_wav = os.path.join(td, "output.wav")
        if inst:
            subprocess.run([
                "ffmpeg", "-y",
                "-i", chicken_vocal, "-i", inst,
                "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.9[a1];[a0][a1]amix=inputs=2:normalize=0",
                out_wav
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            out_wav = chicken_vocal

        # --- Upload to S3 ---
        data, sr = sf.read(out_wav)
        dur = float(len(data)/sr)
        s3.upload_file(out_wav, S3_BUCKET, s3_prefix,
                       ExtraArgs={"ContentType": "audio/wav", "ACL": "public-read"})
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_prefix}"

        return {"ok": True, "output_s3_url": url, "duration_sec": dur}
=======
import os, io, uuid, datetime as dt
from fastapi import FastAPI, Request, Form, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, create_engine, select
from models import User, Job
from auth import hash_pw, check_pw, set_session, clear_session, get_current_user
from s3utils import put_input_bytes
import httpx

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
WORKER_URL = os.getenv("WORKER_URL", "")
WORKER_API_KEY = os.getenv("WORKER_API_KEY", "")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SQLModel.metadata.create_all(engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def db_sess():
    with Session(engine) as s:
        yield s

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(db_sess)):
    user = get_current_user(request, db)
    jobs = []
    if user:
        jobs = db.exec(select(Job).where(Job.user_id==user.id).order_by(Job.id.desc())).all()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "jobs": jobs})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(request: Request, db: Session = Depends(db_sess), email: str = Form(...), password: str = Form(...)):
    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not user.is_active or not check_pw(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    resp = RedirectResponse("/", status_code=302)
    set_session(resp, user.id)
    return resp

@app.post("/logout")
def logout():
    resp = RedirectResponse("/", status_code=302)
    clear_session(resp)
    return resp

def require_admin(request: Request, db: Session) -> User:
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@app.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request, db: Session = Depends(db_sess)):
    admin = require_admin(request, db)
    users = db.exec(select(User).order_by(User.id.desc())).all()
    return templates.TemplateResponse("admin_users.html", {"request": request, "user": admin, "users": users})

@app.post("/admin/users")
def admin_create_user(request: Request, db: Session = Depends(db_sess),
                      email: str = Form(...), password: str = Form(...), role: str = Form("user")):
    admin = require_admin(request, db)
    if db.exec(select(User).where(User.email == email)).first():
        return RedirectResponse("/admin/users?err=exists", status_code=302)
    u = User(email=email, password_hash=hash_pw(password), role=role, is_active=True)
    db.add(u); db.commit()
    return RedirectResponse("/admin/users?ok=1", status_code=302)

@app.post("/jobs")
async def create_job(request: Request, db: Session = Depends(db_sess), song: UploadFile = None):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if not song or (song.content_type not in ("audio/mpeg","audio/wav","audio/x-wav")):
        return RedirectResponse("/?err=badfile", status_code=302)
    job = Job(user_id=user.id, status="queued", input_filename=song.filename)
    db.add(job); db.commit(); db.refresh(job)
    headers = {"X-API-Key": WORKER_API_KEY}
    file_bytes = await song.read()
    data = {"job_id": str(job.id),"user_id": str(user.id),"s3_prefix": f"outputs/{user.id}/{job.id}.wav"}
    files = {"audio": (song.filename, file_bytes, song.content_type)}
    async with httpx.AsyncClient(timeout=300) as client:
        try:
            r = await client.post(f"{WORKER_URL}/infer", headers=headers, data=data, files=files)
            if r.status_code != 200:
                job.status="error"; job.error_message=f"Worker {r.status_code}"
            else:
                p=r.json()
                if p.get("ok"):
                    job.status="done"; job.output_s3_url=p["output_s3_url"]
                    job.input_duration_sec=float(p.get("duration_sec") or 0)
                    job.completed_at=dt.datetime.utcnow()
                else:
                    job.status="error"; job.error_message=p.get("error","unknown")
        except Exception as e:
            job.status="error"; job.error_message=str(e)
        finally:
            db.add(job); db.commit()
    return RedirectResponse("/", status_code=302)
>>>>>>> 320d5c312a70bb5f69ac9cb2673e5613a8843927
