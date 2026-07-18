#this file will calculate the balance

from decimal import Decimal 
from typing import Optional 

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import LedgerEntry, LedgerEntryType

class WalletService:
    def __init__(self, db: Session):
        self.db=db
    
    def get_balance(self, user_id: str) -> Decimal:
        total=(
            self.db.query(func.coalesce(func.sum(LedgerEntry.amount),0)).filter(LedgerEntry.user_id==user_id).scalar()
        )
        return Decimal(total)
    
    def add_entry(
            self,
            user_id: str,
            type_: LedgerEntryType,
            amount: Decimal,
            sale_id: Optional[str] = None,
            payout_id: Optional[str] = None,
            description: Optional[str] = None,
    ) -> LedgerEntry:
        entry=LedgerEntry(
            user_id=user_id,
            sale_id=sale_id,
            payout_id=payout_id,
            type=type_,
            amount=amount,
            description=description,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_ledger(self, user_id: str):
        return(
            self.db.query(LedgerEntry)
            .filter(LedgerEntry.user_id == user_id)
            .order_by(LedgerEntry.created_at.asc())
            .all()
        )