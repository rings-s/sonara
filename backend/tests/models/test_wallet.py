def test_wallet_defaults():
    from app.models.wallet import TransactionType, TransactionStatus
    assert TransactionType.deposit == "deposit"
    assert TransactionStatus.pending == "pending"


def test_review_target_types():
    from app.models.review import ReviewTargetType
    assert ReviewTargetType.teacher == "teacher"
    assert ReviewTargetType.hall == "hall"
