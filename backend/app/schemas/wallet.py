import uuid
from pydantic import BaseModel
from app.models.wallet import TransactionType, TransactionStatus, PaymentMethod


class WalletOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    balance: float
    pending_balance: float


class DepositRequest(BaseModel):
    amount: float
    method: PaymentMethod
    reference: str | None = None


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    amount: float
    type: TransactionType
    method: PaymentMethod
    status: TransactionStatus
    created_at: str
