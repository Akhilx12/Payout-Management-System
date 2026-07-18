from fastapi import FastAPI
from app.database import Base, engine
from app import models 
from app.routers import sales, wallet, withdrawals, admin

Base.metadata.create_all(bind=engine)
app=FastAPI(title="User payout management system")
app.include_router(sales.router)
app.include_router(wallet.router)
app.include_router(withdrawals.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return{"status": "ok", "service": "payout-management-system"}