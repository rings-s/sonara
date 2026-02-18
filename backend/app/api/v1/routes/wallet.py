from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.wallet import Wallet, Transaction, TransactionType, TransactionStatus
from app.schemas.wallet import WalletOut, DepositRequest, TransactionOut

router = APIRouter(prefix="/wallet", tags=["wallet"])


async def get_or_create_wallet(user: User, db: AsyncSession) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user.id)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


@router.get("/", response_model=WalletOut)
async def get_wallet(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_or_create_wallet(current_user, db)


@router.post("/deposit", response_model=TransactionOut)
async def deposit(
    payload: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    wallet = await get_or_create_wallet(current_user, db)
    tx = Transaction(
        user_id=current_user.id,
        amount=payload.amount,
        type=TransactionType.deposit,
        method=payload.method,
        status=TransactionStatus.pending,
        reference=payload.reference,
    )
    db.add(tx)
    # Wallet balance updated after admin approval in production
    await db.commit()
    await db.refresh(tx)
    return tx
