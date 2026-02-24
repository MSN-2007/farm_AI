from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from database import Base
from datetime import datetime

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    question_text = Column(Text)
    domain = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer)
    poll_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed = Column(Boolean, default=False)