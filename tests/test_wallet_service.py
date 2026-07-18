from decimal import Decimal 

from app.models import User, LedgerEntryType
from app.services.wallet_service import WalletService

def _make_user(db, email="user1@example.com"):
    user=User(name="user1",email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_balance_is_zero_with_no_entries(db_session):
    user=_make_user(db_session)
    wallet=WalletService(db_session)
    assert wallet.get_balance(user.id)==Decimal("0")

def test_balance_sums_credits_and_debits(db_session):
    user = _make_user(db_session)
    wallet = WalletService(db_session)

    wallet.add_entry(user.id, LedgerEntryType.ADVANCE_CREDIT, Decimal("4.00"))
    wallet.add_entry(user.id, LedgerEntryType.ADVANCE_CREDIT, Decimal("4.00"))
    wallet.add_entry(user.id, LedgerEntryType.WITHDRAWAL_DEBIT, Decimal("-3.00"))

    assert wallet.get_balance(user.id) == Decimal("5.00")

def test_example_from_pdf(db_session):
    user = _make_user(db_session)
    wallet = WalletService(db_session)

    #advance payout on 3 pending sales = rs 4 each(10% of 40)
    for _ in range(3):
        wallet.add_entry(user.id,LedgerEntryType.ADVANCE_CREDIT, Decimal("4.00"))
    
    assert wallet.get_balance(user.id) == Decimal("12.00")

    #reconci adjustments
    #1 failed sale so -4 and 2 accepted sales so the remaining rs36 each.
    adjustments = [Decimal("-4.00"), Decimal("36.00"), Decimal("36.00")]
    for amt in adjustments:
        wallet.add_entry(user.id,LedgerEntryType.ADJUSTMENT, amt)
    
    assert sum(adjustments) == Decimal("68.00")

    assert wallet.get_balance(user.id) == Decimal("80.00")