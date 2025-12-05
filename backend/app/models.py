from sqlalchemy import Column, Integer, String, Date, Text, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .db import Base
import datetime
import uuid

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    discharge_date = Column(Date, nullable=False)
    primary_diagnosis = Column(Text, nullable=False)
    medications = Column(JSON, nullable=False)
    dietary_restrictions = Column(Text)
    follow_up = Column(Text)
    warning_signs = Column(Text)
    discharge_instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    agent = Column(String) # 'receptionist' | 'clinical' | 'system'
    message = Column(Text, nullable=False)

class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    agent = Column(String, nullable=False)
    event_type = Column(String, nullable=False) # 'db_lookup', 'handoff', 'rag_query', 'web_search', 'error'
    details = Column(JSON)
