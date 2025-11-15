"""
Database Schemas for Gym App

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name. For example: Member -> "member"
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Member(BaseModel):
    full_name: str = Field(..., description="Member full name")
    email: str = Field(..., description="Member email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    date_of_birth: Optional[str] = Field(None, description="YYYY-MM-DD")
    goals: Optional[str] = Field(None, description="Fitness goals")
    plan_id: Optional[str] = Field(None, description="Membership plan id")
    is_active: bool = Field(True, description="Active membership status")

class Trainer(BaseModel):
    full_name: str = Field(..., description="Trainer full name")
    specialties: List[str] = Field(default_factory=list, description="Areas of expertise")
    bio: Optional[str] = Field(None, description="Short bio")
    email: Optional[str] = Field(None, description="Email")

class Membershipplan(BaseModel):
    title: str = Field(..., description="Plan name")
    price: float = Field(..., ge=0, description="Monthly price")
    duration_months: int = Field(..., ge=1, description="Duration in months")
    access_level: str = Field("standard", description="standard | premium | vip")
    description: Optional[str] = Field(None, description="What is included")

class Gymclass(BaseModel):
    title: str = Field(..., description="Class name e.g., Yoga, HIIT")
    trainer_id: Optional[str] = Field(None, description="Assigned trainer id")
    start_time: str = Field(..., description="ISO datetime string")
    end_time: str = Field(..., description="ISO datetime string")
    capacity: int = Field(20, ge=1, description="Max attendees")
    location: Optional[str] = Field(None, description="Room or studio")

class Booking(BaseModel):
    member_id: str = Field(..., description="Member id")
    class_id: str = Field(..., description="Gymclass id")
    status: str = Field("booked", description="booked | canceled | attended")

class Workoutlog(BaseModel):
    member_id: str = Field(..., description="Member id")
    date: str = Field(..., description="YYYY-MM-DD")
    workout_name: str = Field(..., description="Workout title")
    duration_minutes: int = Field(..., ge=0)
    calories_burned: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

class Checkin(BaseModel):
    member_id: str = Field(..., description="Member id")
    timestamp: Optional[str] = Field(None, description="ISO datetime; defaults to now on server")

class Payment(BaseModel):
    member_id: str = Field(..., description="Member id")
    plan_id: Optional[str] = Field(None, description="Related plan id")
    amount: float = Field(..., ge=0)
    currency: str = Field("USD")
    status: str = Field("paid", description="paid | pending | failed")
    paid_at: Optional[str] = Field(None, description="ISO datetime; defaults to now on server")
