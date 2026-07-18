from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReconcileRequest, SaleOut, PayoutFailureRequest
from app.services.advance_payout_service import AdvancePayoutService
from app.services.reconciliation_service import (
    ReconciliationService, SaleNotFoundError, SaleAlreadyReconciledError
)
from app.services.payout_recovery_service import (
    PayoutRecoveryService, PayoutNotFoundError, InvalidPayoutStateError
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/advance-payout/run")
def run_advance_payout(db: Session = Depends(get_db)):
    service = AdvancePayoutService(db)
    results = service.run_batch()
    return {
        "sales_paid": len(results),
        "total_paid": str(sum(amount for _, amount in results)) if results else "0.00",
    }


@router.post("/sales/{sale_id}/reconcile", response_model=SaleOut)
def reconcile_sale(sale_id: str, payload: ReconcileRequest, db: Session = Depends(get_db)):
    service = ReconciliationService(db)
    try:
        service.reconcile(sale_id, payload.status)
    except SaleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SaleAlreadyReconciledError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from app.models import Sale
    return db.query(Sale).filter(Sale.id == sale_id).first()


@router.post("/payouts/{payout_id}/status")
def update_payout_status(payout_id: str, payload: PayoutFailureRequest, db: Session = Depends(get_db)):
    service = PayoutRecoveryService(db)
    try:
        service.mark_payout_failed(payout_id, payload.status, payload.reason or "")
    except PayoutNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidPayoutStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}