from decimal import Decimal
from datetime import datetime 
from typing import Optional 

from pydantic import BaseModel, Field
from app.models import SaleStatus, PayoutStatus, LedgerEntryType

#Request
class SaleCreate(BaseModel):
    user_id: str
    brand_id: str
    earning: Decimal = Field(gt=0, description="Must be a positive amount")

class ReconcileRequest(BaseModel):
    status: SaleStatus #only approved or rejected will be sent 

class WithdrawalRequest(BaseModel):
    user_id: str
    amount: Decimal = Field(gt=0)

class PayoutFailureRequest(BaseModel):
    status: PayoutStatus # cancelled, rejected, failed
    reason: Optional[str]=None

#Response
class SaleOut(BaseModel):
    id: str
    user_id: str
    brand_id: str
    earning: Decimal 
    status: SaleStatus
    advance_paid_amount: Optional[Decimal]
    advance_paid_at: Optional[datetime]
    reconciled_at: Optional[datetime]

    class Config:
        from_attributes = True 

class LedgerEntryOut(BaseModel):
    id: str
    type: LedgerEntryType
    amount: Decimal
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes=True
    
class BalanceOut(BaseModel):
    user_id: str
    balance: Decimal 

class PayoutOut(BaseModel):
    id: str
    user_id: str
    amount: Decimal
    status: PayoutStatus
    requested_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes=True