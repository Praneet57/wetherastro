from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)
    country = Column(String(10))
    temperature = Column(Float)
    description = Column(String(150))
    searched_at = Column(DateTime, default=datetime.utcnow)
