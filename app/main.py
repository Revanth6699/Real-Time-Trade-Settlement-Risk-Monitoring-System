from fastapi import (
    FastAPI,
    Request,
    Response,
    Depends,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from slowapi import Limiter
from slowapi.util import get_remote_address

from prometheus_client import (
    Counter,
    generate_latest
)

from pydantic import BaseModel

import redis
import os

from app.database import (
    SessionLocal,
    get_db,
    Base,
    engine
)

from app.models import trade
from app.models.trade import Trade
from app.models.user import User
from app.schemas import UserCreate, UserLogin

from app.routes.websocket import (
    router as websocket_router
)

from app.services.cache_service import (
    set_cache,
    get_cache
)


from app.auth import (
    oauth2_scheme,
    verify_token,
    hash_password,
    authenticate_user,
    create_access_token,
    validate_password,
    admin_required,
    trader_required,
    auditor_required,
    admin_or_trader,
    admin_or_auditor,
    authenticated_user

)
from fastapi.security import OAuth2PasswordBearer

from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from app.routes.websocket import router as websocket_router
from app.routes.alerts_ws import router as alerts_router
import json
import asyncio
from app.routes.metrics import router as metrics_router

import threading

from app.routes.health import router as health_router

from app.monitoring.prometheus_metrics import (
    TRADES_PRODUCED,
    TRADES_STORED,
    MARKET_STATE,
    HIGH_RISK,
    ANOMALIES,
    TOTAL,
)


from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connected to PostgreSQL")
    print("Connected to Upstash Redis")

    yield

    print("Application shutting down")



# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Real-Time Trade Settlement Risk Monitoring API",
    version="2.0.0",
    lifespan=lifespan
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)
app.include_router(websocket_router)
app.include_router(alerts_router)
app.include_router(health_router)
app.include_router(metrics_router)



# =====================================
# WEBSOCKET CONNECTION MANAGER
# =====================================

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):

        dead_connections = []

        for connection in self.active_connections:

            try:
                await connection.send_json(message)

            except Exception:
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()

# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# WEBSOCKET ROUTER
# =========================================================

app.include_router(websocket_router)

# =========================================================
# REDIS (UPSTASH)
# =========================================================

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL"),
    ssl=True,
    decode_responses=True
)

# =========================================================
# RATE LIMITER
# =========================================================

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

# =========================================================
# PROMETHEUS METRICS
# =========================================================

api_hits = Counter(
    "api_hits",
    "Total API hits"
)

# =========================================================
# REQUEST MODELS
# =========================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "trader"

# =========================================================
# ROOT
# =========================================================

@app.get("/")
def home():

    api_hits.inc()

    return {
        "message": "Real-Time Trade Settlement Risk Monitoring API Running"
    }


# =========================================================
# LOGIN
# =========================================================


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }
# =========================================================
# REGISTER
# =========================================================

class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "trader"


@app.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)):
    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    validate_password(user.password)

    hashed_password = hash_password(
        user.password
    )

    new_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    


    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "User registered successfully",
    }

# =========================================================
# GET TRADES
# =========================================================

@app.get("/trades")
def get_trades(db: Session = Depends(get_db),current_user=Depends(trader_required)):

    trades = db.query(Trade).all()

    result = []

    for trade in trades:

        result.append({
            "trade_id": trade.trade_id,
            "asset": trade.asset,
            "broker": trade.broker,
            "quantity": trade.quantity,
            "price": trade.price,
            "trade_amount": trade.trade_amount,
            "settlement_status": trade.settlement_status,
            "risk_score": trade.risk_score,
            "anomaly_flag": trade.anomaly_flag,
            "timestamp": trade.timestamp
        })

    return result

# =========================================================
# STATS ENDPOINT
# =========================================================

@app.get("/stats")
@limiter.limit("20/minute")
def get_stats(request: Request, current_user=Depends(authenticated_user)):

    api_hits.inc()

    db: Session = SessionLocal()

    try:

        total_trades = db.query(Trade).count()

        failed_trades = db.query(Trade).filter(
            Trade.settlement_status == "FAILED"
        ).count()

        anomalies = db.query(Trade).filter(
            Trade.anomaly_flag == True
        ).count()

        high_risk = db.query(Trade).filter(
            Trade.risk_score >= 80
        ).count()

        failure_rate = round(
            (failed_trades / total_trades) * 100,
            2
        ) if total_trades > 0 else 0

        set_cache(
            "stats",
            {
                "total_trades": total_trades,
                "failed_trades": failed_trades,
                "anomalies": anomalies,
                "high_risk": high_risk,
                "failure_rate": failure_rate
            }
        )


        return {
            "total_trades": total_trades,
            "failed_trades": failed_trades,
            "anomalies": anomalies,
            "high_risk": high_risk,
            "failure_rate": failure_rate
        }

    finally:
        db.close()

# =========================================================
# CACHED STATS
# =========================================================

@app.get("/cached-stats")
def cached_stats(current_user=Depends(authenticated_user)):

    api_hits.inc()

    cached_data = get_cache("stats")

    if cached_data:
        return cached_data

    return {
        "message": "No cached stats found"
    }

# =========================================================
# RECENT TRADES
# =========================================================

