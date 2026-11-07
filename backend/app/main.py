import base64, hashlib, hmac, json, os, secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session, engine
from .models import User, Provider, Slot, Appointment
from .validation import normalize_registration

app = FastAPI(title="SmartCare API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SECRET = os.getenv("APP_SECRET", "smartcare-course-demo-secret")

class RegisterBody(dict): pass

from pydantic import BaseModel
class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
class LoginRequest(BaseModel):
    email: str
    password: str
class AppointmentRequest(BaseModel):
    slot_id: int
    reason: str = "General appointment"
class RescheduleRequest(BaseModel):
    new_slot_id: int
class ProviderRequest(BaseModel):
    name: str
    specialty: str
    bio: str = ""
class SlotRequest(BaseModel):
    provider_id: int
    start_time: datetime
class StatusRequest(BaseModel):
    status: str
class AIRequest(BaseModel):
    message: str

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return base64.urlsafe_b64encode(salt + digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    raw = base64.urlsafe_b64decode(encoded.encode())
    salt, expected = raw[:16], raw[16:]
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return hmac.compare_digest(actual, expected)

def make_token(user: User) -> str:
    payload = {"id": user.id, "role": user.role, "email": user.email, "exp": int((datetime.utcnow()+timedelta(hours=12)).timestamp())}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"

def parse_token(token: str) -> dict:
    try:
        body, sig = token.split(".", 1)
        expected = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): raise ValueError()
        padded = body + "=" * (-len(body) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode())
        if data["exp"] < int(datetime.utcnow().timestamp()): raise ValueError()
        return data
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

def current_user(authorization: Optional[str] = Header(None), session: Session = Depends(get_session)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Login required")
    data = parse_token(authorization[7:])
    user = session.get(User, data["id"])
    if not user: raise HTTPException(401, "User not found")
    return user

def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin": raise HTTPException(403, "Admin access required")
    return user

def seed_data(session: Session):
    if not session.exec(select(User).where(User.email == "admin@smartcare.demo")).first():
        session.add(User(full_name="SmartCare Administrator", email="admin@smartcare.demo", password_hash=hash_password("SmartCareAdmin123"), role="admin"))
    if not session.exec(select(Provider)).first():
        providers = [
            Provider(name="Dr. Maya Johnson", specialty="Family Medicine", bio="Routine checkups and general primary care."),
            Provider(name="Dr. Daniel Kim", specialty="Internal Medicine", bio="Adult preventive care and follow-up visits."),
            Provider(name="Dr. Sofia Patel", specialty="Pediatrics", bio="Primary care appointments for children and adolescents."),
        ]
        for p in providers: session.add(p)
        session.commit()
        for p in session.exec(select(Provider)).all():
            for d in range(1, 8):
                for hour in (9, 11, 14, 16):
                    session.add(Slot(provider_id=p.id, start_time=(datetime.now()+timedelta(days=d)).replace(hour=hour, minute=0, second=0, microsecond=0)))
    session.commit()

@app.on_event("startup")
def startup():
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)

@app.get("/api/health")
def health(): return {"status":"ok"}

@app.post("/api/auth/register")
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    try:
        full_name, email = normalize_registration(body.full_name, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if session.exec(select(User).where(User.email == email)).first(): raise HTTPException(400, "Email already registered")
    user = User(full_name=full_name, email=email, password_hash=hash_password(body.password))
    session.add(user); session.commit(); session.refresh(user)
    return {"token": make_token(user), "user": {"id":user.id,"full_name":user.full_name,"email":user.email,"role":user.role}}

@app.post("/api/auth/login")
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email.lower())).first()
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return {"token": make_token(user), "user": {"id":user.id,"full_name":user.full_name,"email":user.email,"role":user.role}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id":user.id,"full_name":user.full_name,"email":user.email,"role":user.role}

@app.get("/api/providers")
def providers(session: Session = Depends(get_session)):
    return session.exec(select(Provider)).all()

@app.get("/api/slots")
def slots(provider_id: Optional[int]=None, session: Session = Depends(get_session)):
    q = select(Slot).where(Slot.is_booked == False, Slot.start_time > datetime.now())
    if provider_id: q = q.where(Slot.provider_id == provider_id)
    return session.exec(q.order_by(Slot.start_time)).all()

@app.get("/api/appointments")
def my_appointments(user: User = Depends(current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(Appointment).where(Appointment.user_id == user.id).order_by(Appointment.created_at.desc())).all()
    out=[]
    for a in rows:
        s=session.get(Slot,a.slot_id); p=session.get(Provider,s.provider_id) if s else None
        out.append({"id":a.id,"reason":a.reason,"status":a.status,"start_time":s.start_time if s else None,"provider_name":p.name if p else "Unknown","specialty":p.specialty if p else ""})
    return out

@app.post("/api/appointments")
def book(body: AppointmentRequest, user: User = Depends(current_user), session: Session = Depends(get_session)):
    slot=session.get(Slot,body.slot_id)
    if not slot or slot.is_booked or slot.start_time <= datetime.now():
        raise HTTPException(400, "That time is no longer available")
    slot.is_booked=True
    appt=Appointment(user_id=user.id,slot_id=slot.id,reason=body.reason,status="confirmed")
    session.add(slot);session.add(appt);session.commit();session.refresh(appt)
    return appt

@app.patch("/api/appointments/{appointment_id}/cancel")
def cancel(appointment_id:int,user:User=Depends(current_user),session:Session=Depends(get_session)):
    a=session.get(Appointment,appointment_id)
    if not a or (a.user_id!=user.id and user.role!="admin"): raise HTTPException(404,"Appointment not found")
    if a.status=="cancelled": return a
    a.status="cancelled"; s=session.get(Slot,a.slot_id)
    if s: s.is_booked=False; session.add(s)
    session.add(a);session.commit();session.refresh(a);return a

@app.patch("/api/appointments/{appointment_id}/reschedule")
def reschedule(appointment_id:int,body:RescheduleRequest,user:User=Depends(current_user),session:Session=Depends(get_session)):
    a=session.get(Appointment,appointment_id)
    if not a or a.user_id!=user.id: raise HTTPException(404,"Appointment not found")
    new=session.get(Slot,body.new_slot_id)
    if not new or new.is_booked: raise HTTPException(400,"New time is unavailable")
    old=session.get(Slot,a.slot_id)
    if old: old.is_booked=False; session.add(old)
    new.is_booked=True;a.slot_id=new.id;a.status="confirmed"
    session.add(new);session.add(a);session.commit();return {"ok":True}

@app.get("/api/admin/stats")
def stats(_:User=Depends(admin_user),session:Session=Depends(get_session)):
    return {"patients":len(session.exec(select(User).where(User.role=="patient")).all()),"providers":len(session.exec(select(Provider)).all()),"appointments":len(session.exec(select(Appointment)).all())}

@app.get("/api/admin/appointments")
def admin_appointments(_:User=Depends(admin_user),session:Session=Depends(get_session)):
    out=[]
    for a in session.exec(select(Appointment).order_by(Appointment.created_at.desc())).all():
        u=session.get(User,a.user_id);s=session.get(Slot,a.slot_id);p=session.get(Provider,s.provider_id) if s else None
        out.append({"id":a.id,"patient":u.full_name if u else "Unknown","provider":p.name if p else "Unknown","start_time":s.start_time if s else None,"status":a.status,"reason":a.reason})
    return out

@app.post("/api/admin/providers")
def create_provider(body:ProviderRequest,_:User=Depends(admin_user),session:Session=Depends(get_session)):
    p=Provider(**body.model_dump());session.add(p);session.commit();session.refresh(p);return p

@app.post("/api/admin/slots")
def create_slot(body:SlotRequest,_:User=Depends(admin_user),session:Session=Depends(get_session)):
    if not session.get(Provider,body.provider_id): raise HTTPException(404,"Provider not found")
    s=Slot(**body.model_dump());session.add(s);session.commit();session.refresh(s);return s

@app.patch("/api/admin/appointments/{appointment_id}/status")
def set_status(appointment_id:int,body:StatusRequest,_:User=Depends(admin_user),session:Session=Depends(get_session)):
    if body.status not in {"confirmed","completed","cancelled","no-show"}: raise HTTPException(400,"Invalid status")
    a=session.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,"Appointment not found")
    a.status=body.status;session.add(a);session.commit();return {"ok":True}

def local_ai_match(message:str, session:Session):
    text=message.lower(); preferred_hour=None
    if "morning" in text: preferred_hour=(8,12)
    elif "afternoon" in text: preferred_hour=(12,17)
    elif "evening" in text or "after 5" in text: preferred_hour=(17,20)
    elif "after 3" in text or "after 3 pm" in text: preferred_hour=(15,20)
    slots=session.exec(select(Slot).where(Slot.is_booked==False,Slot.start_time>datetime.now()).order_by(Slot.start_time)).all()
    ranked=[]
    for s in slots:
        p=session.get(Provider,s.provider_id)
        score=0
        if preferred_hour and preferred_hour[0] <= s.start_time.hour < preferred_hour[1]: score+=3
        if p and p.specialty.lower() in text: score+=3
        ranked.append((score,s,p))
    ranked.sort(key=lambda x:(-x[0],x[1].start_time))
    return [{"slot_id":s.id,"provider":p.name,"specialty":p.specialty,"start_time":s.start_time.isoformat()} for _,s,p in ranked[:5]]

@app.post("/api/ai/schedule-assistant")
def ai_schedule(body:AIRequest, user:User=Depends(current_user), session:Session=Depends(get_session)):
    suggestions=local_ai_match(body.message,session)
    api_key=os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"mode":"demo-assistant","message":"I matched your request to the closest available times. Add OPENAI_API_KEY in deployment to enable the language-model interpretation layer.","suggestions":suggestions}
    try:
        available="\n".join([f"slot {x['slot_id']}: {x['provider']} ({x['specialty']}) at {x['start_time']}" for x in suggestions])
        prompt=f"You are SmartCare's scheduling assistant. Do not diagnose or give medical advice. Briefly explain which of these available slots best fit the patient's scheduling request. Patient request: {body.message}\nAvailable options:\n{available}"
        r=httpx.post("https://api.openai.com/v1/responses",headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},json={"model":os.getenv("OPENAI_MODEL","gpt-5.6-luna"),"input":prompt},timeout=30)
        r.raise_for_status(); data=r.json(); text=data.get("output_text")
        if not text:
            text="I found several appointment times that may fit your request."
        return {"mode":"ai","message":text,"suggestions":suggestions}
    except Exception:
        return {"mode":"fallback","message":"I found the closest available times based on your request.","suggestions":suggestions}

# Serve React build in production
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        requested = DIST / full_path
        if requested.is_file(): return FileResponse(requested)
        return FileResponse(DIST / "index.html")
