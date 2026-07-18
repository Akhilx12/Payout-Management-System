from decimal import Decimal
from sqlalchemy.orm import Session 

from app.models import Sale, SaleStatus, LedgerEntryType, _now
from app.services.wallet_service import WalletService

class SaleNotFoundError(Exception):
    pass

class SaleAlreadyReconciledError(Exception):
    pass

class ReconciliationService:
    def __init__(self,db:Session):
        self.db=db
        self.wallet=WalletService(db)
    
    def reconcile(self, sale_id: str, new_status: SaleStatus) -> Decimal:
        sale = self.db.query(Sale).filter(Sale.id==sale_id).first()
        if sale is None:
            raise SaleNotFoundError(f"No sale found with id {sale_id}")

        if sale.status!=SaleStatus.pending:
            raise SaleAlreadyReconciledError(
                f"Sale {sale_id} is already {sale.status.value}, cannot be reconciled again"
            )
        
        advance_already_paid=sale.advance_paid_amount or Decimal("0.00")

        if new_status == SaleStatus.approved:
            final_entitlement=sale.earning
        elif new_status == SaleStatus.rejected:
            final_entitlement=Decimal("0.00")
        else:
            raise ValueError("new_status should be approved or rejected")
        
        adjustment = final_entitlement - advance_already_paid

        self.wallet.add_entry(
            user_id=sale.user_id,
            type_=LedgerEntryType.ADJUSTMENT,
            amount=adjustment,
            sale_id=sale.id,
            description=f"Reconciliation ({new_status.value}) for sale {sale.id}",
        )

        sale.status=new_status
        sale.reconciled_at=_now()
        self.db.commit()

        return adjustment