@app.get("/trades/recent")
def recent_trades(current_user=Depends(authenticated_user)):

    api_hits.inc()

    db: Session = SessionLocal()

    try:

        trades = (
            db.query(Trade)
            .order_by(Trade.timestamp.desc())
            .limit(20)
            .all()
        )

        return [
            {
                "trade_id": trade.trade_id,
                "broker": trade.broker,
                "asset": trade.asset,
                "trade_amount": trade.trade_amount,
                "risk_score": trade.risk_score,
                "settlement_status": trade.settlement_status,
                "anomaly_flag": trade.anomaly_flag,
                "timestamp": trade.timestamp
            }
            for trade in trades
        ]

    finally:
        db.close()

# =========================================================
# BROKER ACTIVITY
# =========================================================

@app.get("/broker-activity")
def broker_activity(current_user=Depends(authenticated_user)):

    api_hits.inc()

    db: Session = SessionLocal()

    try:

        data = (
            db.query(
                Trade.broker,
                func.count(Trade.id).label("trade_count")
            )
            .group_by(Trade.broker)
            .all()
        )

        return [
            {
                "broker": item[0],
                "trade_count": item[1]
            }
            for item in data
        ]

    finally:
        db.close()

# =========================================================
# HIGH RISK TRADES
# =========================================================

@app.get("/high-risk-trades")
def high_risk_trades(current_user=Depends(authenticated_user)):

    api_hits.inc()

    db: Session = SessionLocal()

    try:

        trades = (
            db.query(Trade)
            .filter(Trade.risk_score >= 80)
            .order_by(Trade.timestamp.desc())
            .limit(20)
            .all()
        )

        return [
            {
                "trade_id": trade.trade_id,
                "broker": trade.broker,
                "asset": trade.asset,
                "risk_score": trade.risk_score,
                "settlement_status": trade.settlement_status,
                "timestamp": trade.timestamp
            }
            for trade in trades
        ]

    finally:
        db.close()

# =========================================================
# FAILED TRADES
# =========================================================

@app.get("/failed-trades")
def failed_trades(current_user=Depends(authenticated_user)):

    api_hits.inc()

    db: Session = SessionLocal()

    try:

        trades = (
            db.query(Trade)
            .filter(Trade.settlement_status == "FAILED")
            .order_by(Trade.timestamp.desc())
            .limit(20)
            .all()
        )

        return [
            {
                "trade_id": trade.trade_id,
                "broker": trade.broker,
                "asset": trade.asset,
                "risk_score": trade.risk_score,
                "timestamp": trade.timestamp
            }
            for trade in trades
        ]

    finally:
        db.close()

# =========================================================
# ANOMALIES
# =========================================================

@app.get("/anomalies")
def anomaly_trades(current_user=Depends(authenticated_user)):

    api_hits.inc()

    db: Session = SessionLocal()

    try:

        trades = (
            db.query(Trade)
            .filter(Trade.anomaly_flag == True)
            .order_by(Trade.timestamp.desc())
            .limit(20)
            .all()
        )

        return [
            {
                "trade_id": trade.trade_id,
                "broker": trade.broker,
                "asset": trade.asset,
                "risk_score": trade.risk_score,
                "timestamp": trade.timestamp
            }
            for trade in trades
        ]

    finally:
        db.close()

# =========================================================
# PROMETHEUS METRICS
# =========================================================

@app.get("/metrics", include_in_schema=False)
def metrics():

    db = SessionLocal()

    try:
        total_trades = db.query(Trade).count()

        stored_trades = total_trades

        high_risk = (
            db.query(Trade)
            .filter(Trade.risk_score >= 80)
            .count()
        )

        anomalies = (
            db.query(Trade)
            .filter(Trade.anomaly_flag == True)
            .count()
        )

        failed = (
            db.query(Trade)
            .filter(Trade.settlement_status == "FAILED")
            .count()
        )

        produced = total_trades

        TRADES_PRODUCED.set(produced)
        TRADES_STORED.set(stored_trades)
        TOTAL.set(total_trades)
        HIGH_RISK.set(high_risk)
        ANOMALIES.set(anomalies)

        if failed == 0:
            MARKET_STATE.set(1)
        elif failed < 100:
            MARKET_STATE.set(2)
        else:
            MARKET_STATE.set(3)

        return Response(
            generate_latest(),
            media_type="text/plain"
        )

    finally:
        db.close()
# =========================================================
# ALL TRADES
# =========================================================

@app.get("/all-trades")
def get_all_trades(db: Session = Depends(get_db),current_user=Depends(admin_required)):


    trades = db.query(Trade).all()

    return trades


# =========================================================
# PROTECTED ROUTE
# =========================================================

@app.get("/protected")
def protected_route(
    token: str = Depends(oauth2_scheme),
    current_user=Depends(admin_required)
):

    payload = verify_token(token)

    return {
        "message": "Protected route accessed",
        "user": payload
    }
    
    
@app.get("/users")
def get_users(
    current_user=Depends(admin_required),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    payload = verify_token(token)

    if payload["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username
        }
        for user in users
    ]

@app.get("/admin")
def admin_route(
    token: str = Depends(oauth2_scheme)
):

    payload = verify_token(token)

    if payload["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    return {
        "message": "Welcome Admin"
    }
    

@app.get("/trader")
def trader_route(
    token: str = Depends(oauth2_scheme),
    current_user=Depends(trader_required)
):

    payload = verify_token(token)

    if payload["role"] not in ["trader", "admin"]:

        raise HTTPException(
            status_code=403,
            detail="Trader access required"
        )

    return {
        "message": "Trader dashboard"
    }
    
from app.websocket_manager import manager

@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)