from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session 

from app.models import Sale, SaleStatus, LedgerEntryType, _now
from app.services.wallet_service import WalletService 

class AdvancePayoutService:
    ADVANCE_PERCENTAGE = Decimal("0.10")

    def __init__(self,db: Session):
        self.db=db
        self.wallet=WalletService(db)
    
    def run_batch(self):
        eligible_sales=(
            self.db.query(Sale)
            .filter(Sale.status==SaleStatus.pending)
            .filter(Sale.advance_paid_at.is_(None))
            .all()
        )

        paid=[]
        for sale in eligible_sales:
            advance_amount=(sale.earning * self.ADVANCE_PERCENTAGE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            self.wallet.add_entry(
                user_id=sale.user_id,
                type_=LedgerEntryType.ADVANCE_CREDIT,
                amount=advance_amount,
                sale_id=sale.id,
                description=f"10% advance on sale {sale.id}",
            )

            sale.advance_paid_amount=advance_amount
            sale.advance_paid_at=_now()
            self.db.commit()

            paid.append((sale.id,advance_amount))
        return paid