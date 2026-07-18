from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import WithdrawalRequest, PayoutOut
from app.services.withdrawal_service import (
    WithdrawalService, InsufficientBalanceError, WithdrawalTooSoonError
)

router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])


@router.post("", response_model=PayoutOut, status_code=201)
def request_withdrawal(payload: WithdrawalRequest, db: Session = Depends(get_db)):
    service = WithdrawalService(db)
    try:
        return service.request_withdrawal(payload.user_id, payload.amount)
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WithdrawalTooSoonError as e:
        raise HTTPException(status_code=429, detail=str(e))