from decimal import Decimal

from app.models import User, Brand, Sale, SaleStatus
from app.services.advance_payout_service import AdvancePayoutService
from app.services.wallet_service import WalletService


def _make_user_brand(db):
    user = User(name="Akhik", email="akhil@example.com")
    brand = Brand(name="faym.co")
    db.add_all([user, brand])
    db.commit()
    db.refresh(user)
    db.refresh(brand)
    return user, brand


def test_advance_payout_pays_ten_percent(db_session):
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("40.00"), status=SaleStatus.pending)
    db_session.add(sale)
    db_session.commit()

    service = AdvancePayoutService(db_session)
    result = service.run_batch()

    assert len(result) == 1
    assert result[0][1] == Decimal("4.00")

    wallet = WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("4.00")


def test_advance_payout_is_idempotent(db_session):
    """Running the batch job twice should never pay the same sale twice."""
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("40.00"), status=SaleStatus.pending)
    db_session.add(sale)
    db_session.commit()

    service = AdvancePayoutService(db_session)
    service.run_batch()
    second_run_result = service.run_batch()

    assert second_run_result == []

    wallet = WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("4.00")  # not 8.00


def test_advance_payout_skips_non_pending_sales(db_session):
    """Only pending sales are eligible -- approved/rejected sales must be ignored."""
    user, brand = _make_user_brand(db_session)
    sale = Sale(user_id=user.id, brand_id=brand.id, earning=Decimal("50.00"), status=SaleStatus.approved)
    db_session.add(sale)
    db_session.commit()

    service = AdvancePayoutService(db_session)
    result = service.run_batch()

    assert result == []