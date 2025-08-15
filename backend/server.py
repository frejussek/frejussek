from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import uuid
from typing import Optional, List

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'eduflow_db')
SECRET_KEY = "eduflow_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(title="EduFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"  # student, instructor, admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class CourseCreate(BaseModel):
    title: str
    description: str
    category: str
    level: str = "beginner"  # beginner, intermediate, advanced
    duration_hours: int = 1

class LessonCreate(BaseModel):
    course_id: str
    title: str
    content: str
    video_url: Optional[str] = None
    order: int = 1

class ProgressUpdate(BaseModel):
    lesson_id: str
    completed: bool = True

# Auth helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.users.find_one({"user_id": user_id})
    if user is None:
        raise credentials_exception
    return user

# Auth endpoints
@app.post("/api/auth/register")
async def register(user: UserCreate):
    # Check if user exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    user_doc = {
        "user_id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "level": 1,
        "xp": 0,
        "badges": []
    }
    
    db.users.insert_one(user_doc)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "level": 1,
            "xp": 0
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["user_id"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": db_user["user_id"],
            "email": db_user["email"],
            "full_name": db_user["full_name"],
            "role": db_user["role"],
            "level": db_user.get("level", 1),
            "xp": db_user.get("xp", 0)
        }
    }

# User endpoints
@app.get("/api/user/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "level": current_user.get("level", 1),
        "xp": current_user.get("xp", 0),
        "badges": current_user.get("badges", []),
        "created_at": current_user["created_at"]
    }

# Course endpoints
@app.post("/api/courses")
async def create_course(course: CourseCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create courses")
    
    course_id = str(uuid.uuid4())
    course_doc = {
        "course_id": course_id,
        "title": course.title,
        "description": course.description,
        "category": course.category,
        "level": course.level,
        "duration_hours": course.duration_hours,
        "instructor_id": current_user["user_id"],
        "instructor_name": current_user["full_name"],
        "created_at": datetime.utcnow(),
        "is_published": True,
        "students_count": 0
    }
    
    db.courses.insert_one(course_doc)
    return {"message": "Course created successfully", "course_id": course_id}

@app.get("/api/courses")
async def get_courses():
    courses = list(db.courses.find({"is_published": True}, {"_id": 0}).sort("created_at", -1))
    
    # Add lessons count for each course
    for course in courses:
        lessons_count = db.lessons.count_documents({"course_id": course["course_id"]})
        course["lessons_count"] = lessons_count
    
    return {"courses": courses}

@app.get("/api/courses/{course_id}")
async def get_course(course_id: str):
    course = db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get lessons for this course
    lessons = list(db.lessons.find({"course_id": course_id}, {"_id": 0}).sort("order", 1))
    course["lessons"] = lessons
    
    return course

@app.post("/api/courses/{course_id}/lessons")
async def create_lesson(course_id: str, lesson: LessonCreate, current_user: dict = Depends(get_current_user)):
    # Check if course exists and user is instructor
    course = db.courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] not in ["instructor", "admin"] or course["instructor_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    lesson_id = str(uuid.uuid4())
    lesson_doc = {
        "lesson_id": lesson_id,
        "course_id": course_id,
        "title": lesson.title,
        "content": lesson.content,
        "video_url": lesson.video_url,
        "order": lesson.order,
        "created_at": datetime.utcnow()
    }
    
    db.lessons.insert_one(lesson_doc)
    return {"message": "Lesson created successfully", "lesson_id": lesson_id}

# Progress endpoints
@app.post("/api/progress")
async def update_progress(progress: ProgressUpdate, current_user: dict = Depends(get_current_user)):
    # Check if lesson exists
    lesson = db.lessons.find_one({"lesson_id": progress.lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Update or create progress
    progress_doc = {
        "user_id": current_user["user_id"],
        "lesson_id": progress.lesson_id,
        "course_id": lesson["course_id"],
        "completed": progress.completed,
        "completed_at": datetime.utcnow() if progress.completed else None
    }
    
    db.progress.update_one(
        {"user_id": current_user["user_id"], "lesson_id": progress.lesson_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    # Award XP for completion
    if progress.completed:
        xp_gained = 10
        db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$inc": {"xp": xp_gained}}
        )
        
        # Check for level up (every 100 XP = 1 level)
        updated_user = db.users.find_one({"user_id": current_user["user_id"]})
        new_level = (updated_user["xp"] // 100) + 1
        if new_level > updated_user.get("level", 1):
            db.users.update_one(
                {"user_id": current_user["user_id"]},
                {"$set": {"level": new_level}}
            )
    
    return {"message": "Progress updated successfully"}

@app.get("/api/progress/{course_id}")
async def get_progress(course_id: str, current_user: dict = Depends(get_current_user)):
    # Get all lessons for the course
    lessons = list(db.lessons.find({"course_id": course_id}, {"lesson_id": 1, "title": 1, "order": 1}).sort("order", 1))
    
    # Get user's progress for each lesson
    progress_data = []
    for lesson in lessons:
        progress = db.progress.find_one({
            "user_id": current_user["user_id"],
            "lesson_id": lesson["lesson_id"]
        })
        
        progress_data.append({
            "lesson_id": lesson["lesson_id"],
            "title": lesson["title"],
            "order": lesson["order"],
            "completed": progress["completed"] if progress else False,
            "completed_at": progress["completed_at"] if progress else None
        })
    
    # Calculate completion percentage
    completed_count = sum(1 for p in progress_data if p["completed"])
    total_lessons = len(progress_data)
    completion_percentage = (completed_count / total_lessons * 100) if total_lessons > 0 else 0
    
    return {
        "course_id": course_id,
        "lessons": progress_data,
        "completion_percentage": round(completion_percentage, 1),
        "completed_lessons": completed_count,
        "total_lessons": total_lessons
    }

@app.get("/api/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    # Get enrolled courses (courses with progress)
    enrolled_courses = []
    course_ids = db.progress.distinct("course_id", {"user_id": current_user["user_id"]})
    
    for course_id in course_ids:
        course = db.courses.find_one({"course_id": course_id}, {"_id": 0})
        if course:
            # Calculate progress
            total_lessons = db.lessons.count_documents({"course_id": course_id})
            completed_lessons = db.progress.count_documents({
                "user_id": current_user["user_id"],
                "course_id": course_id,
                "completed": True
            })
            completion_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            
            course["completion_percentage"] = round(completion_percentage, 1)
            course["completed_lessons"] = completed_lessons
            course["total_lessons"] = total_lessons
            enrolled_courses.append(course)
    
    # Get recent activity
    recent_progress = list(db.progress.find(
        {"user_id": current_user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("completed_at", -1).limit(5))
    
    return {
        "user": {
            "full_name": current_user["full_name"],
            "level": current_user.get("level", 1),
            "xp": current_user.get("xp", 0),
            "badges": current_user.get("badges", [])
        },
        "enrolled_courses": enrolled_courses,
        "recent_activity": recent_progress,
        "stats": {
            "total_courses": len(enrolled_courses),
            "completed_courses": sum(1 for c in enrolled_courses if c["completion_percentage"] == 100),
            "total_xp": current_user.get("xp", 0),
            "current_level": current_user.get("level", 1)
        }
    }

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "EduFlow API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)