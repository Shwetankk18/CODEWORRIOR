from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
DATABASE_URL = "sqlite:///./blood_donation.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    _tablename_ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    blood_type = Column(String, index=True)
    role = Column(String, index=True)  # 'donor' or 'hospital'
    contact_info = Column(String, index=True)
    available = Column(Boolean, default=True)

class BloodRequest(Base):
    _tablename_ = "blood_requests"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("users.id"))
    blood_type = Column(String, index=True)
    status = Column(String, default="pending")

Base.metadata.create_all(bind=engine)

# API setup
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class UserCreate(BaseModel):
    name: str
    blood_type: str
    role: str
    contact_info: str
    available: bool = True

class BloodRequestCreate(BaseModel):
    hospital_id: int
    blood_type: str

# Endpoints
@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, blood_type=user.blood_type, role=user.role, contact_info=user.contact_info, available=user.available)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/request-blood/")
def request_blood(request: BloodRequestCreate, db: Session = Depends(get_db)):
    db_request = BloodRequest(hospital_id=request.hospital_id, blood_type=request.blood_type)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/donors/{blood_type}")
def get_donors(blood_type: str, db: Session = Depends(get_db)):
    donors = db.query(User).filter(User.blood_type == blood_type, User.role == "donor", User.available == True).all()
    if not donors:
        raise HTTPException(status_code=404, detail="No available donors found")
    return donors

@app.get("/hospitals/")
def get_hospitals(db: Session = Depends(get_db)):
    hospitals = db.query(User).filter(User.role == "hospital").all()
    if not hospitals:
        raise HTTPException(status_code=404, detail="No hospitals found")
    return hospitals