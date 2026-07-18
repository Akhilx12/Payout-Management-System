from sqlalchemy.orm import Session 

from app.models import Payout, PayoutStatus, LedgerEntryType, _now 
from app.services.wallet_service import WalletService 

class PayoutNotFoundError(Exception):
    pass

class InvalidPayoutStateError(Exception):
    pass

class PayoutRecoveryService:
    RECOVERABLE_STATUSES = (PayoutStatus.cancelled, PayoutStatus.rejected, PayoutStatus.failed)

    def __init__(self,db: Session):
        self.db=db
        self.wallet=WalletService(db)

    def mark_payout_failed(self, payout_id: str, new_status: PayoutStatus, reason:str = "") -> None:
        if new_status not in self.RECOVERABLE_STATUSES:
            raise ValueError(f"{new_status} is not a recoverable status")
        
        payout=self.db.query(Payout).filter(Payout.id==payout_id).first()
        if payout is None:
            raise PayoutNotFoundError(f"No payout with id {payout_id}")
        
        if payout.status != PayoutStatus.initiated:
            raise InvalidPayoutStateError(
                f"Payout {payout_id} is already {payout.status.value}, cannot mark as {new_status.value}"
            )
        
        payout.status=new_status
        payout.completed_at=_now()
        self.db.commit()

        self.wallet.add_entry(
            user_id=payout.user_id,
            type_=LedgerEntryType.REVERSAL_CREDIT,
            amount=payout.amount,
            payout_id=payout.id,
            description=f"Reversal for {new_status.value} payout {payout.id}: {reason}".strip(),
        )