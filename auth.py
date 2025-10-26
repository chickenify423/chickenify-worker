import bcrypt, itsdangerous, os
from fastapi import Request
from sqlmodel import Session, select
from models import User

SECRET = os.environ.get("SESSION_SECRET", "change-me-please")
signer = itsdangerous.TimestampSigner(SECRET)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_pw(pw: str, pw_hash: str) -> bool:
    return bcrypt.checkpw(pw.encode(), pw_hash.encode())

def set_session(response, user_id: int):
    token = signer.sign(str(user_id)).decode()
    response.set_cookie("session", token, httponly=True, samesite="lax", secure=False)

def get_current_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get("session")
    if not token: return None
    try:
        raw = signer.unsign(token, max_age=60*60*24*30).decode()
        uid = int(raw)
    except Exception:
        return None
    user = db.exec(select(User).where(User.id == uid)).first()
    return user if (user and user.is_active) else None

def clear_session(response):
    response.delete_cookie("session")
