from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BalanceOut, LedgerEntryOut
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/users", tags=["wallet"])


@router.get("/{user_id}/balance", response_model=BalanceOut)
def get_balance(user_id: str, db: Session = Depends(get_db)):
    wallet = WalletService(db)
    balance = wallet.get_balance(user_id)
    return BalanceOut(user_id=user_id, balance=balance)


@router.get("/{user_id}/ledger", response_model=list[LedgerEntryOut])
def get_ledger(user_id: str, db: Session = Depends(get_db)):
    wallet = WalletService(db)
    return wallet.get_ledger(user_id)