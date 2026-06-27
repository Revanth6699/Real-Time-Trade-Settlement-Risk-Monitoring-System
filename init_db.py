from app.database import engine
from app.models.trade import Trade
from app.database import Base

Base.metadata.create_all(bind=engine)

print("Tables Created")