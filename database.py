from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # Store hashed passwords only
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    searches = relationship("Search", back_populates="user")

class Search(Base):
    __tablename__ = 'searches'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    query = Column(Text, nullable=False)
    response = Column(Text)
    model_used = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="searches")

def init_db():
    db_path = os.path.join('data', 'backup', 'database', 'llm_wrapper.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def get_db():
    db = init_db()
    try:
        yield db
    finally:
        db.close()