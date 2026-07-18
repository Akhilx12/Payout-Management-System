from decimal import Decimal 
import pytest 
from app.models import User, LedgerEntryType, PayoutStatus 
from app.services.wallet_service import WalletService 
from app.services.withdrawal_service import(
    WithdrawalService, 
    InsufficientBalanceError,
    WithdrawalTooSoonError,
)

def _make_funded_user(db, balance=Decimal("50.00"), email="withtest@test.com"):
    user=User(name="WithTest", email=email)
    db.add(user)
    db.commit()
    db.refresh(user)

    wallet=WalletService(db)
    wallet.add_entry(user.id, LedgerEntryType.ADVANCE_CREDIT, balance)
    return user 

def test_withdrawal_with_suff_balance(db_session):
    user=_make_funded_user(db_session)
    withdrawal=WithdrawalService(db_session)

    payout=withdrawal.request_withdrawal(user.id, Decimal("20.00"))

    assert payout.status == PayoutStatus.initiated
    assert payout.amount == Decimal("20.00")

    wallet=WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("30.00")

def test_withdrawal_with_insuff_balance(db_session):
    user = _make_funded_user(db_session)
    withdrawal = WithdrawalService(db_session)

    with pytest.raises(InsufficientBalanceError):
        withdrawal.request_withdrawal(user.id, Decimal("100.00"))
    
    #balance must be untouched after a attempt which is blocked
    wallet=WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("50.00")

def test_another_withdraw_in_24h(db_session):
    user=_make_funded_user(db_session)
    withdrawal=WithdrawalService(db_session)

    withdrawal.request_withdrawal(user.id, Decimal("10.00"))
    with pytest.raises(WithdrawalTooSoonError):
        withdrawal.request_withdrawal(user.id, Decimal("5.00"))