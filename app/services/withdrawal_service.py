from datetime import timedelta 
from decimal import Decimal 

from sqlalchemy.orm import Session 

from app.models import Payout, PayoutStatus, LedgerEntryType, _now, _ensure_aware
from app.services.wallet_service import WalletService 

class InsufficientBalanceError(Exception):
    pass

class WithdrawalTooSoonError(Exception):
    pass

class WithdrawalService:
    COOLDOWN=timedelta(hours=24)
    #the cooldown is only for withdrawal with status completed or active
    #not for failed cancelled or rejected withdrawal
    COOLDOWN_TRIGGERING_STATUSES=(PayoutStatus.initiated, PayoutStatus.completed)

    def __init__(self,db:Session):
        self.db=db
        self.wallet=WalletService(db)

    def request_withdrawal(self, user_id: str, amount:Decimal) -> Payout:
        last_relevant_payout=(
            self.db.query(Payout).filter(Payout.user_id==user_id)
            .filter(Payout.status.in_(self.COOLDOWN_TRIGGERING_STATUSES))
            .order_by(Payout.requested_at.desc())
            .first()
        )
        
        if last_relevant_payout is not None:
            last_time = _ensure_aware(last_relevant_payout.requested_at)
            elapsed = _now() - last_time
            if elapsed < self.COOLDOWN:
                remaining = self.COOLDOWN - elapsed
                raise WithdrawalTooSoonError(
                    f"Please wait {remaining} for next withdrawal"
                )
        
        balance=self.wallet.get_balance(user_id)
        if amount>balance:
            raise InsufficientBalanceError(
                f"Insufficient balance, unable to withdraw {amount}"
            )
        
        payout=Payout(user_id=user_id,amount=amount,status=PayoutStatus.initiated)
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)

        self.wallet.add_entry(
            user_id=user_id,
            type_=LedgerEntryType.WITHDRAWAL_DEBIT,
            amount=-amount,
            payout_id=payout.id,
            description=f"Withdrawal request {payout.id}",
        )
        return payout