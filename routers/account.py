from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.enums import BalanceStatus
from models.user import User
from schemas.account import AccountResponse, DepositRequest, WithdrawRequest
from schemas.base import ProblemDetail
from services.account_service import AccountService
from utils.security import get_current_user

router = APIRouter()


def account_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    return AccountService(db)


@router.get("/balance", response_model=AccountResponse)
async def get_balance(
    user: User = Depends(get_current_user),
    service: AccountService = Depends(account_service),
):
    balance = await service.get_balance(user.id)
    if balance is None:
        return ProblemDetail(title="Not Found", status=404, detail="No account balance found").to_response()
    return balance


@router.post("/deposit", response_model=AccountResponse)
async def deposit(
    body: DepositRequest,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(account_service),
):
    balance = await service.deposit(user.id, body.amount)
    if balance is None:
        return ProblemDetail(title="Not Found", status=404, detail="No account balance found").to_response()
    return balance


@router.post("/withdraw", response_model=AccountResponse)
async def withdraw(
    body: WithdrawRequest,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(account_service),
):
    status = await service.check_withdrawable(user.id, body.amount)
    if status == BalanceStatus.NOT_FOUND:
        return ProblemDetail(title="Not Found", status=404, detail="No account balance found").to_response()
    if status == BalanceStatus.INSUFFICIENT_FUNDS:
        return ProblemDetail(title="Unprocessable Entity", status=422, detail="Insufficient funds").to_response()

    balance = await service.withdraw(user.id, body.amount)
    return balance
