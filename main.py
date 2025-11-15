import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Gym App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
@app.get("/")
def root():
    return {"status": "ok", "service": "gym-api"}

# Schema exposure for viewer
@app.get("/schema")
def get_schema():
    try:
        import schemas
        models = [
            name for name, obj in schemas.__dict__.items()
            if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
        ]
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Auth: simple email-based sign-up/login (no passwords for demo)
class AuthRequest(BaseModel):
    full_name: Optional[str] = None
    email: str

@app.post("/auth/login")
def login(req: AuthRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    member = db["member"].find_one({"email": req.email})
    if member:
        member["_id"] = str(member["_id"])  # serialize
        return {"member": member}
    # create if name provided
    if not req.full_name:
        raise HTTPException(status_code=404, detail="Member not found. Provide full_name to sign up.")
    from schemas import Member
    create_document("member", Member(full_name=req.full_name, email=req.email))
    created = db["member"].find_one({"email": req.email})
    created["_id"] = str(created["_id"])  # type: ignore
    return {"member": created}

# Plans
@app.get("/plans")
def list_plans():
    plans = get_documents("membershipplan")
    for p in plans:
        p["_id"] = str(p["_id"])  # serialize
    return {"plans": plans}

class PlanCreate(BaseModel):
    title: str
    price: float
    duration_months: int
    access_level: Optional[str] = "standard"
    description: Optional[str] = None

@app.post("/plans")
def create_plan(plan: PlanCreate):
    from schemas import Membershipplan
    plan_id = create_document("membershipplan", Membershipplan(**plan.model_dump()))
    return {"id": plan_id}

# Classes
@app.get("/classes")
def list_classes():
    classes = get_documents("gymclass")
    for c in classes:
        c["_id"] = str(c["_id"])  # serialize
    return {"classes": classes}

class ClassCreate(BaseModel):
    title: str
    trainer_id: Optional[str] = None
    start_time: str
    end_time: str
    capacity: int = 20
    location: Optional[str] = None

@app.post("/classes")
def create_class(data: ClassCreate):
    from schemas import Gymclass
    cid = create_document("gymclass", Gymclass(**data.model_dump()))
    return {"id": cid}

# Bookings
class BookingRequest(BaseModel):
    member_id: str
    class_id: str

@app.post("/bookings")
def book_class(req: BookingRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    from schemas import Booking
    # fetch class for capacity
    try:
        class_obj = db["gymclass"].find_one({"_id": ObjectId(req.class_id)})
    except Exception:
        class_obj = None
    capacity = class_obj.get("capacity", 9999) if class_obj else 9999

    current = db["booking"].count_documents({"class_id": req.class_id, "status": "booked"})
    if current >= capacity:
        raise HTTPException(status_code=400, detail="Class is full")

    bid = create_document("booking", Booking(**req.model_dump(), status="booked"))
    return {"id": bid}

@app.get("/bookings")
def list_bookings(member_id: Optional[str] = None, class_id: Optional[str] = None):
    query = {}
    if member_id:
        query["member_id"] = member_id
    if class_id:
        query["class_id"] = class_id
    items = get_documents("booking", query)
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return {"bookings": items}

# Workout Logs
class WorkoutLogCreate(BaseModel):
    member_id: str
    date: str
    workout_name: str
    duration_minutes: int
    calories_burned: Optional[int] = None
    notes: Optional[str] = None

@app.post("/workouts")
def create_workout(data: WorkoutLogCreate):
    from schemas import Workoutlog
    wid = create_document("workoutlog", Workoutlog(**data.model_dump()))
    return {"id": wid}

@app.get("/workouts")
def list_workouts(member_id: Optional[str] = None, date: Optional[str] = None):
    query = {}
    if member_id:
        query["member_id"] = member_id
    if date:
        query["date"] = date
    items = get_documents("workoutlog", query)
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return {"workouts": items}

# Check-ins
class CheckInRequest(BaseModel):
    member_id: str

@app.post("/checkins")
def check_in(req: CheckInRequest):
    from schemas import Checkin
    now_iso = datetime.now(timezone.utc).isoformat()
    cid = create_document("checkin", Checkin(member_id=req.member_id, timestamp=now_iso))
    return {"id": cid}

@app.get("/checkins")
def list_checkins(member_id: Optional[str] = None):
    query = {"member_id": member_id} if member_id else {}
    items = get_documents("checkin", query)
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return {"checkins": items}

# Payments
class PaymentCreate(BaseModel):
    member_id: str
    plan_id: Optional[str] = None
    amount: float
    currency: Optional[str] = "USD"
    status: Optional[str] = "paid"

@app.post("/payments")
def create_payment(data: PaymentCreate):
    from schemas import Payment
    now_iso = datetime.now(timezone.utc).isoformat()
    pid = create_document("payment", Payment(**data.model_dump(), paid_at=now_iso))
    return {"id": pid}

@app.get("/payments")
def list_payments(member_id: Optional[str] = None):
    query = {"member_id": member_id} if member_id else {}
    items = get_documents("payment", query)
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return {"payments": items}

# Trainers
@app.get("/trainers")
def list_trainers():
    items = get_documents("trainer")
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return {"trainers": items}

class TrainerCreate(BaseModel):
    full_name: str
    specialties: Optional[List[str]] = None
    bio: Optional[str] = None
    email: Optional[str] = None

@app.post("/trainers")
def create_trainer(data: TrainerCreate):
    from schemas import Trainer
    tid = create_document("trainer", Trainer(**{**data.model_dump(), "specialties": data.specialties or []}))
    return {"id": tid}

# Members
@app.get("/members")
def list_members():
    items = get_documents("member")
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return {"members": items}

class MemberCreate(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    goals: Optional[str] = None
    plan_id: Optional[str] = None

@app.post("/members")
def create_member(data: MemberCreate):
    from schemas import Member
    mid = create_document("member", Member(**data.model_dump()))
    return {"id": mid}

# Utility: test database connectivity
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
