#this file describes the structure of our tables
import uuid
from datetime import datetime, timezone 

from sqlalchemy import Column, String, DateTime
from sqlalchemy import ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy import Text
from app.database import Base

import enum

def _uuid() -> str:
    return str(uuid.uuid4())

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _ensure_aware(dt: datetime) -> datetime: 
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class SaleStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class LedgerEntryType(str, enum.Enum):
    ADVANCE_CREDIT = "ADVANCE_CREDIT" #10% advance on pending sale
    ADJUSTMENT = "ADJUSTMENT" #result of reconci (+ or -)
    WITHDRAWAL_DEBIT = "WITHDRAWAL_DEBIT"  #user withdrew the money
    REVERSAL_CREDIT = "REVERSAL_CREDIT"  #failed payout credited back

class PayoutStatus(str, enum.Enum):
    initiated = "initiated"
    completed = "completed"
    cancelled = "cancelled"
    rejected = "rejected"
    failed = "failed"

class User(Base):
    __tablename__ = "users"

    id=Column(String, primary_key=True, default = _uuid)
    name=Column(String, nullable=False)
    email=Column(String, nullable=False, unique=True)
    created_at=Column(DateTime(timezone=True), default=_now)

class Brand(Base):
    __tablename__ = "brands"

    id=Column(String, primary_key=True, default=_uuid)
    name=Column(String, nullable=False, unique=True)

class Sale(Base):
    __tablename__ = "sales"

    id=Column(String, primary_key=True, default=_uuid)
    user_id=Column(String, ForeignKey("users.id"), nullable=False, index=True)
    brand_id=Column(String, ForeignKey("brands.id"), nullable=False)

    earning=Column(Numeric(12, 2), nullable=False)
    status=Column(SAEnum(SaleStatus), nullable=False, default=SaleStatus.pending)

    advance_paid_amount=Column(Numeric(12,2), nullable=True)
    advance_paid_at=Column(DateTime(timezone=True), nullable=True)

    reconciled_at=Column(DateTime(timezone=True), nullable=True)
    created_at=Column(DateTime(timezone=True), default=_now)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    sale_id = Column(String, ForeignKey("sales.id"), nullable=True)
    payout_id = Column(String, ForeignKey("payouts.id"), nullable=True)

    type = Column(SAEnum(LedgerEntryType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now, index=True)

class Payout(Base):
    __tablename__ = "payouts"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(SAEnum(PayoutStatus), nullable=False, default=PayoutStatus.initiated)

    requested_at = Column(DateTime(timezone=True), default=_now, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)