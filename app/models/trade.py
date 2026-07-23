from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from sqlalchemy import Column, DateTime
from datetime import datetime

from app.database import Base

class Trade(Base):

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    trade_id = Column(String, unique=True)

    asset = Column(String)

    broker = Column(String)

    quantity = Column(Integer)

    price = Column(Float)

    trade_amount = Column(Float)

    settlement_status = Column(String)

    retry_count = Column(Integer, default=0)

    risk_score = Column(Float)

    anomaly_flag = Column(Boolean)
    
    
    created_at = Column(DateTime, default=datetime.utcnow)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )