from decimal import Decimal

import pytest

from app.models import User, LedgerEntryType, PayoutStatus
from app.services.wallet_service import WalletService
from app.services.withdrawal_service import WithdrawalService
from app.services.payout_recovery_service import (
    PayoutRecoveryService,
    PayoutNotFoundError,
    InvalidPayoutStateError,
)


def _make_funded_user_with_withdrawal(db, withdraw_amount=Decimal("20.00")):
    user = User(name="Recovery Test", email="recoverytest@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    wallet = WalletService(db)
    wallet.add_entry(user.id, LedgerEntryType.ADVANCE_CREDIT, Decimal("50.00"))

    withdrawal = WithdrawalService(db)
    payout = withdrawal.request_withdrawal(user.id, withdraw_amount)
    return user, payout


def test_failed_payout_credits_balance_back(db_session):
    user, payout = _make_funded_user_with_withdrawal(db_session)
    wallet = WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("30.00")

    recovery = PayoutRecoveryService(db_session)
    recovery.mark_payout_failed(payout.id, PayoutStatus.failed, reason="Bank error")

    assert wallet.get_balance(user.id) == Decimal("50.00")
    assert payout.status == PayoutStatus.failed


def test_cannot_reverse_same_payout_twice(db_session):
    user, payout = _make_funded_user_with_withdrawal(db_session)
    recovery = PayoutRecoveryService(db_session)
    recovery.mark_payout_failed(payout.id, PayoutStatus.failed)

    with pytest.raises(InvalidPayoutStateError):
        recovery.mark_payout_failed(payout.id, PayoutStatus.failed)


def test_reversed_amount_is_withdrawable_again(db_session):
    """Core requirement: after reversal, user can initiate another withdrawal for that amount."""
    user, payout = _make_funded_user_with_withdrawal(db_session, withdraw_amount=Decimal("20.00"))
    recovery = PayoutRecoveryService(db_session)
    recovery.mark_payout_failed(payout.id, PayoutStatus.failed)

    wallet = WalletService(db_session)
    assert wallet.get_balance(user.id) == Decimal("50.00")

    # The failed payout no longer counts toward the 24h cooldown (only
    # 'initiated'/'completed' payouts do), so a new withdrawal should
    # succeed immediately -- this is the actual point of Question 2.
    withdrawal = WithdrawalService(db_session)
    new_payout = withdrawal.request_withdrawal(user.id, Decimal("20.00"))

    assert new_payout.status == PayoutStatus.initiated
    assert wallet.get_balance(user.id) == Decimal("30.00")

def test_reversing_nonexistent_payout_raises(db_session):
    recovery = PayoutRecoveryService(db_session)
    with pytest.raises(PayoutNotFoundError):
        recovery.mark_payout_failed("does-not-exist", PayoutStatus.failed)