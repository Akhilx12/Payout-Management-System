from decimal import Decimal

import pytest

from app.models import User, Brand, Sale, SaleStatus
from app.services.advance_payout_service import AdvancePayoutService
from app.services.reconciliation_service import (
    ReconciliationService,
    SaleAlreadyReconciledError,
    SaleNotFoundError,
)
from app.services.wallet_service import WalletService


def _make_user_brand(db, email="user@example.com"):
    user = User(name="Test User", email=email)
    brand = Brand(name="brand_x")
    db.add_all([user, brand])
    db.commit()
    db.refresh(user)
    db.refresh(brand)
    return user, brand


def test_case1_approved_sale(db_session):
    #PDF Case 1: earning 30, advance 3, approved. adjustment = 27
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("30.00"),
                status=SaleStatus.pending, advance_paid_amount=Decimal("3.00"))
    db_session.add(sale)
    db_session.commit()

    recon = ReconciliationService(db_session)
    adjustment = recon.reconcile(sale.id, SaleStatus.approved)

    assert adjustment == Decimal("27.00")
    assert sale.status == SaleStatus.approved
    assert sale.reconciled_at is not None


def test_case2_rejected_sale(db_session):
    #PDF Case 2: earning 50, advance 5, rejected. adjustment = -5
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("50.00"),
                status=SaleStatus.pending, advance_paid_amount=Decimal("5.00"))
    db_session.add(sale)
    db_session.commit()

    recon = ReconciliationService(db_session)
    adjustment = recon.reconcile(sale.id, SaleStatus.rejected)

    assert adjustment == Decimal("-5.00")
    assert sale.status == SaleStatus.rejected


def test_reconciling_sale_with_no_advance_paid(db_session):
    #Edge case: sale reconciled without ever going through the advance job
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("20.00"),
                status=SaleStatus.pending)  # advance_paid_amount stays None
    db_session.add(sale)
    db_session.commit()

    recon = ReconciliationService(db_session)
    adjustment = recon.reconcile(sale.id, SaleStatus.approved)

    assert adjustment == Decimal("20.00")  # full amount, nothing to subtract


def test_cannot_reconcile_same_sale_twice(db_session):
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("30.00"),
                status=SaleStatus.pending, advance_paid_amount=Decimal("3.00"))
    db_session.add(sale)
    db_session.commit()

    recon = ReconciliationService(db_session)
    recon.reconcile(sale.id, SaleStatus.approved)

    with pytest.raises(SaleAlreadyReconciledError):
        recon.reconcile(sale.id, SaleStatus.approved)


def test_reconciling_nonexistent_sale_raises(db_session):
    recon = ReconciliationService(db_session)
    with pytest.raises(SaleNotFoundError):
        recon.reconcile("does-not-exist", SaleStatus.approved)


def test_full_pdf_example_end_to_end(db_session):
    
    #The complete PDF example: 3 pending sales of rs40 each
    #Advance job pays 10% (rs4) on each. total advance rs12
    #Reconciliation: 1 rejected, 2 approved.
    #Batch adjustment total should be rs68, final balance should be rs80
    
    user, brand = _make_user_brand(db_session)
    sales = [
        Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("40.00"), status=SaleStatus.pending)
        for _ in range(3)
    ]
    db_session.add_all(sales)
    db_session.commit()

    # Step 1: advance payout job runs
    advance_service = AdvancePayoutService(db_session)
    advance_results = advance_service.run_batch()
    assert len(advance_results) == 3
    assert all(amount == Decimal("4.00") for _, amount in advance_results)

    wallet = WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("12.00")

    # Step 2: reconciliation -- sale[0] rejected, sale[1] and sale[2] approved
    recon = ReconciliationService(db_session)
    adjustments = [
        recon.reconcile(sales[0].id, SaleStatus.rejected),
        recon.reconcile(sales[1].id, SaleStatus.approved),
        recon.reconcile(sales[2].id, SaleStatus.approved),
    ]

    assert sum(adjustments) == Decimal("68.00")  # matches final payout
    assert wallet.get_balance(user.id) == Decimal("80.00")  # true total balance